"""
HVAC Network Solver — Script de démarrage rapide
Envoie automatiquement les 3 requêtes nécessaires à un calcul complet.
API Live : https://hvac-api-wtuu.onrender.com
"""
import requests
import json

BASE_URL = "https://hvac-api-wtuu.onrender.com"

# Reset
print("🔄 Reset du moteur...")
requests.post(f"{BASE_URL}/network/reset")

# Import du projet
project = {
    "nodes": [
        {"name": "fan_01", "supply": 2200.0},
        {"name": "jn_01",  "supply": 0.0},
        {"name": "jn_a",   "supply": 0.0},
        {"name": "of_01",  "supply": -550.0},
        {"name": "of_02",  "supply": -500.0},
        {"name": "jn_b",   "supply": 0.0},
        {"name": "of_03",  "supply": -600.0},
        {"name": "of_04",  "supply": -550.0}
    ],
    "edges": [
        {"name": "main_trunk",   "n1": "fan_01", "n2": "jn_01", "L": 2.0, "D": 0.45, "epsilon": 0.15, "coeffs": [], "is_branch": False},
        {"name": "to_jn_a",      "n1": "jn_01",  "n2": "jn_a",  "L": 3.0, "D": 0.40, "epsilon": 0.15, "coeffs": [], "slope_degrees": 15, "is_branch": False},
        {"name": "office_1",     "n1": "jn_a",   "n2": "of_01", "L": 2.0, "W": 0.20, "H": 0.17, "epsilon": 0.02, "coeffs": ["grille_soufflage_ailettes"], "is_branch": True},
        {"name": "office_2",     "n1": "jn_a",   "n2": "of_02", "L": 2.0, "W": 0.20, "H": 0.16, "epsilon": 0.02, "coeffs": ["diffuseur_plafonnier_4_voies"], "is_branch": True},
        {"name": "transit_to_b", "n1": "jn_a",   "n2": "jn_b",  "L": 3.0, "D": 0.30, "epsilon": 0.15, "coeffs": [], "is_branch": False},
        {"name": "office_3",     "n1": "jn_b",   "n2": "of_03", "L": 2.0, "W": 0.20, "H": 0.18, "epsilon": 0.02, "coeffs": ["bouche_extraction_standard"], "is_branch": True},
        {"name": "office_4",     "n1": "jn_b",   "n2": "of_04", "L": 2.0, "W": 0.20, "H": 0.17, "epsilon": 0.02, "coeffs": ["diffuseur_rotatif"], "is_branch": True}
    ],
    "fans": [
        {"name": "Main_Fan", "node_name": "fan_01", "rendement": 0.75, "description": "Fresh air supply unit"}
    ]
}

print("📦 Import du projet...")
r = requests.post(f"{BASE_URL}/network/import-project", json=project)
print(f"   → {r.json().get('Message', r.text)}")

# Calcul
print("⚙️  Lancement du solveur...")
r = requests.post(f"{BASE_URL}/network/calculate", params={
    "Temperature_Air_Celsius": 20,
    "Altitude_Metres": 170,
    "Heures_exploitation_par_jour": 10,
    "Jours_exploitation_par_an": 250,
    "Prix_du_kWh": 0.25
})

results = r.json()
fans    = results["summary"]["system_performance_metrics"].get("fans", {})

print("\n✅ Résultats :")
for fan_id, fan_data in fans.items():
    print(f"   🌀 {fan_data.get('fan_label', fan_id)}")
    print(f"      Pression totale  : {fan_data['total_pressure_pa']} Pa")
    print(f"      Puissance        : {fan_data['shaft_input_power_w']} W")
    print(f"      Circuit critique : {fan_data['critical_node']}")

print("\n🖼️  Schéma réseau → GET /network/schema")
print("📄 Rapport PDF   → GET /network/report")
print("📊 Export JSON   → GET /network/data")