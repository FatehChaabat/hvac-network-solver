# HVAC Network Solver API

> **Moteur de calcul aéraulique haute performance** dédié au dimensionnement et à l'équilibrage dynamique de réseaux CVC complexes. Développé avec une architecture API-First (FastAPI), il automatise la résolution physique non linéaire par une approche nodale rigoureuse pour garantir une précision industrielle et une efficience énergétique optimale.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-8BE9FD?style=flat&logo=openapi-initiative)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)



---

## 💡 Valeur Ajoutée pour l'Ingénierie

- **Rigueur physique** : Modèles explicites et validés (Darcy-Weisbach, Colebrook-White, Sutherland, Idelchik, Borda-Carnot, Bernoulli généralisé).
- **Fiabilité** : Solveur à haute précision (résidu $< 10^{-9}$ m³/s) respectant strictement la conservation des masses (Loi de Kirchhoff).
- **Universalité** : Supporte nativement les topologies mono et multi-ventilateurs, en soufflage et en extraction, avec détection automatique du mode opératoire.
- **Automatisation** : Du dimensionnement des conduits à la génération de rapports techniques complets au format PDF.
- **Flexibilité** : API REST scalable, prête pour l'intégration dans des workflows BIM, jumeaux numériques ou logiciels de CAO.

---

## 🚀 Fonctionnalités Clés


