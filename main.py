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
import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, model_validator
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.openapi.utils import get_openapi
from datetime import datetime
import time
from network import HVACNetwork
from calculs import section_circulaire, section_rectangulaire, diametre_hydraulique, suggerer_diametre_circ, suggerer_dimensions_rect
from report_gen import export_to_pdf, print_console_report

import uvicorn
import webbrowser
from threading import Timer
                                                                                                                                                                                                                                                                                                                                                                                                                            
# --- INITIALISATION ---
# Creation de l'API et configuration des métadonnées (cadre de réseau).  
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

# --- CONFIGURATION DES CHEMINS ---
DOCS_DIR = "docs"
SCHEMA_PATH = os.path.join(DOCS_DIR, "temp_network_schema.png")
REPORT_PATH = os.path.join(DOCS_DIR, "report_aeraulique.pdf")

# Création du dossier docs s'il n'existe pas au démarrage
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)


# Instance globale du moteur de calcul (cerveau de réseau)
net = HVACNetwork()       

# --- ROUTE D'ACCUEIL ---
@app.get("/", tags=["Système"])
def root():
    """Route d'accueil pour vérifier que l'API est en ligne."""
    return {
        "message": "Bienvenue sur HVAC Expert API",
        "docs": "/docs",
        "status": "online",
        "author": "Fateh Chaabat",
        "version": "1.0.0"
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
    D: float = None                                                                                         # Diamètre (m), Optionnel si W/H fournis
    W: float = None                                                                                         # Largeur (m), Optionnel si D fourni
    H: float = None                                                                                         # Hauteur (m), Optionnel si D fourni
    
    # Propriétés aérauliques
    coeffs: list[float] = []                                                                                # Somme des coefficients singuliers Σζ (ex: coudes, grilles, etc.)
    is_smooth: bool = False                                                                                 # true pour lisse (PVC/Alu), false pour Rugueux (Acier Galvanisé)
    
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
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return {
        "status": "success",
        "message": "Le moteur de calcul a été réinitialisé. Prêt pour un nouveau projet.",
        "timestamp": current_time
    }

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
    try:
        for d in ducts:
            # Logique de détermination de la géométrie
            if d.W is not None and d.H is not None:
                dh = diametre_hydraulique(d.W, d.H)
                sect = section_rectangulaire(d.W, d.H)
            elif d.D is not None:
                dh = d.D
                sect = section_circulaire(d.D)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Dimensions (D ou W/H) manquantes pour le conduit {d.name}"
                )
            
            # Ajout au moteur de calcul
            net.add_duct(d.name, d.n1, d.n2, d.L, dh, d.coeffs, sect, d.is_smooth)
            
        return {"message": f"{len(ducts)} conduits configurés avec succès"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout : {str(e)}")                                                


# --- ROUTES DE CALCUL & ANALYSE ---
@app.get("/network/solve", tags=["Calcul"])
def solve():
    """
    Exécute la résolution hydraulique et génère le bilan énergétique.
    L'algorithme équilibre les pressions (Kirchhoff) et calcule les pertes 
    linéaires et singulières (Darcy-Weisbach) sur l'ensemble du graphe.
    """
    # 1. Validation de l'existence de la topologie
    if not net.ducts:
        raise HTTPException(
            status_code=400, 
            detail="Calcul impossible : aucun conduit défini dans le réseau."
        )

    try:
        # 2. Résolution itérative (Convergence des débits et pressions)
        start_time = time.time()
        residu_final = net.solve()
        execution_time = time.time() - start_time
        
        # STABILITÉ : Seuil de convergence sur le débit (m³/s)
        # 1e-5 m³/s correspond à une erreur résiduelle de 0.036 m³/h.
        tolerance = 1e-5
        is_stable = residu_final < tolerance

        # 3. Extraction des résultats
        results = net.get_results()
        
        # 4. Ajout des métadonnées de performance
        results["solver_metadata"] = {
            "execution_time_sec": round(execution_time, 3),
            "convergence_status": "stable" if is_stable else "unstable",
            "residual_error_m3s": float(f"{residu_final:.2e}"),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            #"pdf_report": "report_aeraulique.pdf"
        }
        
        # 5. Génération des fichiers (Image et PDF)
        # Donner l'endroit de suvgarde à la fonction draw_network
        net.draw_network(save_path=SCHEMA_PATH)
        
        # Génération du PDF contenant résultats et schéma et enregistrement dans le chemin REPORT_PATH
        export_to_pdf(results, REPORT_PATH, image_path=SCHEMA_PATH)
        
        # 6. Rapport Console
        print_console_report(results)
        
        # 7. RETURN FINAL (C'est ce return qui envoie tout à Swagger)
        return results
        
        
    except Exception as e:
        # Capture d'éventuelles erreurs numériques (divergence, division par zéro)
        raise HTTPException(
            status_code=500, 
            detail=f"Échec de la convergence ou erreur de calcul : {str(e)}"
        )
 
# --- VISUALISATION ---
@app.get("/network/visualize", tags=["Visualisation"])
def visualize():
    """
    Génère un schéma dynamique du réseau aéraulique.
    Affiche les flux (m³/h), les vitesses (m/s) et les pressions (Pa).
    """
    
    try:
        # On s'assure que le dossier existe avant de dessiner
        os.makedirs(DOCS_DIR, exist_ok=True)
        
        # On génère l'image
        net.draw_network(save_path=SCHEMA_PATH)
        
        # On vérifie physiquement la taille du fichier
        # Si le fichier fait 0 octet, c'est qu'il y a un souci dans le dessin
        if os.path.getsize(SCHEMA_PATH) == 0:
            raise Exception("Le fichier généré est vide (0 octets).")

        return FileResponse(
            SCHEMA_PATH, 
            media_type="image/png",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
    except Exception as e:
        print(f"ERREUR VISUALIZE: {str(e)}") # Regarde ton terminal !
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get(
    "/network/download-report", 
    tags=["Telechargement PDF"],
    response_class=FileResponse  # Informe Swagger que la réponse est un fichier
)
def download_report():
    """
    **Télécharger le dernier rapport PDF généré**
    
    Cette route renvoie le fichier PDF contenant les calculs et le schéma 
    générés lors du dernier appel à `/solve`.
    """
    
    # 1. Vérification de l'existence du fichier
    if not os.path.exists(REPORT_PATH):
        raise HTTPException(status_code=404, detail="Le rapport n'a pas encore été généré.")

    # 2. Retour du fichier
    return FileResponse(
        path=REPORT_PATH, 
        filename="Rapport_HVAC_Expert.pdf", 
        media_type='application/pdf'
    )


# --- ROUTE DE DIMENSIONNEMENT (OUTIL D'AIDE) ---
@app.get(
    "/suggest", 
    tags=["💡 Assistant de Design"],
    summary="Duct Sizer (D or W x H)",
    description=(
        "### Utilitaire indépendant\n"
        "Cet outil permet de prédimensionner vos conduits avant de les intégrer au réseau. "
        "Il calcule la section idéale pour garantir que la vitesse de l'air ne dépasse pas la valeur cible."
    )
)
def suggest(
    q: float = Query(..., title="Débit d'air", description="Débit en m³/h"), 
    v: float = Query(..., title="Vitesse cible", description="Vitesse de l'air souhaitée en m/s"), 
    shape: str = Query("circular", enum=["circular", "rectangular"], description="Forme du conduit")
):
    """
    Suggère des dimensions optimales (D ou WxH) pour un débit donné (m3/h) 
    en respectant une vitesse de passage cible (m/s).
    """
    # --- VALIDATION DES VALEURS ---
    # FastAPI gère l'absence (Required) grâce aux '...'    
    if q <= 0:
        raise HTTPException(status_code=400, detail="Le débit (q) doit être supérieur à 0.")
    if v <= 0:
        raise HTTPException(status_code=400, detail="La vitesse (v) doit être supérieure à 0.")
    
    # 1. Cas du conduit circulaire
    if shape == "circular":
        d_m = suggerer_diametre_circ(q, v)
        return {
            "status": "success",
            "type": "Preliminary Sizing Assistant",
            "results": {
                "shape": "circular",
                "suggested_diameter_mm": round(d_m * 1000, 0),
                "section_m2": round(section_circulaire(d_m), 4),
                "target_velocity_ms": v,
                "note": "Design optimized for acoustic comfort"
            }
        }
    
    # 2. Cas du conduit rectangulaire
    elif shape == "rectangular":
        w, h = suggerer_dimensions_rect(q, v)
        return {
            "status": "success",
            "type": "Preliminary Sizing Assistant",
            "results": {
                "shape": "rectangular",
                "suggested_W_mm": round(w * 1000, 0),
                "suggested_H_mm": round(h * 1000, 0),
                "section_m2": round(section_rectangulaire(w, h), 4),
                "aspect_ratio": "1.5",
                "target_velocity_ms": v,
                "note": "Design optimized for acoustic comfort"
            }
        }
    

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