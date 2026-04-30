# HVAC Expert API

>API de calcul aéraulique pour réseaux HVAC (ventilation & désenfumage).  
Ce projet permet de modéliser, résoudre et visualiser un réseau complet avec estimation énergétique.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🚀 Démo

👉 Interface API (Swagger)  
http://127.0.0.1:8000/docs

👉 Génération de réseau + visualisation :

![demo](docs/demo.png)

---

## ⚙️ Fonctionnalités

### 🔹 Calcul réseau
- Résolution des débits (m³/h)
- Calcul des pressions nodales
- Pertes de charge linéaires + singulières
- Support soufflage / extraction

### 🔹 Géométrie
- Gaines circulaires
- Gaines rectangulaires
- Diamètre hydraulique automatique
- Section réelle utilisée pour vitesse

### 🔹 Énergie
- Puissance ventilateur
- Estimation coût annuel
- Paramétrable (rendement, prix élec)

### 🔹 Dimensionnement
- Diamètre optimal
- Dimensions rectangulaires (ratio contrôlé)

### 🔹 Visualisation
- Schéma automatique du réseau
- Débits affichés sur chaque gaine
- Distinction visuelle :
  - 🔵 circulaire
  - ⚪ rectangulaire

---

## 🧠 Modèle physique

### Conservation de masse
\[
\sum Q = S
\]

### Relation pression-débit
\[
Q = \sqrt{\frac{\Delta P}{R}}
\]

### Résistance aéraulique
\[
R = \left(f \frac{L}{D} + \sum \zeta\right) \cdot \frac{\rho}{2S^2}
\]

---

## 📦 Installation

```bash
git clone https://github.com/ton-user/hvac-expert-api.git
cd hvac-expert-api

pip install -r requirements.txt