- **Simulation Multi-Régimes** : Calcul des pertes de charge (frottements et singularités) via la résolution exacte de **Colebrook-White** par bisection, adaptée à chaque conduit selon sa rugosité et son régime d'écoulement.
- **Solveur Nodal Non Linéaire** : Équilibrage automatique des débits par méthode itérative de relaxation nodale avec facteur adaptatif anti-oscillation.
- **Singularités Dynamiques Avancées** : Calcul automatique des pertes de charge des tés (Idelchik) avec détection locale du type de jonction, et des transitions convergent/divergent (Idelchik, Borda-Carnot pondéré) affectées sur la section de référence correcte.
- **Dimensionnement Multi-Ventilateurs** : Circuit critique, pression totale et puissance calculés individuellement par ventilateur (rendement propre), avec table d'équilibrage hydraulique par terminal.
- **Analyse Énergétique** : Estimation de la puissance électrique réelle absorbée (Bernoulli généralisé, méthodes B/C Almeco/AMCA) et calcul du coût d'exploitation annuel (OPEX).
- **Rapports PDF Professionnels** : Génération automatisée d'un document technique structuré incluant bilans aérauliques, audit hydraulique, analyse acoustique et recommandations de redimensionnement.
- **Assistant de Design** : Module autonome de prédimensionnement des conduits circulaires et rectangulaires selon des cibles de vitesse et de débit *(Voir [l'annexe technique](#duct-sizer))*.

---

## 🔬 Méthodologie de Calcul & Ingénierie Physique

Le moteur transforme la topologie physique du réseau en un système d'équations non linéaires, résolu par itérations successives jusqu'à l'équilibre parfait des flux.

### 1. Physique des Fluides & Propriétés Dynamiques

Le solveur adapte ses calculs aux conditions réelles de l'installation :

**Propriétés de l'air :** Calcul dynamique de la masse volumique ($\rho$) via la **loi des gaz parfaits** couplée au modèle atmosphérique standard ISA, et de la viscosité dynamique ($\mu$) via l'équation de **Sutherland** — en fonction de la température ($T$) et de l'altitude du site ($z$).

$$\rho = \frac{P_{atm}(z)}{R_{air} \cdot T} \qquad et \qquad \mu = \mu_0 \left(\frac{T}{T_0}\right)^{3/2} \frac{T_0 + S}{T + S}$$

> * $$P_{atm}(z) = 101325.0 \cdot (1.0 - 2.25577 \times 10^{-5} \cdot \text z)^{5.25588}$$.
> * $R_{air} = 287.05 \ \text{J/(kg}\cdot\text{K)}$ &nbsp; | &nbsp; $\mu_0 = 1.716 \times 10^{-5} \ \text{Pa}\cdot\text{s}$ &nbsp; | &nbsp; $S = 110.4 \ \text{K}$ &nbsp; | &nbsp; $T_0 = 273.15 \ \text{K}$ &nbsp; | &nbsp; $T = (T_{temp\textunderscore c} + T_0) \ \text{K}$.

**Friction de haute précision :** Utilisation de **Darcy-Weisbach** couplée à la résolution exacte de **Colebrook-White** par méthode de **bisection** (convergence garantie, précision $< 10^{-10}$) pour le régime turbulent, et de **Poiseuille** ($\lambda = 64/Re$) pour le régime laminaire :

$$\Delta P = \left( \lambda \cdot \frac{L}{D_h} + \Sigma\zeta \right) \cdot \frac{\rho \cdot v^2}{2} \qquad et \qquad \frac{1}{\sqrt{\lambda}} = -2\log_{10}\left(\frac{\varepsilon/D_h}{3.7} + \frac{2.51}{Re\sqrt{\lambda}}\right)$$


### 2. Résistance Aéraulique ($R$)

Le moteur condense les propriétés physiques et géométriques en une **résistance aéraulique** $R$ (Pa·s²/m⁶), réévaluée dynamiquement à chaque itération :

$$R = \left( \lambda \cdot \frac{L}{D_h} + \Sigma\zeta \right) \cdot \frac{\rho}{2 \cdot A^2} \qquad \Rightarrow \qquad \Delta P = R \cdot Q^2$$

Cette analogie avec les circuits électriques (loi d'Ohm non linéaire) garantit une fidélité physique supérieure aux modèles à résistance fixe.


### 3. Formulation par Conductance ($C$)

Pour optimiser la stabilité numérique du solveur, la résistance $R_d$ est convertie en **conductance aéraulique** $C_d = 1 / \sqrt{R_d}$, définissant la capacité du conduit $d$ à laisser passer le flux pour une différence de pression donnée :

$$Q_d = \text{sign}(\Delta P_d) \cdot C_d \cdot \sqrt{|\Delta P_d|} \qquad \text{et} \qquad Imb_n = S_n + \sum Q_{d, \text{entrants}} - \sum Q_{d, \text{sortants}}$$

<br>

  > * **$\Delta P_d$** : Différence de pression du conduit $d$ ($P_{amont} - P_{aval}$).
  > * **$S_n$** : Contrainte de débit imposée au nœud $n$ (Injection $>0$, Extraction $<0$, Transit $=0$).
  > * **$Imb_n$** : Résidu de flux. Si **$Imb_n \neq 0$**, le nœud $n$ est en déséquilibre et sa pression doit être ajustée. 

La correction de pression est calculée par ajustement itératif (linéarisation de Newton-Raphson) via la conductance totale des conduits $d$ connectés au nœud $n$ pour satisfaire la **loi de conservation de la masse** (Kirchhoff) :

$$P_{n, \text{nouveau}} = P_{n, \text{ancien}} + w \cdot \frac{Imb_n}{\displaystyle\sum_{d \in n} (0.5 \cdot C_d / \sqrt{|\Delta P_d|})}$$

> * **$w$ :** Facteur de relaxation adaptatif ($0.02 \le w \le 0.3$).
> * **Convergence :** Le processus itère jusqu'à ce que $Imb_{max} < 10^{-9} \ \text{m}^3/\text{s}$ (soit $0.0036 \ \text{l/h}$).

### 4. Solveur Nodal : Stratégie de Convergence en Deux Phases

Pour garantir robustesse et précision sur tous types de topologies, le solveur adopte une stratégie en deux phases distinctes :

#### Phase 1 — Convergence Primaire (Frottement Linéaire Pur et Singularités Constantes)
Le solveur converge sans singularités dynamiques (tés, transitions). Cela garantit une base de débits stables et évite les oscillations précoces.

#### Phase 2 — Activation des Singularités Dynamiques
Dès qu'une pré-convergence est atteinte ($Imb < 10^{-3} \text{ m}^3/\text{s}$), les singularités dynamiques sont injectées pour la convergence finale de haute précision ($< 10^{-9}$ m³/s).

### 5. Calcul Physique des Singularités

#### 5.1 Transitions Convergent / Divergent (Idelchik Ch.5)

Appliquées uniquement aux jonctions simples (2 conduits) — les tés sont exclus pour éviter tout double comptage. Le type de transition est détecté automatiquement selon le sens réel du flux (soufflage ou extraction) :

- **Convergent** : $\zeta = \zeta_{fr} + \zeta_{loc}$ (frottement Idelchik 5.6 + perte locale 5.23)
- **Divergent** : $\zeta = k(\alpha) \cdot (1-\beta)^2$ (Borda-Carnot pondéré, Idelchik/Miller)

Le ζ est toujours affecté sur la petite section (référence Idelchik). 

#### 5.2 Tés Dynamiques (Idelchik Ch.7)

Le type de jonction (**division** ou **confluence**) est détecté localement selon la direction du tronc commun au nœud — indépendamment du mode global soufflage/extraction :

- **Division** : $\zeta_b = 1 + v_r^2 - 2x$ ; $\zeta_s = 0.4(1-x)^2$
- **Confluence** : $\zeta_b = 1 + v_r^2 - 2(1-x)$ ; $\zeta_s = 0.1(1-x)^2$

Les ζ sont convertis depuis la vitesse du tronc commun vers la vitesse locale de chaque conduit via le rapport $\left(\frac{v_{commun}}{v_{local}}\right)^2$.

Les **ζ négatifs** (gain d'inertie) sont isolés et appliqués en post-traitement sans déstabiliser le solveur.

### 6. Analyse du Chemin Critique & Dimensionnement Ventilateur

#### 6.1 Identification par Ventilateur (Dijkstra)

Pour chaque ventilateur, l'algorithme de **Dijkstra** identifie le circuit le plus résistant parmi toutes ses bouches terminales. Les pertes statiques sont calculées par sommation directe sur le chemin physique, intégrant frottements et singularités.

#### 6.2 Formule de Bernoulli Généralisée

Conforme à la classification **Almeco/AMCA** (méthodes B et C) :

$$\boxed{\Delta P_{ventilateur} = \sum \Delta P_{pertes} + \frac{\rho\ \cdot V_{bouche}^2}{2}}$$

Valable en **soufflage** (entrée libre, sortie raccordée) et en **extraction** (entrée raccordée, sortie libre) — la pression dynamique d'aspiration est implicitement gérée par la courbe fabricant dans les deux cas.

#### 6.3 Dimensionnement Individuel Multi-Ventilateurs

La puissance absorbée et le coût d'exploitation sont calculés pour chaque ventilateur via son rendement $\eta_i$ :

$$\dot{W}_{fan,i} = \frac{\Delta P_{tot,i} \cdot Q_i}{\eta_i} \qquad \text{et} \qquad \dot{W}_{total} = \sum_i \dot{W}_{fan,i}$$

---

## 📖 Documentation API

L'API intègre nativement deux interfaces de documentation automatique conformes au standard **OpenAPI 3.1**.

*   **Swagger UI** : Interface interactive permettant de tester chaque endpoint.
    > Accessible via : [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)

*   **ReDoc** : Documentation structurée, idéale pour une lecture approfondie des modèles de données.
    > Accessible via : [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

---

## 🔌 Endpoints de l'API
Le tableau suivant récapitule toutes les routes du moteur de calcul :

### 📋 API du Solveur Aéraulique

| Méthode | Route | Description | Format |
| :--- | :--- | :--- | :--- |
| `GET` | `/system/info` | Diagnostic du système | JSON |
| `POST` | `/network/reset` | Réinitialisation complète du moteur | JSON |
| `POST` | `/project/info` | Configuration des métadonnées | JSON |
| `POST` | `/network/import-project` | Importation massive du projet | JSON |
| `POST` | `/network/nodes` | Configuration des points (nœuds) | JSON |
| `POST` | `/network/ducts` | Définition des conduits (liaisons) | JSON |
| `POST` | `/network/fans` | Configuration des ventilateurs | JSON |
| `POST` | `/network/calculate` | Moteur de résolution itérative | JSON |
| `GET` | `/network/schema` | Visualisation interactive | PNG |
| `GET` | `/network/report` | Générateur de rapport PDF | PDF |
| `GET` | `/network/data` | Export Jumeau Numérique (JSON) | JSON |
| `GET` | `/catalog/zeta` | Catalogue des coefficients singuliers | JSON |
| `GET` | `/tools/duct-sizer` | Utilitaire de pré-dimensionnement | JSON |
| `POST` | `/shutdown`| Arrêt sécurisé du serveur | JSON |

---

## 🏗️ Exemple d'Utilisation (Workflow)

### 1. Reset (`POST /network/reset`)
Purge le moteur pour garantir qu'aucun résidu de calcul précédent ne vienne fausser la nouvelle étude.

### 2. Informations Projet (`POST /project/info`)
Exemple : Projet = Batiment_R+4, Client = Promoteur_X, Site = Lyon_69

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
  {"name": "Main_Section_AB", "n1": "A", "n2": "B", "L": 5, "D": 0.6, "coeffs": [0.3], "is_smooth": false},
  {"name": "Connection_BC", "n1": "B", "n2": "C", "L": 8, "D": 0.5, "coeffs": [0.3], "is_smooth": false},
  {"name": "Near_Branch_BD", "n1": "B", "n2": "D", "L": 2, "D": 0.3, "coeffs": [1.5], "is_smooth": true},
  {"name": "Middle_Branch_CE", "n1": "C", "n2": "E", "L": 10, "W": 0.4, "H": 0.25, "coeffs": [1.5], "is_smooth": false},
  {"name": "Far_Branch_CF", "n1": "C", "n2": "F", "L": 25, "W": 0.35, "H": 0.2, "coeffs": [2.0], "is_smooth": false}
]
```

### 4. Résolution & Analyse (`GET /network/solve`)
Le solveur identifie le chemin critique et calcule l'impact énergétique. Les résultats sont exportés en JSON pour la console et en PDF pour le rapport d'expertise.
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
   Execution time (s)                 : 1.841
   Convergence status                 : stable
   Residual error (m3/s)              : 1e-09
   Iterations performed               : 81056
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
  <img src="docs/temp_network_schema_demo.png" width="850" alt="Schéma technique du réseau aéraulique généré par l'API">
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
│   └── temp_network_schema_demo.png                # Image démo
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

L'endpoint `/suggest` fonctionne comme un calculateur autonome. Il permet de déterminer les dimensions optimales de gaines (circulaires ou rectangulaires) à partir du **débit** et d'une **vitesse cible**, garantissant ainsi la maîtrise du **confort acoustique** et la limitation des **bruits de régénération**.

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
