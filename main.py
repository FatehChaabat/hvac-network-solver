# =================================================================
# COMPOSANT : MAIN API (FastAPI)
# PROJET    : HVAC Expert & Design API
# VERSION   : 1.0.0 (OAS 3.1 compliant)
# ROLE      : Point d'entrée de l'application. Gère les routes et
#             l'orchestration entre le solveur et l'interface.
# =================================================================

import matplotlib
matplotlib.use('Agg')                              
import matplotlib.pyplot as plt
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, model_validator
from fastapi.responses import StreamingResponse
from fastapi.openapi.utils import get_openapi

from network import HVACNetwork
from calculs import (
    section_circulaire,
    section_rectangulaire, 
    diametre_hydraulique, 
    suggerer_diametre_circ, 
    suggerer_dimensions_rect
)

import uvicorn
import webbrowser
from threading import Timer
                                                                                                                                                                                                                                                                                                                                                                                                                            
# --- INITIALISATION ---
# Configuration de l'API avec une description détaillée et des liens vers mes profils.  
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


# Instance globale du moteur de calcul HVACNetwork
net = HVACNetwork()       

# --- ROUTE D'ACCUEIL ---
@app.get("/", tags=["Général"])
def root():
    """Route d'accueil pour vérifier que l'API est en ligne."""
    return {
        "message": "Bienvenue sur HVAC Expert API",
        "docs": "/docs",
        "status": "online",
        "author": "Fateh Chaabat"
    }
    
                                                                                                       
# --- MODÈLES DE DONNÉES (API) ---
class NodeItem(BaseModel):
    """Schéma pour la définition d'un nœud."""
    name: str                                                                                               # Nom du nœud (ex: 'Ventilateur', 'Bouche_01')
    supply: float = 0.0                                                                                     # Débit (positif = entrée, négatif = sortie, 0 = transit)

class DuctItem(BaseModel):   
    """
    Schéma de validation pour la création d'un conduit.
    Gère la géométrie (circulaire ou rectangulaire) et les propriétés physiques.
    """                                                                                                     
    name: str                                                                                               # ID unique (ex: 'D01')
    n1: str                                                                                                 # Nœud amont
    n2: str                                                                                                 # Nœud aval
    L: float                                                                                                # Longueur (m)
    
    # Géométrie : D pour circulaire, W/H pour rectangulaire
    D: float = None                                                                                         # Diamètre hydraulique (m)
    W: float = None                                                                                         # Largeur (m)
    H: float = None                                                                                         # Hauteur (m)
    
    # Propriétés aérauliques
    coeffs: list[float] = []                                                                                # Somme des coefficients singuliers Σζ (ex: coudes, grilles, etc.)
    is_smooth: bool = False                                                                                 # Modèle de rugosité (Lisse vs Rugueux)
    
    @model_validator(mode='after')
    def check_geometry(self):
        """Vérifie qu'une géométrie valide est fournie (D ou W+H)."""
        if self.D is None and (self.W is None or self.H is None):
            raise ValueError("Un conduit doit avoir soit un diamètre (D), soit une largeur et hauteur (W, H).")
        return self


# --- ROUTES DE CONFIGURATION ---
@app.post("/network/init", tags=["Configuration"])                                                          
def init():                                                                                            
    """Réinitialise complètement le réseau pour un nouveau projet."""
    global net                                                                                         
    net = HVACNetwork()                                                                                
    return {"status": "Réseau réinitialisé"}

@app.post("/network/nodes", tags=["Configuration"])                                                         
def add_nodes(nodes: list[NodeItem]): 
    """
    Définit les points du réseau.
    'supply' > 0 : Soufflage | 'supply' < 0 : Extraction | 0 : Transit.
    """
    for n in nodes: 
        # On accède maintenant aux données via n.name et n.supply
        net.add_node(n.name, n.supply) 
    return {"message": f"{len(nodes)} nœuds ajoutés"}                                                  

