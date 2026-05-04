# =================================================================
# COMPOSANT : MAIN API (FastAPI)
# PROJET    : HVAC Expert & Design API
# VERSION   : 1.0.0 (OAS 3.1 compliant)
# ROLE      : Point d'entrée de l'application. Gère les routes et
#             l'orchestration entre le solveur et l'interface.
# =================================================================

import matplotlib
matplotlib.use('Agg')  # Mode sans fenêtre pour le serveur
import matplotlib.pyplot as plt
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.openapi.utils import get_openapi

from network import HVACNetwork
from calculs import *

# --- INITIALISATION ---
app = FastAPI(
    title="HVAC Expert API", 
    description="""### Moteur de calcul et d'expertise aéraulique
> **HVAC Expert API** est un outil robuste conçu pour les bureaux d'études et ingénieurs souhaitant automatiser le calcul et la visualisation de réseaux de gaines.

#### 🛠 Fonctionnalités clés
* **Simulation Multi-régimes :** Modélisation précise via Haaland (conduits industriels) ou Blasius (conduits lisses).
* **Analyse d'Expertise :** Identification du chemin critique, calcul de la puissance totale, puissance ventilateur et coût énergétique.
* **Aide au Dimensionnement :** Algorithmes de suggestion de diamètres (Circulaire/Rectangulaire) basés sur vos vitesses cibles.
* **Visualisation :** Génération de schémas techniques dynamiques avec annotations des flux (m³/h, m/s, Pa).
* **Standardisation :** Nativement compatible **OpenAPI 3.1** pour une intégration moderne.

#### ⚠️ Note d'ingénierie
> Les résultats fournis sont des estimations basées sur des modèles physiques classiques (Darcy-Weisbach). Ils constituent une aide à la décision et **doivent être validés par un ingénieur qualifié** avant toute mise en œuvre technique ou commande de matériel.

---
**Version 1.0.0** | *Prochainement : Optimisation multi-objectif et réseaux de reprise.* 

[![Portfolio](https://img.shields.io/badge/Portfolio-fatehchaabat.github.io-blue?logo=google-chrome&logoColor=white)](https://fatehchaabat.github.io) 
[![GitHub](https://img.shields.io/badge/GitHub-FatehChaabat-red?logo=github&logoColor=white)](https://github.com/FatehChaabat) 
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Fateh%20Chaabat-green?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/fateh-chaabat-08202aa9/) 
[![ResearchGate](https://img.shields.io/badge/ResearchGate-Fateh%20Chaabat-00CCBB?logo=researchgate)](https://www.researchgate.net/profile/Fateh-Chaabat-2) 
""",
    version="1.0.0"
)


# Instance globale du réseau
net = HVACNetwork()

# --- MODÈLES DE DONNÉES ---
class DuctItem(BaseModel):
    name: str
    n1: str
    n2: str
    L: float
    D: float = None  # Diamètre (si circulaire)
    W: float = None  # Largeur (si rectangulaire)
    H: float = None  # Hauteur (si rectangulaire)
    coeffs: list[float] = []
    is_smooth: bool = False  # Pour type de conduit (lisse ou rugueux)


# --- ROUTES DE CONFIGURATION ---
@app.post("/network/init", tags=["Configuration"])
def init():
    """Réinitialise le réseau pour un nouveau projet."""
    global net
    net = HVACNetwork()
    return {"status": "Réseau réinitialisé"}

@app.post("/network/nodes", tags=["Configuration"])
def add_nodes(nodes: list[dict]):
    """Ajoute des points de passage ou de consommation (supply en m3/h)."""
    for n in nodes:
        net.add_node(n['name'], n.get('supply', 0))
    return {"message": f"{len(nodes)} nœuds ajoutés"}

@app.post("/network/ducts", tags=["Configuration"])
def add_ducts(ducts: list[DuctItem]):
    """Ajoute des conduits avec conversion automatique vers diamètre hydraulique."""
    for d in ducts:
        if d.W and d.H:
            # Cas rectangulaire : calcul Dh et Section réelle
            dh = diametre_hydraulique(d.W, d.H)
            sect = section_rectangulaire(d.W, d.H)
        elif d.D:
            # Cas circulaire
            dh = d.D
            sect = section_circulaire(d.D)
        else:
            raise HTTPException(status_code=400, detail=f"Dimensions manquantes pour le conduit {d.name}")
        
        net.add_duct(d.name, d.n1, d.n2, d.L, dh, d.coeffs, sect, d.is_smooth)
    return {"message": f"{len(ducts)} conduits configurés"}


# --- ROUTES DE CALCUL & ANALYSE ---
@app.get("/network/solve", tags=["Calcul"])
def solve():
    """
    Résout le réseau et génère le bilan énergétique complet.
    La pression dynamique est calculée automatiquement sur la branche critique.
    """
    if not net.ducts:
        raise HTTPException(status_code=400, detail="Le réseau est vide.")

    # 1. Résolution itérative (équilibre Kirchhoff)
    net.solve()
    
    # 2. Récupération du bilan complet (Summary + Results)
    return net.get_results()

# --- ROUTE DE DIMENSIONNEMENT (SUGGESTION) ---
@app.get("/suggest", tags=["Dimensionnement"])
def suggest(q: float, v: float = 4.0, shape: str = "circular"):
    """Suggère des dimensions optimales selon un débit q et une vitesse cible v."""
    if shape == "circular":
        d_m = suggerer_diametre_circ(q, v)
        return {
            "shape": "circular",
            "suggested_diameter_mm": round(d_m * 1000, 0),
            "section_m2": round(section_circulaire(d_m), 4),
            "info": f"Calculé pour v={v}m/s"
        }
    else:
        w, h = suggerer_dimensions_rect(q, v)
        return {
            "shape": "rectangular",
            "suggested_W_mm": round(w * 1000, 0),
            "suggested_H_mm": round(h * 1000, 0),
            "section_m2": round(section_rectangulaire(w, h), 4),
            "info": f"Calculé pour v={v}m/s avec ratio 1.5"
        }

  
# --- VISUALISATION ---
@app.get("/network/visualize", tags=["Visualisation"])
def visualize():
    """Génère un schéma dynamique du réseau aéraulique."""
    # On vide la mémoire de matplotlib pour éviter les superpositions
    plt.clf()
    plt.close('all') 
    
    # On crée une figure explicitement
    fig = plt.figure(figsize=(10, 8))
    
    try:
        # On génère le dessin via la méthode de ton objet net
        net.draw_network() 
        
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        plt.close(fig)
        raise HTTPException(status_code=500, detail=f"Erreur lors du dessin : {str(e)}")    
    

# --- CONFIGURATION OPENAPI CUSTOM ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # On force la version OpenAPI 3.1.0 pour compatibilité JSON Schema 2020-12
    openapi_schema["openapi"] = "3.1.0"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi