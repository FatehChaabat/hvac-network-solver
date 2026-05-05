# HVAC Network Solver

>**HVAC Network Solver** est un moteur de calcul aéraulique haute performance basé sur une modélisation de réseau nodal non linéaire. Il permet le **dimensionnement**, **l’équilibrage** et **l’analyse énergétique** de réseaux complexes via une interface API moderne.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-8BE9FD?style=flat&logo=openapi-initiative)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

---

## 💡 Contexte & Vision

Ce projet propose une alternative open-source aux logiciels HVAC propriétaires souvent "boîtes noires". Il offre un moteur transparent, automatisable et prêt pour l'industrie 4.0.

- **Transparence** : Modèles physiques explicites (Haaland, Blasius, Darcy-Weisbach)
- **Flexibilité** : Intégrable dans des workflows d'optimisation ou de CAO
- **Modernité** : Documentation conforme au standard **OpenAPI 3.1**

---

## 🚀 Fonctionnalités Clés

- **Solveur Nodal Non Linéaire** : Équilibrage automatique des débits par itération (Relaxation)
- **Simulation Multi-Régimes** : Choix entre régime rugueux (**Haaland**) et lisse (**Blasius**)
- **Expertise du Chemin Critique** : Identification automatique de la branche la plus défavorable pour le calcul du ventilateur via algorithme de graphe (Dijkstra)
- **Dimensionnement Automatique** : Route `/suggest` pour calculer les dimensions optimales (D ou WxH) selon une vitesse cible
- **Analyse Énergétique** : Estimation de la puissance réelle absorbée et du coût annuel (Standard Bureau 2500h/an)
- **Visualisation Dynamique** : Schémas PNG annotés avec codes couleurs (sections) et épaisseurs proportionnelles aux débits

---

## 🧠 Modèle Physique Intégré

Le moteur s'appuie sur les équations fondamentales de la mécanique des fluides :

1. **Pertes de charge Darcy-Weisbach (en Pa)** : $\Delta P = \left( f \cdot \frac{L}{D} + \Sigma\zeta \right) \cdot \frac{\rho \cdot v^2}{2}$
   - $f$ : Facteur de friction (**Haaland** pour conduits rugueux, **Blasius** pour parois lisses)
   - $Σζ$ : Somme des coefficients de pertes singulières (coudes, tés, registres)
   - $ρ$ : Masse volumique de l’air (~1.204 kg/m³)

2. **Puissance et Énergie** : $P_{fan} = \frac{\Delta P_{totale} \cdot Q}{\eta}$
   - $\Delta P_{totale}$ : Pression totale (statique + dynamique de sortie) en Pa.
   - $Q$ : Débit volumique exprimé en $m^3/s$.
   - $\eta$ : Rendement global du groupe moto-ventilateur (valeur par défaut : 0.75).
   - Résultat $P_{fan}$ en **Watts**.

3. **Conservation de la masse** : $\Sigma Q_{in} - \Sigma Q_{out} = S$ (Loi des nœuds de Kirchhoff)
   - $S \neq 0$ pour les points d'injection ou d'extraction

4. **Formulation réseau (Modèle résistif)** : $\Delta P = R \cdot Q^2$
   - Chaque conduit est modélisé par une résistance aéraulique $R$ dépendant de sa géométrie et de son état de surface

---

## 📖 Documentation API

L'API est documentée interactivement via Swagger et Redoc :

