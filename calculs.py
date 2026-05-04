import math

# --- CONSTANTES PHYSIQUES (Air à 20°C) ---
RHO = 1.204  # Densité de l'air (kg/m3)
MU = 1.82e-5  # Viscosité dynamique (Pa.s)
EPSILON = 0.00015 # Rugosité moyenne (m) pour acier galvanisé

# ---------------------------
# GÉOMÉTRIE
# ---------------------------
def section_circulaire(d):
    """Calcule la section transversale d'un conduit circulaire (m2)"""
    return math.pi * (max(d, 1e-6) / 2) ** 2

def section_rectangulaire(w, h):
    """Calcule la section transversale d'un conduit rectangulaire (m2)"""
    return max(w, 1e-6) * max(h, 1e-6)

def diametre_hydraulique(w, h):
    """Calcule le diamètre hydraulique (Dh).
    Utilisé pour appliquer les formules des conduits circulaires aux rectangles.
    Dh = 4 * Section / Périmètre = 2ab / (a+b)
    """
    return (2 * w * h) / max((w + h), 1e-6)


# ---------------------------
# PHYSIQUE DE L'ÉCOULEMENT
# ---------------------------
def reynolds(v, d):
    """Calcule le nombre de Reynolds pour déterminer le régime d'écoulement."""
    return (RHO * abs(v) * max(d, 1e-6)) / MU

def facteur_friction(re, d, type_conduit="rugueux"):
    """
    Calcule le facteur de friction f.
    - re : Nombre de Reynolds
    - d : Diamètre hydraulique (m)
    - type_conduit : "lisse" (Blasius) ou "rugueux" (Haaland)
    """
    # 1. Régime Laminaire (Commun à tous les tubes)
    if re < 2300:
        return 64 / max(re, 1e-6)
    
    # 2. Régime Turbulent
    re_safe = max(re, 2301)
    
    if type_conduit == "lisse":
        # Formule de Blasius (Tube parfaitement lisse, ex: PVC, Cuivre neuf)
        # Limité à Re < 100 000
        return 0.3164 / (re_safe**0.25)
    
    else:
        # Formule de Haaland (Tube industriel, ex: Acier Galva)
        # EPSILON est défini dans tes constantes (ex: 0.00015)
        d_safe = max(d, 0.001)
        term = ((EPSILON / d_safe) / 3.7)**1.11 + (6.9 / re_safe)
        inv_sqrt_f = -1.8 * math.log10(max(term, 1e-12))
        return (1 / inv_sqrt_f)**2
    

# ---------------------------
# PRESSIONS & PERTES (LE COEUR DU SOLVEUR)
# ---------------------------
def pression_dynamique(v):
    return 0.5 * RHO * abs(v)**2

def calculer_R(L, D, section, flow, coeffs, is_smooth=False):
    """
    Calcule la résistance hydraulique R telle que DeltaP = R * Q^2
    Centralise la physique du réseau.
    Utilise Haaland pour plus de précision, avec option pour conduits lisses.
    """
    # Vitesse et Reynolds
    v = abs(flow) / max(section, 1e-6)
    re = reynolds(v, D)
    # Facteur de friction f selon le régime et la rugosité
    f = facteur_friction(re, D, "lisse" if is_smooth else "rugueux")
    # Calcul du coefficient de perte de charge (K)
    # K = (f * L/D) + somme des coefficients locaux
    facteur_k = (f * (L / max(D, 1e-6))) + sum(coeffs or [])
    # 4. Conversion en Résistance R (DeltaP = R * Q^2)
    # R = K * (Rho / (2 * Section^2))
    resistance = facteur_k * (RHO / (2 * max(section, 1e-6)**2))
    return max(resistance, 1e-6)


# ---------------------------
# FONCTIONS MÉTIER & ANALYSE
# ---------------------------
def puissance_ventilateur_reelle(debit_m3h, somme_pertes_pa, vitesse_sortie, rendement=0.75):
    """
    Calcule la puissance absorbée réelle (W).
    Compense les frottements (Pression Statique) ET l'éjection de l'air (Pression Dynamique).
    """
    # Calcul de l'énergie cinétique à fournir pour l'éjection
    p_dyn_sortie = pression_dynamique(vitesse_sortie)
    
    # Pression totale que le ventilateur doit générer
    p_totale_requise = somme_pertes_pa + p_dyn_sortie
    
    # Conversion débit et calcul de puissance
    debit_m3s = debit_m3h / 3600
    rendement_safe = max(rendement, 0.01)
    
    return (debit_m3s * abs(p_totale_requise)) / rendement_safe

def suggerer_diametre_circ(debit_m3h, v_cible):
    """Suggère un diamètre (m) selon un débit et une vitesse cible"""
    q_m3s = debit_m3h / 3600
    section_voulue = q_m3s / max(v_cible, 0.1)
    # D = racine(4 * Section / Pi)
    return round(math.sqrt((4 * section_voulue) / math.pi), 4) 

def suggerer_dimensions_rect(debit_m3h, v_cible, ratio_aspect=1.5):
    """Suggère Largeur et Hauteur (m) pour une vitesse cible"""
    q_m3s = debit_m3h / 3600
    section_voulue = q_m3s / max(v_cible, 0.1)
    # On calcule H en fonction du ratio (W = H * ratio)
    h = math.sqrt(section_voulue / ratio_aspect)
    w = h * ratio_aspect
    return round(w, 4), round(h, 4)

def calcul_cout_annuel(puissance_w, heures_par_jour=10, jours_par_an=250, prix_kwh=0.25):
    """
    Estime le coût électrique annuel
    Par défaut : Usage bureau (10h/jour, 250 jours/an), prix moyen 0.25€/kWh
    """
    conso_annuelle_kwh = (puissance_w / 1000) * heures_par_jour * jours_par_an
    return round(conso_annuelle_kwh * prix_kwh, 2)