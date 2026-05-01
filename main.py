import matplotlib
matplotlib.use('Agg') # Force le mode sans fenêtre pour le serveur
import matplotlib.pyplot as plt
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from network import HVACNetwork
from calculs import *


# Initialisation de l'application FastAPI
app = FastAPI(
    title="HVAC Expert API",
    description="Moteur de calcul et de dimensionnement aéraulique"
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

# --- ROUTES DE CALCUL ---

@app.post("/network/init")
def init():
    """Réinitialise le réseau pour un nouveau projet"""
    global net
    net = HVACNetwork()
    return {"status": "Réseau réinitialisé"}

@app.post("/network/nodes")
def add_nodes(nodes: list[dict]):
    """Ajoute des points de passage ou de consommation"""
    for n in nodes:
        net.add_node(n['name'], n.get('supply', 0))
    return {"message": f"{len(nodes)} nœuds ajoutés"}

@app.post("/network/ducts")
def add_ducts(ducts: list[DuctItem]):
    """Ajoute des conduits (automatique Rectangulaire vs Circulaire)"""
    for d in ducts:
        if d.W and d.H:
            # Cas rectangulaire
            dh = diametre_hydraulique(d.W, d.H)
            sect = section_rectangulaire(d.W, d.H)
        else:
            # Cas circulaire
            dh = d.D
            sect = section_circulaire(d.D)
        net.add_duct(d.name, d.n1, d.n2, d.L, dh, d.coeffs, sect)
    return {"message": f"{len(ducts)} conduits configurés"}

@app.get("/network/solve")
def solve(eff: float = 0.7, prix_elec: float = 0.25):
    net.solve()
    
    max_dp = abs(min(n.P for n in net.nodes.values()))
    total_q = sum(n.supply for n in net.nodes.values() if n.supply > 0)
    puissance = puissance_ventilateur(total_q, max_dp, eff)
    
    # Nouveau : Calcul du coût annuel
    cout_annuel = calcul_cout_annuel(puissance, prix_kwh=prix_elec)
    
    return {
        "summary": {
            "total_flow_m3h": round(total_q, 2),
            "max_pressure_drop_pa": round(max_dp, 2),
            "fan_power_watts": round(puissance, 2),
            "estimated_annual_cost_euros": cout_annuel, # <-- Ajout ici
            "efficiency_used": eff
        },
        "results": [
            {
                "duct": d.name,
                "flow_m3h": round(d.flow * 3600, 2),
                "delta_p_pa": round(abs(d.n1.P - d.n2.P), 2),
                "velocity_ms": round(abs(d.flow) / d.section_reelle, 2)
            } for d in net.ducts
        ]
    }

# --- ROUTE DE DIMENSIONNEMENT (SUGGESTION) ---

@app.get("/suggest")
def suggest(q: float, v: float = 4.0, shape: str = "circular"):
    """Suggère des dimensions selon un débit q et une vitesse cible v"""
    if shape == "circular":
        d_m = diametre_optimal(q, v)
        return {
            "shape": "circular",
            "suggested_diameter_mm": round(d_m * 1000, 0),
            "info": f"Dimension calculée pour v={v}m/s"
        }
    else:
        w, h = suggerer_dimensions_rect(q, v)
        return {
            "shape": "rectangular",
            "suggested_W_mm": round(w * 1000, 0),
            "suggested_H_mm": round(h * 1000, 0),
            "info": f"Dimension calculée pour v={v}m/s avec un ratio de 1.5"
        }
    


@app.get("/network/visualize")
def visualize():
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