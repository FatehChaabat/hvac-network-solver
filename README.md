# HVAC Expert API

>**HVAC Expert API** est un moteur de simulation aéraulique professionnel conçu pour le calcul, l'équilibrage et l'audit énergétique de réseaux de ventilation. Développé avec **FastAPI**, il transforme des données de conception en un modèle physique précis.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---
## 🎯 Objectifs & Valeur Métier
- Bureau d’étude CVC
- Pré-dimensionnement ventilation
- Désenfumage (parking, ERP)
- Outil pédagogique

---

## 🚀 Fonctionnalités

*   **Solveur Nodal Itératif** : Équilibre automatiquement les débits et calcule les pressions aux nœuds via une méthode de relaxation.
*   **Audit Énergétique Intégré** : Calcule la puissance du ventilateur et estime le coût annuel d'électricité en Euros.
*   **Génération de Schéma Technique** : Visualisation dynamique du réseau avec distinction visuelle des formes (Circulaire vs Rectangulaire).
*   **Calculs Physiques Avancés** : Prise en charge des pertes de charge linéaires (friction) et singulières (coudes, tés, etc.).

---

## 🧠 Modèle physique

Le moteur de calcul repose sur trois piliers fondamentaux de la mécanique des fluides :

### 1. Conservation de la masse (Loi des nœuds)
La somme des débits entrants et sortants à chaque nœud doit être égale à la source ou à la consommation (S) :
> **Σ Q = S**

### 2. Relation Pression-Débit
Le débit (Q) circulant dans un conduit est proportionnel à la racine carrée de la perte de charge (ΔP) divisée par la résistance (R) :
> **Q = √(ΔP / R)**

### 3. Résistance aéraulique (R)
Elle combine les pertes de charge linéaires (friction) et les pertes singulières (coudes, tés) :
> **R = [ f * (L/D) + Σζ ] * [ ρ / (2 * S²) ]**

Où :
*   **f** : Coefficient de friction (0.02 par défaut)
*   **L** : Longueur (m) / **D** : Diamètre (m)
*   **ζ (Zeta)** : Coefficients de pertes singulières
*   **ρ (Rho)** : Densité de l'air (1.204 kg/m³)
*   **S** : Section réelle de la gaine (m²)

---
## 🔬 Hypothèses
- Écoulement incompressible
- Facteur de friction constant (approximation)
- Solveur itératif (relaxation)
- Pas de courbe ventilateur intégrée

---

## 📖 Documentation de l'API

L'interface interactive (Swagger) est accessible sur : `http://127.0.0.1:8000/docs`

### Points d'entrée (Endpoints) principaux :

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/network/init` | Réinitialise le réseau à zéro. |
| `POST` | `/network/nodes` | Ajoute des points de passage ou de consommation (m3/h). |
| `POST` | `/network/ducts` | Définit les conduits (Longueurs, Diamètres, Coeffs). |
| `GET` | `/network/solve` | Lance le solveur et retourne l'audit énergétique. |
| `GET` | `/network/visualize` | Génère et affiche le schéma technique en PNG. |

---

## 🎨 Rendu Visuel

Le moteur de visualisation utilise **Matplotlib** et **NetworkX** pour créer un schéma de principe où :
*   🔵 **Bleu (Circulaire)** : Conduits à section ronde.
*   ⚪ **Gris (Rectangulaire)** : Conduits à section rectangulaire.
*   **Épaisseur** : Proportionnelle au diamètre hydraulique du conduit.

---

## 🏗️ Exemple complet (réseau réaliste BE)

### 1. Initialisation

```http
POST /network/init
```

### 2. Ajouter les nœuds
```http
POST /network/nodes

[
  {"name": "A", "supply": 4000},
  {"name": "B", "supply": 0},
  {"name": "C", "supply": 0},
  {"name": "D", "supply": -1000},
  {"name": "E", "supply": -1500},
  {"name": "F", "supply": -1500}
]
```
👉 Interprétation :

- A = soufflage principal (4000 m³/h)
- D, E, F = bouches d’extraction
- B, C = nœuds de distribution

### 3. Ajouter les conduits
```http
POST /network/ducts