- **Swagger UI** : [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **ReDoc** : [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

### Endpoints Principaux

| Méthode | Route | Description | Format |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | **Root** : Vérification de l'état du serveur | JSON |
| `POST` | `/network/init` | Réinitialise le projet actuel | JSON |
| `POST` | `/network/nodes` | Ajoute des nœuds (terminaux ou transit) | JSON |
| `POST` | `/network/ducts` | Ajoute des conduits (circulaires ou rectangulaires) | JSON |
| `GET` | `/network/solve` | **Solveur** : Calcule l'équilibrage et le chemin critique | JSON |
| `GET` | `/network/visualize` | **Rendu** : Génère le schéma PNG dynamique | PNG |
| `GET` | `/suggest` | **Optimisation** : Suggère des dimensions ($D$ ou $W \times H$) | JSON |

---

## 🏗️ Exemple d'Utilisation

### 1. Définition des Nœuds
On définit les points d'injection (soufflage) et les points d'extraction (terminaux)
```json
[
  {"name": "A", "supply": 4000},
  {"name": "B", "supply": 0},
  {"name": "C", "supply": 0},
  {"name": "D", "supply": -1000},
  {"name": "E", "supply": -1500},
  {"name": "F", "supply": -1500}
]
```

### 2. Définition des Conduits
Le moteur gère automatiquement le calcul du diamètre hydraulique pour les sections rectangulaires
```json
[
  {
    "name": "Troncon_Principal_AB",
    "n1": "A", "n2": "B",
    "L": 5, "D": 0.6,
    "coeffs": [0.3],
    "is_smooth": false
  },
  {
    "name": "Liaison_BC",
    "n1": "B", "n2": "C",
    "L": 8, "D": 0.5,
    "coeffs": [0.3],
    "is_smooth": false
  },
  {
    "name": "Branche_Proche_D",
    "n1": "B", "n2": "D",
    "L": 2, "D": 0.3,
    "coeffs": [1.5],
    "is_smooth": true
  },
  {
    "name": "Branche_Milieu_E",
    "n1": "C", "n2": "E",
    "L": 10, "W": 0.4, "H": 0.25,
    "coeffs": [1.5],
    "is_smooth": false
  },
  {
    "name": "Branche_Lointaine_F",
    "n1": "C", "n2": "F",
    "L": 25, "W": 0.35, "H": 0.2,
    "coeffs": [2.0],
    "is_smooth": false
  }
]
```

### 3. Résultat de l'Analyse
Le solveur identifie le chemin critique et calcule l'impact énergétique
```json
{
  "summary": {
    "total_flow_m3h": 4000,
    "critical_node": "F",
    "static_pressure_loss_pa": 96.04,
    "dynamic_pressure_at_exit_pa": 21.33,
    "total_pressure_fan_pa": 117.37,
    "total_fan_power_watts": 173.88,
    "efficiency_used": 0.75,
    "estimated_annual_cost_euros": 108.68
  },
  "results": [
    {
      "duct": "Troncon_Principal_AB",
      "n1": "A",
      "n2": "B",
      "flow_m3h": 4000,
      "velocity_ms": 3.93,
      "delta_p_pa": 4.16,
      "friction_model": "Haaland (Rugueux)"
    },
    {
      "duct": "Liaison_BC",
      "n1": "B",
      "n2": "C",
      "flow_m3h": 3000,
      "velocity_ms": 4.24,
      "delta_p_pa": 6.43,
      "friction_model": "Haaland (Rugueux)"
    },
    {
      "duct": "Branche_Proche_D",
      "n1": "B",
      "n2": "D",
      "flow_m3h": 1000,
      "velocity_ms": 3.93,
      "delta_p_pa": 15.12,
      "friction_model": "Blasius (Lisse)"
    },
    {
      "duct": "Branche_Milieu_E",
      "n1": "C",
      "n2": "E",
      "flow_m3h": 1500,
      "velocity_ms": 4.17,
      "delta_p_pa": 22.63,
      "friction_model": "Haaland (Rugueux)"
    },
    {
      "duct": "Branche_Lointaine_F",
      "n1": "C",
      "n2": "F",
      "flow_m3h": 1500,
      "velocity_ms": 5.95,
      "delta_p_pa": 85.45,
      "friction_model": "Haaland (Rugueux)"
    }
  ]
}
```
👉 Lecture ingénieur
* **Continuité flux** : Conservation des masses respectée (loi des nœuds)
* **Pression système** : Dictée par la somme cumulée du chemin le plus résistant
* **Dimensionnement ventilateur** : Conditionné par l'énergie cinétique de la dernière branche
* **Confort / Acoustique** : Vérification directe via le monitoring des vitesses
* **Précision physique** : Choix dynamique entre modèles Haaland et Blasius

---

### 4. Visualisation

<p align="center">
  <img src="docs/hvac_network_results.png" width="850" alt="Schéma technique du réseau aéraulique généré par l'API">
</p>

👉 **Guide de lecture :**
* 🔵 **Bleu** : Conduits à section circulaire.
* 🔴 **Rouge** : Conduits à section rectangulaire.
* 🟢 **Vert / 🟠 Orange** : Identification automatique des sources (Supply) et des bouches d'extraction.
* **Épaisseur des lignes** : Proportionnelle au débit circulant dans le tronçon.

---

## 📁 Structure du projet
```text
hvac-network-solver/
│
├── README.md                                       # Documentation principale
├── LICENSE                                         # Licence MIT                          
├── requirements.txt                                # Dépendances Python 
├── main.py                                         # API FastAPI
├── network.py                                      # Solveur réseau
├── calculs.py                                      # Modèle physique
│
├── docs/
│   └── hvac_network_results.png                    # Image démo
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

# Lancer l'API 
python main.py  

```

---

## 👤 Auteur
Ingénieur en mécanique des fluides et énergétique, spécialisé en modélisation et systèmes CVC.

[![Portfolio](https://img.shields.io/badge/Portfolio-fatehchaabat.github.io-blue?logo=google-chrome&logoColor=white)](https://fatehchaabat.github.io)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Fateh%20Chaabat-green?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/fateh-chaabat-08202aa9/)
[![GitHub](https://img.shields.io/badge/GitHub-FatehChaabat-red?logo=github&logoColor=white)](https://github.com/FatehChaabat)
[![ResearchGate](https://img.shields.io/badge/ResearchGate-Fateh%20Chaabat-00CCBB?logo=researchgate)](https://www.researchgate.net/profile/Fateh-Chaabat-2)

---

## 📄 Licence
Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
