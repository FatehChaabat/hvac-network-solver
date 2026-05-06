# HVAC Network Solver API

>Cette **API FastAPI** est un moteur de calcul spécialisé dans **l'équilibrage aéraulique** et le **dimensionnement de réseaux de ventilation**. Elle permet de résoudre des systèmes complexes via une approche nodale non linéaire et d'aider au choix des composants.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-8BE9FD?style=flat&logo=openapi-initiative)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

---

## 💡 Contexte & Vision

- **Transparence** : Modèles physiques explicites (Haaland, Blasius, Darcy-Weisbach).
- **Flexibilité** : Intégrable dans des workflows d'optimisation ou de CAO via une API REST.
- **Modernité** : Documentation conforme au standard OpenAPI 3.1.

---

## 🚀 Fonctionnalités Clés

- **Solveur Nodal Non Linéaire** : Équilibrage automatique des débits par méthode itérative (Relaxation).
- **Simulation Multi-Régimes** : Calcul des pertes de charge selon la nature des matériaux (conduits lisses ou rugueux) et les singularités du réseau.
- **Expertise du Chemin Critique** : Identification automatique de la branche critique pour le dimensionnement du ventilateur.
- **Analyse Énergétique** : Estimation de la puissance réelle absorbée et du coût d'exploitation annuel.
- **Rapports PDF Professionnels** : Édition d'un document technique regroupant les bilans aérauliques, les calculs énergétiques et les schémas.
- **Assistant de Design** : Calculateur autonome pour le prédimensionnement de gaines *(Voir [l'annexe technique](#duct-sizer))*.

---

## 🧠 Modèle Physique Intégré

Le moteur s’appuie sur les équations fondamentales de la mécanique des fluides :

1. **Pertes de charge (Darcy-Weisbach)** :
<br>

$$ \Delta P = \left( f \cdot \frac{L}{D_h} + \Sigma\zeta \right) \cdot \frac{\rho \cdot v^2}{2} $$

<br>

- **$f$** : Facteur de friction (Haaland pour conduits rugueux, Blasius pour conduits lisses).
- **$L$** : Longueur linéaire du tronçon de conduit (m).
- **$D_h$** : Diamètre hydraulique calculé selon la section (m).
- **$\Sigma\zeta$** : Somme des coefficients de pertes singulières (coudes, tés, registres).
- **$\rho$** : Masse volumique de l'air (~ 1.204 $kg/m^3$ à 20°C et 1 atm).
- **$v$** : Vitesse moyenne de l'air dans la section (m/s).

2. **Puissance et Énergie** :
<br>

$$ P_{fan} = \frac{\Delta P_{totale} \cdot Q}{\eta} $$

<br>

- **$\Delta P_{totale}$** : Pression totale (statique + dynamique) au point le plus défavorable (Pa).
- **$Q$** : Débit volumique total circulant dans le ventilateur ($m^3/s$).
- **$\eta$** : Rendement global du groupe moto-ventilateur (défaut : 0.75).
- **$P_{fan}$** : Résultat en Watts.

3. **Conservation de la masse (Loi des nœuds de Kirchhoff)** :
<br>

$$ \Sigma Q_{in} - \Sigma Q_{out} = S $$

 <br>

- **$S \neq 0$** pour les points d'injection ou d'extraction.

4. **Formulation réseau (Modèle résistif)** :
<br>

$$ \Delta P = R \cdot Q^2 $$

 <br>
 
 - Chaque tronçon est modélisé par une **résistance aéraulique $R$**.
 - Cette formulation permet une résolution matricielle du réseau via une méthode de **relaxation non linéaire**.

---

## 📖 Documentation API

L'API intègre nativement deux interfaces de documentation automatique conformes au standard **OpenAPI 3.1**. Ces outils permettent de tester les requêtes en temps réel sans installer de client externe.

*   **Swagger UI** : Interface interactive permettant de tester chaque endpoint.
    > Accessible via : [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)

*   **ReDoc** : Documentation structurée, idéale pour une lecture approfondie des modèles de données.
    > Accessible via : [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

---

## 🔌 Endpoints de l'API
Le tableau suivant récapitule les principales routes du moteur de calcul :

| Méthode | Route | Description | Format |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | **Root** : Vérifie l'état du serveur | JSON |
| `POST` | `/network/init` | **Initialisation** : Réinitialise le projet actuel | JSON |
| `POST` | `/network/nodes` | **Nœuds** : Ajoute des nœuds (soufflage, extraction ou transit) | JSON |
| `POST` | `/network/ducts` | **Conduits** : Ajoute des conduits (circulaires ou rectangulaires) | JSON |
| `GET` | `/network/solve` | **Solveur** : Calcule l'équilibrage et le chemin critique | JSON |
| `GET` | `/network/visualize` | **Rendu** : Génère le schéma PNG dynamique | PNG |
| `GET` | `/network/download-report` | **Export** : Télécharge le rapport technique complet | PDF |
| `GET` | `/suggest` | **Assistant** : Suggère des dimensions ($D$ ou $W \times H$) | JSON |

---

## 🏗️ Exemple d'Utilisation (Workflow)

### 1. Initialisation (`POST /network/init`)
Purge le moteur pour garantir qu'aucun résidu de calcul précédent ne vienne fausser la nouvelle étude.

### 2. Définition des Nœuds (`POST /network/nodes`)
Définition des points de soufflage (valeurs positives), d'extraction (valeurs négatives) et de transit (valeurs nulles).
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

### 3. Définition des Conduits (`POST /network/ducts`)
Le moteur gère automatiquement le diamètre hydraulique et le régime de friction via `is_smooth`.
```json
[
  {
    "name": "Main_Section_AB",
    "n1": "A", "n2": "B",
    "L": 5, "D": 0.6,
    "coeffs": [0.3],
    "is_smooth": false
  },
  {
    "name": "Connection_BC",
    "n1": "B", "n2": "C",
    "L": 8, "D": 0.5,
    "coeffs": [0.3],
    "is_smooth": false
  },
  {
    "name": "Near_Branch_D",
    "n1": "B", "n2": "D",
    "L": 2, "D": 0.3,
    "coeffs": [1.5],
    "is_smooth": true
  },
  {
    "name": "Middle_Branch_E",
    "n1": "C", "n2": "E",
    "L": 10, "W": 0.4, "H": 0.25,
    "coeffs": [1.5],
    "is_smooth": false
  },
  {
    "name": "Far_Branch_F",
    "n1": "C", "n2": "F",
    "L": 25, "W": 0.35, "H": 0.2,
    "coeffs": [2.0],
    "is_smooth": false
  }
]
```

### 4. Résolution & Analyse (`GET /network/solve`)
Le solveur identifie le chemin critique et calcule l'impact énergétique.
```text
===== 1. NETWORK SUMMARY =====
   Total flow (m3/h)                  : 4000.0
   Critical node                      : F
   Static pressure loss (Pa)          : 96.04
   Dynamic pressure at exit (Pa)      : 21.33
   Total pressure fan (Pa)            : 117.37
   Total fan power (W)                : 173.88
   Efficiency used                    : 0.75
   Estimated annual cost (€)          : 108.68

===== 2. DUCT DETAILS =====
   Duct name                 | Air flow (m3/h)    | Velocity (m/s)     | Pressure loss (Pa)  
   ------------------------------------------------------------------------------------------
   Main_Section_AB           |       4000.0       |        3.93        |         4.16        
   Connection_BC             |       3000.0       |        4.24        |         6.43        
   Near_Branch_D             |       1000.0       |        3.93        |        15.12        
   Middle_Branch_E           |       1500.0       |        4.17        |        22.63        
   Far_Branch_F              |       1500.0       |        5.95        |        85.45        

===== 3. SOLVER METADATA =====
   Execution time (s)                 : 1.341
   Convergence status                 : stable
   Residual error (m3/s)              : 1.28e-09
   Timestamp                          : 05/05/2026 21:18:00
   Pdf report                         : report_aeraulique.pdf
```
👉 **Intelligence métier intégrée :**

- **Équilibrage précis** : Le moteur vérifie la conservation des masses à chaque nœud pour garantir des débits réels.
- **Chemin critique** : Il identifie automatiquement le point le plus défavorable (ex: nœud F) pour bien choisir le ventilateur.
- **Bilan financier** : Il calcule le coût électrique annuel pour évaluer la rentabilité de l'installation.

### 5. Visualisation (`GET /network/visualize`)
Génération du schéma technique annoté incluant les débits, les vitesses et le codage couleur par type de section.

<p align="center">
  <img src="docs/hvac_network_results.png" width="850" alt="Schéma technique du réseau aéraulique généré par l'API">
</p>

👉 **Guide de lecture :**
* **Bleu** : Conduits à section circulaire.
* **Rouge** : Conduits à section rectangulaire.
* **Vert / Orange** : Identification automatique des sources et des bouches d'extraction.
* **Épaisseur des lignes** : Proportionnelle au débit circulant dans le tronçon.

### 6. Export (`GET /network/download-report`): 
Téléchargement du rapport d'expertise PDF final, incluant les bilans techniques et le schéma du réseau, prêt pour une transmission client.

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
├── report_gen.py                                   # Générateur de rapports PDF
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

<br>
<br>
<br>
<br>
<br>

---

<a name="duct-sizer"></a>
## 🧮 Annexes : Assistant de Prédimensionnement

L'endpoint `/suggest` fonctionne comme un calculateur autonome. Il permet de déterminer les dimensions optimales de gaines (circulaires ou rectangulaires) à partir du **débit** et d'une **vitesse cible**, garantissant ainsi la maîtrise du **confort acoustique** et des **pertes de charge**.

### 1. Conduit circulaire 

**Requête :** `GET /suggest?q=1200&v=4.5&shape=circular`

**Réponse :**
```json
{
  "status": "success",
  "type": "Preliminary Sizing Assistant",
  "results": {
    "shape": "circular",
    "suggested_diameter_mm": 307,
    "section_m2": 0.0741,
    "target_velocity_ms": 4.5,
    "note": "Design optimized for acoustic comfort"
  }
}
```

### 2. Conduit rectangulaire

**Requête :** `GET /suggest?q=1200&v=4.5&shape=rectangular`

**Réponse :**
```json
{
  "status": "success",
  "type": "Preliminary Sizing Assistant",
  "results": {
    "shape": "rectangular",
    "suggested_W_mm": 333,
    "suggested_H_mm": 222,
    "section_m2": 0.0741,
    "aspect_ratio": "1.5",
    "target_velocity_ms": 4.5,
    "note": "Design optimized for acoustic comfort"
  }
}
```
