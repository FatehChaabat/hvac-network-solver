# HVAC Network Solver API

> **Moteur de calcul aéraulique haute performance** dédié au dimensionnement et à l'équilibrage dynamique de réseaux CVC complexes. Développé avec une architecture API-First (FastAPI), il automatise la résolution physique non linéaire par une approche nodale rigoureuse pour garantir une précision industrielle et une efficience énergétique optimale.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-8BE9FD?style=flat&logo=openapi-initiative)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🌐 Application en Ligne

> L'API est déployée et accessible en production sur Render. Aucune installation requise.

<p align="center">
  <a href="https://hvac-api-wtuu.onrender.com/docs" target="_blank">
    <img src="https://img.shields.io/badge/🚀%20Accéder%20à%20l'API%20Live-Swagger%20UI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="API Live"/>
  </a>
</p>

> **[https://hvac-api-wtuu.onrender.com/docs](https://hvac-api-wtuu.onrender.com/docs)**
>
> ⚠️ *L'instance Render se met en veille après inactivité — prévoir ~30 secondes au premier chargement.*


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

**Propriétés de l'air :** Calcul dynamique de la masse volumique ($\rho$) via la **loi des gaz parfaits** couplée au modèle atmosphérique standard ISA, et de la viscosité dynamique ($\mu$) via l'équation de **Sutherland** — en fonction de la température ($T$) et de l'altitude du site ($z$) :

$$\rho = \frac{P_{atm}(z)}{R_{air} \cdot T} \qquad et \qquad \mu = \mu_0 \left(\frac{T}{T_0}\right)^{3/2} \frac{T_0 + S}{T + S}$$

> $P_{atm}(z) = 101325 \cdot (1 - 2.25577 \times 10^{-5} \cdot z)^{5.25588}$ — Modèle ISA standard (valable jusqu'à 11 000 m)

<br>

**Friction de haute précision :** Résolution exacte de **Colebrook-White** par **bisection** (convergence garantie, précision $< 10^{-10}$) pour le régime turbulent, et **Poiseuille** ($\lambda = 64/Re$) pour le régime laminaire :

$$\Delta P = \left( \lambda \cdot \frac{L}{D_h} + \Sigma\zeta \right) \cdot \frac{\rho \cdot v^2}{2} \qquad et \qquad \frac{1}{\sqrt{\lambda}} = -2\log_{10}\left(\frac{\varepsilon/D_h}{3.7} + \frac{2.51}{Re\sqrt{\lambda}}\right)$$


### 2. Résistance Aéraulique & Formulation par Conductance

Le moteur condense les propriétés physiques et géométriques en une **résistance aéraulique** $R$ (Pa·s²/m⁶), réévaluée dynamiquement à chaque itération (analogie Loi d'Ohm non linéaire) :

$$R = \left( \lambda \cdot \frac{L}{D_h} + \Sigma\zeta \right) \cdot \frac{\rho}{2 \cdot A^2} \qquad \Rightarrow \qquad \Delta P = R \cdot Q^2$$

<br>

Pour optimiser la stabilité numérique du solveur, la résistance $R_d$ est convertie en **conductance aéraulique** $C_d = 1 / \sqrt{R_d}$, définissant la capacité du conduit $d$ à laisser passer le flux $Q_d$ pour une différence de pression donnée $\Delta P_d$:

$$Q_d = \text{sign}(\Delta P_d) \cdot C_d \cdot \sqrt{|\Delta P_d|} \qquad \text{et} \qquad Imb_n = S_n + \sum Q_{d, \text{entrants}} - \sum Q_{d, \text{sortants}}$$

  > * **$S_n$** : Contrainte de débit imposée au nœud $n$ (Injection $>0$, Extraction $<0$, Transit $=0$). **$Imb_n$** : Résidu de flux au nœud $n$.

<br>

La correction de pression à chaque nœud $n$ est calculée par **linéarisation de Newton-Raphson** (ajustement itératif) via la conductance totale des conduits $d$ connectés :

$$P_{n, \text{nouveau}} = P_{n, \text{ancien}} + w \cdot \frac{Imb_n}{\displaystyle\sum_{d \in n} (0.5 \cdot C_d / \sqrt{|\Delta P_d|})}$$

> * **$w$ :** Facteur de relaxation adaptatif ($0.02 \le w \le 0.3$).


### 3. Stratégie de Convergence en Deux Phases

| Phase | Condition | Contenu |
|---|---|---|
| **Phase 1** — Convergence primaire | Démarrage | Frottement linéaire + singularités constantes uniquement |
| **Phase 2** — Singularités dynamiques | $Imb < 10^{-3}$ m³/s | Activation tés + transitions convergent/divergent |
| **Convergence finale** | $Imb < 10^{-9}$ m³/s | Arrêt — résidu ≈ 0.0036 l/h |


### 4. Calcul Physique des Singularités

**Transitions Convergent/Divergent (Idelchik Ch.5) :** Appliquées uniquement aux jonctions simples (2 conduits). Les tés sont exclus pour éviter tout double comptage. Le type de transition est détecté automatiquement selon le sens réel du flux (soufflage ou extraction). Le ζ est toujours affecté sur la petite section (référence Idelchik) :
- **Convergent** : $\zeta = \zeta_{fr} + \zeta_{loc}$ (frottement Idelchik 5.6 + perte locale 5.23)
- **Divergent** : $\zeta = k(\alpha) \cdot (1-\beta)^2$ (Borda-Carnot pondéré, Idelchik/Miller)

**Tés Dynamiques (Idelchik Ch.7) :** Type de jonction détecté **localement** selon la direction du tronc commun — indépendamment du mode global soufflage/extraction :
- **Division** : $\zeta_b = 1 + v_r^2 - 2x$ ; $\zeta_s = 0.4(1-x)^2$
- **Confluence** : $\zeta_b = 1 + v_r^2 - 2(1-x)$ ; $\zeta_s = 0.1(1-x)^2$

Les ζ sont convertis depuis la vitesse du tronc commun vers la vitesse locale de chaque conduit via le rapport $\left(\frac{v_{commun}}{v_{local}}\right)^2$. Les **ζ négatifs** (gain d'inertie) sont isolés et appliqués en post-traitement sans déstabiliser le solveur.


### 5. Analyse du Chemin Critique & Dimensionnement Ventilateur

**Identification par Ventilateur (Dijkstra)** : Pour chaque ventilateur, l'algorithme de **Dijkstra** identifie le circuit le plus résistant parmi toutes ses bouches terminales. Les pertes statiques sont calculées par sommation directe sur le chemin physique, intégrant frottements et singularités.

**Formule de Bernoulli Généralisée** : Conforme à la classification **Almeco/AMCA** (méthodes B et C) :

$$\boxed{\Delta P_{ventilateur} = \sum \Delta P_{pertes} + \frac{\rho\ \cdot V_{bouche}^2}{2}}$$

Valable en **soufflage** (entrée libre, sortie raccordée) et en **extraction** (entrée raccordée, sortie libre) — la pression dynamique d'aspiration est implicitement gérée par la courbe fabricant dans les deux cas.

**Dimensionnement Individuel Multi-Ventilateurs** : La puissance absorbée est calculée pour chaque ventilateur via son rendement ($\eta_i$) :

$$\dot{W}_{fan,i} = \frac{\Delta P_{tot,i} \cdot Q_i}{\eta_i} \qquad \text{et} \qquad \dot{W}_{total} = \sum_i \dot{W}_{fan,i}$$

Le coût annuel estimé est dérivé du temps de service annuel ($T_{annuel}$ en heures) et du coût unitaire de l'énergie ($C_{kWh}$) :

$$\boxed{OPEX = \dot{W}_{total} \cdot T_{annuel} \cdot C_{kWh} \cdot 10^{-3}}$$

---

## 🔌 Endpoints de l'API
L'API est structurée autour des endpoints suivants pour piloter le solveur, de la configuration du réseau jusqu'à l'export des résultats :

| Méthode | Route | Description | Format |
| :--- | :--- | :--- | :--- |
| `GET` | `/system/info` | Diagnostic du système | JSON |
| `POST` | `/network/reset` | Réinitialisation complète du moteur | JSON |
| `POST` | `/project/info` | Configuration des métadonnées projet | JSON |
| `POST` | `/network/import-project` | **Import global** (nœuds + conduits + fans) | JSON |
| `POST` | `/network/nodes` | Configuration des nœuds | JSON |
| `POST` | `/network/ducts` | Définition des conduits | JSON |
| `POST` | `/network/fans` | Configuration des ventilateurs | JSON |
| `POST` | `/network/calculate` | **Solveur** — calcul complet | JSON |
| `GET` | `/network/schema` | Schéma du réseau | PNG |
| `GET` | `/network/report` | Rapport technique PDF | PDF |
| `GET` | `/network/data` | Export données JSON complet | JSON |
| `GET` | `/catalog/zeta` | Catalogue des coefficients singuliers | JSON |
| `POST` | `/tools/duct-sizer` | Prédimensionnement des conduits | JSON |

---

## 🏗️ Tutoriel Rapide — Tester l'API

Accédez à **[https://hvac-api-wtuu.onrender.com/docs](https://hvac-api-wtuu.onrender.com/docs)** et suivez ces étapes dans l'interface Swagger :

### Étape 1 — Reset (`POST /network/reset`)
Purgez le moteur avant chaque nouvelle simulation.

### Étape 2 (optionnelle) — Informations Projet (`POST /project/info`)
Définissez les métadonnées de l'étude pour les rapports (ex. Projet: Batiment_R+4, Client: Promoteur_X, Site: Lyon_69)

### Étape 3 — Import du projet (`POST /network/import-project`)
Copiez-collez le JSON suivant en un seul appel pour configurer simultanément les nœuds, les conduits et les ventilateurs :

```json
{
  "nodes": [
    { "name": "FAN_01", "supply": 2200.0 },
    { "name": "JN_01", "supply": 0.0 },
    { "name": "JN_A", "supply": 0.0 },
    { "name": "OF_01", "supply": -550.0 },
    { "name": "OF_02", "supply": -500.0 },
    { "name": "JN_B", "supply": 0.0 },
    { "name": "OF_03", "supply": -600.0 },
    { "name": "OF_04", "supply": -550.0 }
  ],
  "edges": [
    { "name": "main_trunk", "n1": "FAN_01", "n2": "JN_01", "L": 2.0, "D": 0.45, "epsilon": 0.15, "coeffs": [0, ""], "is_branch": false },
    { "name": "to_junction_A", "n1": "JN_01", "n2": "JN_A", "L": 3.0, "D": 0.40, "epsilon": 0.15, "coeffs": [0, ""], "slope_degrees": 15, "is_branch": false },
    { "name": "office_1", "n1": "JN_A", "n2": "OF_01", "L": 2.0, "W": 0.2, "H": 0.17, "epsilon": 0.02, "coeffs": [0, "grille_soufflage_ailettes"], "is_branch": true },
    { "name": "office_2", "n1": "JN_A", "n2": "OF_02", "L": 2.0, "W": 0.2, "H": 0.16, "epsilon": 0.02, "coeffs": [0, "diffuseur_plafonnier_4_voies"], "is_branch": true },
    { "name": "transit_to_B", "n1": "JN_A", "n2": "JN_B", "L": 3.0, "D": 0.30, "epsilon": 0.15, "coeffs": [0, ""], "is_branch": false },
    { "name": "office_3", "n1": "JN_B", "n2": "OF_03", "L": 2.0, "W": 0.2, "H": 0.18, "epsilon": 0.02, "coeffs": [0, "bouche_extraction_standard"], "is_branch": true },
    { "name": "office_4", "n1": "JN_B", "n2": "OF_04", "L": 2.0, "W": 0.2, "H": 0.17, "epsilon": 0.02, "coeffs": [0, "diffuseur_rotatif"], "is_branch": true }
  ],
  "fans": [
    { "name": "Main_Fan", "node_name": "FAN_01", "rendement": 0.75, "description": "Fresh air supply" }
  ]
}
```

> * **Convention** : Les nœuds ventilateurs doivent impérativement porter le préfixe `fan_` (ex: `fan_1`, `fan_principal`) — détection automatique par le moteur.
> * **Catalogue ζ** : Les clés d'accessoires (`grille_soufflage_ailettes`, `diffuseur_plafonnier_4_voies`...) sont disponibles via `GET /catalog/zeta`.

### Étape 4 — Calcul (`POST /network/calculate`)
Exécutez le solveur avec les paramètres par défaut ou ajustez la température et l'altitude pour affiner les propriétés de l'air. L'exemple ci-dessous illustre une simulation réalisée dans les conditions standards de Lyon (20°C, 170 m d'altitude).

### Étape 5 — Fonctionnalités et Génération de documents
Une fois le calcul validé, l'API génère instantanément vos documents techniques :

**Schéma réseau (`GET /network/schema`) :** Génération automatique du schéma technique du réseau, optimisé (DPI 100) pour garantir une génération rapide sur les environnements Cloud.

<p align="center">
  <img src="docs/Batiment_R+4_Promoteur_X_20260526_194113.png" width="850" alt="Schéma technique du réseau aéraulique généré par l'API">
</p>

**Rapport technique (`GET /network/report`) :** Rapport PDF complet incluant l'audit hydraulique, les pressions, les recommandations acoustiques et le schéma du réseau.

📎 [Exemple de rapport PDF](docs/Batiment_R+4_Promoteur_X_20260526_194113.pdf)

**Données d'intégration (`GET /network/data`) :** Export structuré au format JSON pour une interopérabilité avec vos outils de CAO ou BIM.

📎 [Exemple de rapport JSON](docs/Batiment_R+4_Promoteur_X_20260526_194113.json)

---

## 🛠️ Déploiement et Test Local

Pour exécuter une simulation complète et générer les rapports localement, utilisez le script de démarrage rapide :

```bash
# Cloner ce dépôt
git clone https://github.com/FatehChaabat/hvac-network-solver.git
cd hvac-network-solver

# Installer la dépendance nécessaire
pip install requests

# Lancer le script de démonstration
python quick_start.py
```
> 💡 **Note importante :** Ce dépôt public est une interface de démonstration et de documentation. Le moteur de calcul propriétaire est hébergé dans un dépôt privé, synchronisé via un pipeline CI/CD sur Render.

---

## 📁 Structure du Dépôt

```text
hvac-network-solver/
│
├── README.md                       # Documentation complète & exemples
├── LICENSE                         # Licence MIT
├── quick_start.py                  # Script de démarrage rapide
│
├── docs/
│   ├── Batiment_R+4_Promoteur_X_20260526_194113.png              # Schéma réseau exemple
│   ├── Batiment_R+4_Promoteur_X_20260526_194113.pdf              # Rapport PDF exemple
│   └── Batiment_R+4_Promoteur_X_20260526_194113.json             # Rapport JSON exemple
│
└── .gitignore                      # Fichiers exclus du dépôt
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

<br> <br> <br>

---

<h2 align="center">ANNEXES</h2>


<a name="duct-sizer"></a>
## 🧮 Assistant de Prédimensionnement — `POST /tools/duct-sizer`

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