[
  {
    "name": "Troncon_Principal_AB",
    "n1": "A",
    "n2": "B",
    "L": 5,
    "D": 0.6,
    "coeffs": [0.3]
  },
  {
    "name": "Liaison_BC",
    "n1": "B",
    "n2": "C",
    "L": 8,
    "D": 0.5,
    "coeffs": [0.3]
  },
  {
    "name": "Branche_Proche_D",
    "n1": "B",
    "n2": "D",
    "L": 2,
    "D": 0.3,
    "coeffs": [1.5]
  },
  {
    "name": "Branche_Milieu_E",
    "n1": "C",
    "n2": "E",
    "L": 10,
    "W": 0.4,
    "H": 0.25,
    "coeffs": [1.5]
  },
  {
    "name": "Branche_Lointaine_F",
    "n1": "C",
    "n2": "F",
    "L": 25,
    "W": 0.35,
    "H": 0.2,
    "coeffs": [2.0]
  }
]
```
👉 Points clés :

- Mélange circulaire / rectangulaire
- Branches avec pertes différentes
- Cas typique déséquilibré → le solveur répartit automatiquement

### 4. Solve réseau
```http
GET /network/solve
```
Résultat obtenu
```http
{
  "summary": {
    "total_flow_m3h": 4000,
    "max_pressure_drop_pa": 95.3,
    "fan_power_watts": 151.27,
    "estimated_annual_cost_euros": 94.54,
    "efficiency_used": 0.7
  },
  "results": [
    {
      "duct": "Troncon_Principal_AB",
      "flow_m3h": 4000,
      "delta_p_pa": 4.32,
      "velocity_ms": 3.93
    },
    {
      "duct": "Liaison_BC",
      "flow_m3h": 3000,
      "delta_p_pa": 6.7,
      "velocity_ms": 4.24
    },
    {
      "duct": "Branche_Proche_D",
      "flow_m3h": 1000,
      "delta_p_pa": 15.13,
      "velocity_ms": 3.93
    },
    {
      "duct": "Branche_Milieu_E",
      "flow_m3h": 1500,
      "delta_p_pa": 22.4,
      "velocity_ms": 4.17
    },
    {
      "duct": "Branche_Lointaine_F",
      "flow_m3h": 1500,
      "delta_p_pa": 84.27,
      "velocity_ms": 5.95
    }
  ]
}
```
👉 Lecture technique
- La loi des nœuds est respectée, le débit total injecté est égal à la somme des sorties ($4000 = 1000 + 1500 + 1500$)
- La branche la plus éloignée ou résistante dicte la pression maximale du ventilateur ($95.3$ Pa)
- La branche F est en limite haute ($5.95$ m/s), ce qui peut générer des nuisances acoustiques
- Le coût annuel ($94.54$ €) est directement lié à la perte de charge de la branche la plus défavorisée

### 5. Visualisation
```http
GET /network/visualize
```
<p align="center">
<img src="docs/hvac_network_results.png" width="850">

👉 Permet de voir :
- structure du réseau
- répartition des débits
- différences géométriques

---

## 🔥 Roadmap
- Solveur Newton-Raphson (niveau industriel)
- Courbes ventilateur (Q–ΔP)
- Export Excel / PDF
- Interface web (dashboard)
- Multi-projets (API stateful)
- Optimisation automatique réseau

---

## ⚠️ Disclaimer

Ce projet fournit une base de calcul fiable pour pré-dimensionnement.
Toute validation réglementaire doit être confirmée par un bureau d’étude.

---

## 📁 Structure du projet
```text
hvac-expert-api/
│
├── README.md                                       # Documentation principale
├── LICENSE                                         # Licence MIT                          
├── requirements.txt                                # Dépendances Python 
├── main.py                                         # API FastAPI
├── network.py                                      # Solveur réseau
├── calculs.py                                      # Modèle physique
│
├── docs/
│   └── demo.png                                    # Image démo
│
└── .gitignore                                      # Fichiers à exclure

```
---
## 🛠️ Installation

```bash
# Cloner le dépôt
git clone https://github.com/FatehChaabat/hvac-network-solver.git
cd hvac-network-solver

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn main:app --reload    

# Accès :
API : http://127.0.0.1:8000
Swagger : http://127.0.0.1:8000/docs
```

---
## 👤 Auteur
Ingénieur en **mécanique des fluides et systèmes énergétiques**, avec un intérêt pour l’analyse de données, la modélisation et l’optimisation énergétique. 

[![Portfolio](https://img.shields.io/badge/Portfolio-fatehchaabat.github.io-blue?logo=google-chrome&logoColor=white)](https://fatehchaabat.github.io)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Fateh%20Chaabat-green?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/fateh-chaabat-08202aa9/)
[![GitHub](https://img.shields.io/badge/GitHub-FatehChaabat-red?logo=github&logoColor=white)](https://github.com/FatehChaabat)
[![ResearchGate](https://img.shields.io/badge/ResearchGate-Fateh%20Chaabat-00CCBB?logo=researchgate)](https://www.researchgate.net/profile/Fateh-Chaabat-2)

---

## 📄 Licence
Ce projet est sous **MIT License** – vous pouvez librement utiliser, modifier et partager le code et les fichiers, à condition de conserver la mention du copyright et de la licence.
