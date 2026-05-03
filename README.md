# HVAC Network Solver

>**HVAC Network Solver** est un moteur de calcul aéraulique haute performance basé sur une modélisation de réseau nodal non linéaire. Il permet le **dimensionnement**, **l’équilibrage** et **l’analyse énergétique** de réseaux complexes via une interface API moderne.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-8BE9FD?style=flat&logo=openapi-initiative)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 💡 Contexte & Vision

Ce projet propose une alternative open-source aux logiciels HVAC propriétaires souvent "boîtes noires". Il offre un moteur transparent, automatisable et prêt pour l'industrie 4.0.

- **Transparence** : Modèles physiques explicites (Haaland, Blasius, Darcy-Weisbach)
- **Flexibilité** : Intégrable dans des workflows d'optimisation ou de CAO
- **Modernité** : Documentation conforme au standard **OpenAPI 3.1**

---

## 🚀 Fonctionnalités Clés

- **Solveur Nodal Non Linéaire** : Équilibrage automatique des débits par itération
- **Simulation Multi-Régimes** : Choix entre régime rugueux (**Haaland**) et lisse (**Blasius**)
- **Expertise du Chemin Critique** : Identification automatique de la branche la plus défavorable pour le calcul du ventilateur
- **Dimensionnement Automatique** : Route `/suggest` pour calculer les dimensions optimales (D ou WxH) selon une vitesse cible
- **Analyse Financière** : Estimation de la puissance réelle et du coût énergétique annuel
- **Visualisation Dynamique** : Schémas PNG annotés avec codes couleurs et épaisseurs proportionnelles aux débits

---

## 🧠 Modèle Physique Intégré

Le moteur s'appuie sur les équations fondamentales de la mécanique des fluides :

1. **Pertes de charge (Darcy-Weisbach)** : $\Delta P = \left( f \cdot \frac{L}{D} + \Sigma\zeta \right) \cdot \frac{\rho \cdot v^2}{2}$
   - $f$ : Facteur de friction (Haaland si conduits industriels industriels et Blasius si conduits lisses)
   - $L$ : Longueur du conduit (m)
   - $D$ : Diamètre hydraulique (m)
   - $Σζ$ : Somme des coefficients de pertes singulières (coudes, tés, registres)
   - $ρ$ : Masse volumique de l’air (~1.204 kg/m³)
   - $v$ : Vitesse de l’air (m/s)
2. **Conservation de la masse** : $\Sigma Q_{in} - \Sigma Q_{out} = S$ (au nœud $i$)
    - $S > 0$ : soufflage
    - $S < 0$ : extraction
    - $S = 0$ : simple transit

3. **Formulation réseau (modèle résistif)** : $\Delta P = R \cdot Q^2$
    - Chaque conduit est caractérisé par une résistance aéraulique $R$ :
      $$R = \left[ f \cdot \frac{L}{D} + \Sigma\zeta \right] \cdot \frac{\rho}{2 \cdot S_{ect}^2}$$
    - $Q$ : Débit volumique ($m^3/s$)
    - $S_{ect}$ : Section du conduit ($m^2$)

4. **Relation débit–pression (inverse)** : $Q = \text{sign}(\Delta P) \cdot \sqrt{\frac{|\Delta P|}{R}}$
    - Cette formulation permet de déduire dynamiquement le débit circulant dans une branche en fonction de la différence de pression entre deux nœuds
---

## ⚙️ Méthode numérique

Le solveur utilise un algorithme de **relaxation nodale itérative** pour équilibrer le réseau :

1. **Initialisation** des pressions nodales $P$
2. **Calcul des débits** $Q$ dans chaque branche via la relation $Q(\Delta P, R)$
3. **Évaluation du résidu** de continuité à chaque nœud ($\Sigma Q - S$)
4. **Mise à jour** des pressions pour l'itération suivante :
   $$P^{(k+1)} = P^{(k)} + \alpha \cdot \text{imbalance}$$
   - $\alpha$ : facteur de relaxation garantissant la stabilité de la convergence numérique
   - imbalance : résidu de continuité nodale (ΣQ - S) au nœud i

---

## 🔍 Hypothèses de Modélisation

Pour le pré-dimensionnement, le moteur suit les hypothèses classiques :
- **Écoulement incompressible** et régime permanent
- **Mélange parfait** aux nœuds (pas de pertes de charge de mélange complexes)
- **Pertes singulières** discrétisées via les coefficients $\zeta$
- **Hypothèse de fluide parfait** excluant les effets transitoires ou thermiques complexes

---

## 📖 Documentation API

L'API est documentée interactivement via Swagger et Redoc.

- **Swagger UI** : [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **ReDoc** : [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

### Endpoints Principaux

| Méthode | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/network/init` | Réinitialise le projet actuel. |
| `POST` | `/network/nodes` | Ajoute des nœuds (terminaux ou transit). |
| `POST` | `/network/ducts` | Ajoute des conduits (circulaires ou rectangulaires). |
| `GET` | `/network/solve` | Résout le réseau et retourne l'analyse énergétique complète. |
| `GET` | `/suggest` | Suggère des dimensions selon $Q$ et $V_{target}$. |
| `GET` | `/network/visualize` | Génère le schéma technique dynamique. |

---

Swagger : [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)

### Endpoints

| Méthode | Route | Description |
|--------|------|------------|
| POST | /network/init | reset réseau |
| POST | /network/nodes | ajout nœuds |
| POST | /network/ducts | ajout conduits |
| GET  | /network/solve | résolution réseau |
| GET  | /network/visualize | schéma réseau |


---

## 🏗️ Exemple 

### Nœuds

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

### Conduits

```json
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

### Solve 

```json
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
👉 Lecture ingénieur
- continuité respectée
- la branche la plus résistante impose la pression système
- la dernière branche conditionne le dimensionnement ventilateur
- vérification des vitesses pour confort / acoustique

### Visualisation

<p align="center">
<img src="docs/hvac_network_results.png" width="850">

👉 Lecture :
- bleu : circulaire
- gris : rectangulaire
- épaisseur = débit

---

## 🔥 Roadmap
- Solveur Newton-Raphson (niveau industriel)
- Courbes ventilateur (Q–ΔP)
- Export Excel / PDF
- Interface web (dashboard CVC)
- Optimisation automatique réseau

---

## ⚠️ Disclaimer

Outil de pré-dimensionnement uniquement.
Ne remplace pas une étude CFD ou une validation réglementaire.

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

# Lancer le serveur
uvicorn main:app --reload    

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
MIT License