@app.post("/network/ducts", tags=["Configuration"])                                                         
def add_ducts(ducts: list[DuctItem]):                                                                  
    """
    Configure les conduits avec gestion hybride des sections :
    - Circulaire : via paramètre 'D'
    - Rectangulaire : via paramètres 'W' et 'H' (conversion auto en diamètre hydraulique)
    """
    for d in ducts:  
        # Logique de détermination de la géométrie                                                                                       
        if d.W and d.H:                                                                                     
            dh = diametre_hydraulique(d.W, d.H)                                                             
            sect = section_rectangulaire(d.W, d.H)                                                         
        elif d.D:                                                                                           
            dh = d.D                                                                                        
            sect = section_circulaire(d.D)                                                                  
        else:
            raise HTTPException(status_code=400, detail=f"Dimensions (D ou W/H) manquantes pour le conduit {d.name}")  
        
        net.add_duct(d.name, d.n1, d.n2, d.L, dh, d.coeffs, sect, d.is_smooth)                              
    return {"message": f"{len(ducts)} conduits configurés"}                                                 


# --- ROUTES DE CALCUL & ANALYSE ---
@app.get("/network/solve", tags=["Calcul"])
def solve():
    """
    Exécute la résolution hydraulique et génère le bilan énergétique.
    L'algorithme équilibre les pressions (Kirchhoff) et calcule les pertes 
    linéaires et singulières (Darcy-Weisbach) sur l'ensemble du graphe.
    """
    # Validation de l'existence de la topologie
    if not net.ducts:
        raise HTTPException(status_code=400, detail="Calcul impossible : aucun conduit défini.")

    try:
        # Résolution itérative (Convergence des pressions et débits)
        net.solve()
        
        # Extraction du bilan (Chemin critique, puissances et synthèse par tronçon)
        return net.get_results()
        
    except Exception as e:
        # Capture d'éventuelles erreurs numériques (divergence, division par zéro)
        raise HTTPException(status_code=500, detail=f"Échec de la convergence : {str(e)}")                                                                

 
# --- VISUALISATION ---
@app.get("/network/visualize", tags=["Visualisation"])
def visualize():
    """
    Génère un schéma dynamique du réseau aéraulique.
    Affiche les flux (m³/h), les vitesses (m/s) et les pressions (Pa).
    """
    # Nettoyage systématique des buffers pour éviter la superposition de tracés
    plt.clf()
    plt.close('all')
    
    fig = plt.figure(figsize=(18, 12))
    
    try:
        # Génération du tracé via NetworkX / Matplotlib
        net.draw_network()
        
        # Sérialisation de l'image en flux binaire (sans écriture disque)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        
        return StreamingResponse(buf, media_type="image/png")
        
    except Exception as e:
        plt.close(fig)
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du rendu graphique : {str(e)}"
        )
    

# --- ROUTE DE DIMENSIONNEMENT (SUGGESTION) ---
@app.get("/suggest", tags=["Dimensionnement"])
def suggest(q: float, v: float = 4.0, shape: str = "circular"):
    """
    Suggère des dimensions optimales (D ou WxH) pour un débit donné (m3/h) 
    en respectant une vitesse de passage cible (m/s).
    """
    
    # 1. Cas du conduit circulaire
    if shape == "circular":
        d_m = suggerer_diametre_circ(q, v)
        return {
            "shape": "circular",
            "suggested_diameter_mm": round(d_m * 1000, 0),
            "section_m2": round(section_circulaire(d_m), 4),
            "info": f"Dimensionné pour v = {v} m/s"
        }
    
    # 2. Cas du conduit rectangulaire (basé sur un ratio standard)
    elif shape == "rectangular":
        w, h = suggerer_dimensions_rect(q, v)
        return {
            "shape": "rectangular",
            "suggested_W_mm": round(w * 1000, 0),
            "suggested_H_mm": round(h * 1000, 0),
            "section_m2": round(section_rectangulaire(w, h), 4),
            "info": f"Dimensionné pour v = {v} m/s (ratio aspect 1.5)"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Forme non supportée. Utilisez 'circular' ou 'rectangular'.")


# --- CONFIGURATION OPENAPI CUSTOM ---
def custom_openapi():
    """
    Personnalise et met en cache le schéma OpenAPI.
    Force la version 3.1.0 pour une compatibilité totale avec JSON Schema 2020-12.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # Génération du schéma initial à partir des métadonnées de l'application
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Mise à niveau vers OpenAPI 3.1.0 (supporte les types complexes et nullables)
    openapi_schema["openapi"] = "3.1.0"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Injection de la méthode personnalisée dans l'instance FastAPI
app.openapi = custom_openapi       


# --- BLOC DE LANCEMENT ---
if __name__ == "__main__":
    
    def open_browser():
        webbrowser.open("http://127.0.0.1:8000/docs")

    # Attend 1.5 seconde que le serveur démarre, puis ouvre le navigateur
    Timer(1.5, open_browser).start()
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)