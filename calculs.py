import math

# --- CONSTANTES ---
RHO = 1.2        # Densité de l'air (kg/m3) à 20°C
MU = 1.8e-5      # Viscosité de l'air (Pa.s)

def section_circulaire(d):
    """Calcule la surface d'un cercle (m2)"""
    return math.pi * (max(d, 1e-6) / 2) ** 2

def section_rectangulaire(w, h):
    """Calcule la surface d'un rectangle (m2)"""
    return max(w, 1e-6) * max(h, 1e-6)

def diametre_hydraulique(w, h):
    """Calcule le diamètre équivalent pour les calculs de friction (Dh)"""
    return (2 * w * h) / (w + h)

def puissance_ventilateur(debit_m3h, dp, rendement=0.6):
    """Calcule la puissance électrique nécessaire (Watts)"""
    debit_m3s = debit_m3h / 3600
    # P = (Q * DeltaP) / rendement
    return (debit_m3s * abs(dp)) / max(rendement, 0.01)

def diametre_optimal(debit_m3h, v_cible):
    """Suggère un diamètre (m) selon un débit et une vitesse cible"""
    q_m3s = debit_m3h / 3600
    section_voulue = q_m3s / max(v_cible, 0.1)
    # D = racine(4 * Section / Pi)
    return math.sqrt((4 * section_voulue) / math.pi)

def suggerer_dimensions_rect(debit_m3h, v_cible, ratio_aspect=1.5):
    """Suggère Largeur et Hauteur (m) pour une vitesse cible"""
    q_m3s = debit_m3h / 3600
    section_voulue = q_m3s / max(v_cible, 0.1)
    # On calcule H en fonction du ratio (W = H * ratio)
    h = math.sqrt(section_voulue / ratio_aspect)
    w = h * ratio_aspect
    return round(w, 3), round(h, 3)

def calcul_cout_annuel(puissance_w, heures_par_jour=10, jours_par_an=250, prix_kwh=0.25):
    """
    Estime le coût électrique annuel
    Par défaut : Usage bureau (10h/jour, 250 jours/an), prix moyen 0.25€/kWh
    """
    consommation_kwh = (puissance_w / 1000) * heures_par_jour * jours_par_an
    cout = consommation_kwh * prix_kwh
    return round(cout, 2)