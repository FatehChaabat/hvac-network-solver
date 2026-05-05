import math

# -------------------------------------------
# CONSTANTES PHYSIQUES (Air à 20°C et 1 atm) 
# -------------------------------------------
RHO = 1.204                                                                                          # Densité de l'air (kg/m3)
MU = 1.82e-5                                                                                         # Viscosité dynamique (Pa.s)
EPSILON = 0.00015                                                                                    # Rugosité typique pour un acier galvanisé (m) - Utilisée dans la formule de Haaland pour les conduits rugueux

# -------------------------------------------
# PARAMÈTRES ÉCONOMIQUES (Valeurs par défaut)
# -------------------------------------------
RENDEMENT_DEFAUT = 0.75                                                                              # Rendement typique pour un ventilateur de qualité moyenne
HEURES_PAR_JOUR = 10                                                                                 # Nombre d'heures d'utilisation par jour, pour estimer la consommation énergétique quotidienne du ventilateur
JOURS_PAR_AN = 250                                                                                   # Nombre de jours d'utilisation par an, pour estimer la consommation énergétique annuelle du ventilateur
PRIX_KWH = 0.25                                                                                      # Prix moyen de l'électricité par kWh en euros, pour estimer le coût de fonctionnement du ventilateur

# -------------------------------------------
# GÉOMÉTRIE
# -------------------------------------------
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


# -------------------------------------------
# PHYSIQUE DE L'ÉCOULEMENT
# -------------------------------------------
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
    # 1. Facteur de friction pour régime laminaire  
    if re < 2300:                                                                                    
        return 64 / max(re, 1e-6)                                                                    
    
    # 2. Facteur de friction pour régime turbulent
    re_safe = max(re, 2301)                                                                          
    
    # Conduit lisse (formule de Blasius)
    if type_conduit == "lisse": 
        return 0.3164 / (re_safe**0.25)                                                              
    
    # Conduit rugueux (formule de Haaland)
    else:
        d_safe = max(d, 0.001)                                                                       
        term = ((EPSILON / d_safe) / 3.7)**1.11 + (6.9 / re_safe)                                    
        inv_sqrt_f = -1.8 * math.log10(max(term, 1e-12))                                             
        return (1 / inv_sqrt_f)**2                                                                   
    

# -------------------------------------------
# PRESSIONS & RESISTANCE HYDRAULIQUE
# -------------------------------------------
def pression_dynamique(v):
    """
    Calcule la pression dynamique (Pa) à partir de la vitesse de l'écoulement. 
    Utilisée pour calculer les pertes de charge dynamiques dans le réseau.
    """
    return 0.5 * RHO * abs(v)**2                                                                     

def calculer_R(L, D, section, flow, coeffs, is_smooth=False):                                        
    """
    Calcule la résistance hydraulique R telle que DeltaP = R * Q^2
    Centralise la physique du réseau.
    Utilise Haaland pour plus de précision, avec option pour conduits lisses.
    """  
    # Vitesse de l'écoulement avec garde-fou numérique (10^-6)
    v = abs(flow) / max(section, 1e-6)   
    # Nombre de Reynolds                                                             
    re = reynolds(v, D)                                                                              
    
    # Facteur de friction (Blasius si lisse et Haaland si rugueux)
    f = facteur_friction(re, D, "lisse" if is_smooth else "rugueux")                                 
   
    # Calcul du facteur K total (f * L/D + pertes locales)
    facteur_k = (f * (L / max(D, 1e-6))) + sum(coeffs or [])                                         
    
    # Résistance hydraulique R = K * (rho / (2 * S^2)) 
    resistance = facteur_k * (RHO / (2 * max(section, 1e-6)**2))                                     
    return max(resistance, 1e-6)                                                                     


# -------------------------------------------
# FONCTIONS MÉTIER & ANALYSE
# -------------------------------------------
def puissance_ventilateur_reelle(debit_m3h, somme_pertes_pa, vitesse_sortie, rendement=RENDEMENT_DEFAUT):    
    """
    Calcule la puissance absorbée réelle (W).
    Compense les frottements (Pression Statique) ET l'éjection de l'air (Pression Dynamique).
    """ 
    # Pression dynamique
    p_dyn_sortie = pression_dynamique(vitesse_sortie)                                                
    
    # Ppression totale requise par le ventilateur (frottements + pression dynamique)
    p_totale_requise = somme_pertes_pa + p_dyn_sortie                                                
    
    # Conversion du débit de m3/h à m3/s pour calcul de puissance 
    debit_m3s = debit_m3h / 3600      
    # Rendement de ventilateur avec garde-fou numérique pour éviter division par zéro (0.01 minimum)                                                               
    rendement_safe = max(rendement, 0.01)                                                            
    
    return (debit_m3s * abs(p_totale_requise)) / rendement_safe                                     

def suggerer_diametre_circ(debit_m3h, v_cible):
    """Suggère un diamètre (m) selon un débit et une vitesse cible"""
    q_m3s = debit_m3h / 3600    

    # Diamètre optimal pour un conduit circulaire avec la section calculée                                                                    
    section_voulue = q_m3s / max(v_cible, 0.1)     
    return round(math.sqrt((4 * section_voulue) / math.pi), 4)                                       

def suggerer_dimensions_rect(debit_m3h, v_cible, ratio_aspect=1.5):
    """Suggère Largeur et Hauteur (m) pour une vitesse cible"""
    q_m3s = debit_m3h / 3600      

    # Calcul de la section nécessaire pour atteindre la vitesse cible.                                                                     
    section_voulue = q_m3s / max(v_cible, 0.1)  

    # Calcul de la hauteur et largeur optimales en respectant le ratio d'aspect donné ( 1.5)                                                     
    h = math.sqrt(section_voulue / ratio_aspect)                                                     
    w = h * ratio_aspect                                                                             
    return round(w, 4), round(h, 4)                                                                  

def calcul_cout_annuel(puissance_w, h_jour = HEURES_PAR_JOUR, j_an=JOURS_PAR_AN, prix=PRIX_KWH):
    """
    Estime le coût électrique annuel
    Par défaut : Usage bureau (10h/jour, 250 jours/an), prix moyen 0.25€/kWh
    """
    # Conversion de la puissance de W à kW et calcul de la consommation annuelle en kWh
    conso_annuelle_kwh = (puissance_w / 1000) * h_jour * j_an                                        
    return round(conso_annuelle_kwh * prix, 2)                                                       