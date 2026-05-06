import math
import numpy as np
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from calculs import (
    section_circulaire, 
    calculer_R, 
    pression_dynamique, 
    calcul_cout_annuel, 
    puissance_ventilateur_reelle, 
    RENDEMENT_DEFAUT
)

class Node:
    """Modélise un nœud du réseau (bifurcation, injection ou extraction)."""
    def __init__(self, name, supply=0):                                                            
        self.name = name                                                                               # Identifiant unique (ex: 'Bouche_1')
        self.supply = float(supply)                                                                    # Débit imposé (m³/h) : >0 Source, <0 extraction, =0 Transit
        self.P = 0.0                                                                                   # Pression statique calculée (Pa) - Initialement à 0, ajusté lors de la résolution du réseau
                                                                                                        
class Duct:
    """Modélise un tronçon de gaine et ses propriétés de perte de charge."""
    def __init__(self, name, n1, n2, L, D, coeffs=None, section_reelle=None, is_smooth=False):
        self.name = name
        self.n1, self.n2 = n1, n2                                                                      # Nœuds amont et aval (instances Node)
        self.L, self.D = float(L), float(D)                                                            # Longueur et Diamètre Hydraulique (m)
        self.coeffs = coeffs or []                                                                     # Liste des coefficients singuliers Σζ
        self.is_smooth = is_smooth                                                                     # Type de rugosité (Blasius vs Haaland)
        self.section_reelle = section_reelle or section_circulaire(D)                                  # Section (m²) pour v = Q/S
        self.flow = 0.0                                                                                # Débit calculé (m³/s) - Initialement à 0, ajusté lors de la résolution du réseau


class HVACNetwork:
    """
    Moteur de résolution orchestrant la topologie et les lois physiques.
    Gère la cohérence entre Darcy-Weisbach et la conservation des débits (Kirchhoff).
    """
    def __init__(self):                                                                                
        self.nodes = {}                                                                                # Registre des nœuds {nom: Node}
        self.ducts = []                                                                                # Liste de tronçons (Duct)
        self.efficiency = RENDEMENT_DEFAUT                                                             # Rendement global du ventilateur. Ici 0.75, mais ajustable dans calculs.py.

    def add_node(self, name, supply=0): 
        """Ajoute un point d'injection, d'extraction ou de transit."""                                                               
        self.nodes[name] = Node(name, supply)                                                          

    def add_duct(self, name, n1, n2, L, D, coeffs=None, section_reelle=None, is_smooth=False):  
        """Crée un conduit entre deux nœuds existants avec ses propriétés physiques."""       
        self.ducts.append(Duct(                                                                        
            name, self.nodes[n1], self.nodes[n2],                                                
            L, D, coeffs, section_reelle, is_smooth
        ))                                                                                             

    def get_resistance(self, d):                                                                       
        """Calcule la résistance hydraulique via le module physique centralisé."""
        return calculer_R(d.L, d.D, d.section_reelle, d.flow, d.coeffs, d.is_smooth)                   

    def solve(self, iterations=100000, alpha=0.1):   
        """
        Résout le réseau par relaxation de pression (analogie Loi des Nœuds).
        Ajuste itérativement P pour annuler l'imbalance de débit à chaque nœud.
        """  
        # Retourne 0 si vide pour éviter le bug NoneType                                                 
        if not self.ducts: return 0.0                                                               
        
        # Nœud 0 sert de référence (0 Pa), les autres sont ajustés pour équilibrer les flux
        nodes_list = list(self.nodes.values())                                                         
                
        for i in range(iterations):    
            # 1. Mise à jour des débits (Loi de Darcy-Weisbach)                                                                
            for d in self.ducts:                                                                 
                dp = d.n1.P - d.n2.P                                                                   
                R = self.get_resistance(d)           
                # Calcul Q = sign(dp) * sqrt(|dp|/R) avec garde-fou numérique                                                   
                d.flow = math.sqrt(abs(dp) / max(R, 1e-9)) * (1 if dp >= 0 else -1)                    

            # 2. Calcul du bilan des flux à chaque nœud "Imbalance" (Loi de Kirchhoff)      
            imb = {n.name: (n.supply / 3600.0) for n in nodes_list}                                    
            for d in self.ducts:                                                                       
                imb[d.n1.name] -= d.flow                                                               
                imb[d.n2.name] += d.flow   

            # Calcul du résidu final pour l'API
            # On prend l'imbalance maximale absolue constatée sur les nœuds : imb = (Débit entrant) - (Débit sortant)
            max_imb = max(abs(v) for v in imb.values())                                                            

            # 3. Correction des pressions par gradient décent (Relaxation)            
            for j in range(1, len(nodes_list)):      
                # P augmente si le nœud est en surpression (imbalance > 0)                                                  
                nodes_list[j].P += alpha * imb[nodes_list[j].name]                                     
            
            # 4. Affinage final : réduction du pas pour stabiliser la convergence
            if i > iterations * 0.8: alpha *= 0.5 

        # On retourne le résidu à l'API ---
        return max_imb                                                   
     
    def get_results(self):                                                                            
        """
        Génère le bilan technique complet : analyse du chemin critique, 
        calculs aérauliques détaillés et synthèse énergétique.
        """
        
        # 1. Analyse Topologique et Pertes de Charge
        G = nx.DiGraph()                                                                               
        for d in self.ducts:   
            # Utiliser un graphe pondéré par les DeltaP réels pour identifier le chemin critique via Dijkstra                                                                        
            dp = abs(d.n1.P - d.n2.P)
            # Exemple pour un conduit D01 : G.add_edge("Source", "Bouche_1", weight=150, name="D01")
            G.add_edge(d.n1.name, d.n2.name, weight=dp, name=d.name)                                   

        # Le premier nœud déclaré est considéré comme la source de référence (0 Pa)                                                                                               
        source_node = list(self.nodes.keys())[0]                                                       

        # Calcul des pertes cumulées via Dijkstra pour trouver le point le plus défavorisé. 
        all_cumulated_losses = nx.single_source_dijkstra_path_length(G, source_node, weight='weight')  
        critical_node = max(all_cumulated_losses, key=all_cumulated_losses.get)                        
        max_static_loss = all_cumulated_losses[critical_node]                                          

        # 2. Compilation des résultats détaillés par tronçon
        results_list = []      
        # Vitesse au point critique pour le calcul dynamique final 
        v_exit = 0                                                                                     

        for d in self.ducts:                                                                           
            vitesse = abs(d.flow) / d.section_reelle                                                   
            dp_statique = abs(d.n1.P - d.n2.P)    

            if d.n2.name == critical_node:
                v_exit = vitesse                                                     
                                 
            results_list.append({                                                                      
                "duct": d.name,
                "n1": d.n1.name,
                "n2": d.n2.name,
                "flow_m3h": round(abs(d.flow * 3600), 2),
                "velocity_ms": round(vitesse, 2),
                "delta_p_pa": round(dp_statique, 2),
                "friction_model": "Blasius (Lisse)" if d.is_smooth else "Haaland (Rugueux)"
            })
                                                                                 
        # 3. Synthèse Energétique et Dimensionnement Ventilateur
        total_flow_h = sum(n.supply for n in self.nodes.values() if n.supply > 0)       

        # Calcul de la puissance absorbée incluant pertes statiques et pression dynamique de sortie
        fan_power = puissance_ventilateur_reelle(                                                      
            debit_m3h=total_flow_h,                                                                    
            somme_pertes_pa=max_static_loss,                                                           
            vitesse_sortie=v_exit,                                                                   
            rendement=self.efficiency                                                                  
        )
                                                               
        dp_dyn = pression_dynamique(v_exit ) 
        cost_annual = calcul_cout_annuel(fan_power)                                                           
        return {                                                                                       
            "summary": {
                "total_flow_m3h": round(total_flow_h, 2),                                              
                "critical_node": critical_node,                                                        
                "static_pressure_loss_pa": round(max_static_loss, 2),                                  
                "dynamic_pressure_at_exit_pa": round(dp_dyn, 2),                                       
                "total_pressure_fan_pa": round(max_static_loss + dp_dyn, 2),                           
                "total_fan_power_watts": round(fan_power, 2),                                          
                "efficiency_used": self.efficiency,                                                    
                "estimated_annual_cost_euros": cost_annual                                             
            },
            # Liste détaillée des résultats pour chaque conduit du réseau
            "results": results_list                                                                    
        }

    def draw_network(self, save_path=None):                                                                                    
        """Génère le schéma technique avec distinction Circulaire / Rectangulaire et Noeuds dynamiques."""
        
        # Si aucun chemin "save_path" n'est fourni, on utilise le dossier docs par défaut
        if save_path is None:
            save_path = os.path.join("docs", "temp_network_schema.png")
        
        # Nettoyage préventif
        plt.clf()                                                                                     
        plt.close('all') 
        fig = plt.figure(figsize=(18, 12))   

        # Construction de la topologie via NetworkX                                                            
        G = nx.DiGraph()                                                                              
        for d in self.ducts:                                                                          
            G.add_edge(d.n1.name, d.n2.name)

        # Calcul du positionnement (Layout élastique avec espacement k=1.5)
        pos = nx.spring_layout(G, seed=42, k=1.5)                                                                     
        ax = plt.gca()                                                                                

        # 1. PRÉPARATION DES COULEURS DES NŒUDS
        node_colors = []
        for node_id in G.nodes:
            # Sécurité : on cherche la valeur du supply associée au nom du noeud
            # Si self.nodes est un dictionnaire { 'Nom': objet_node }
            if isinstance(self.nodes, dict):
                node_obj = self.nodes.get(node_id)
                supply = node_obj.supply if node_obj else 0
            else:
                # Si self.nodes est une liste d'objets
                node_obj = next((n for n in self.nodes if n.name == node_id), None)
                supply = node_obj.supply if node_obj else 0
            
            # Application de la couleur selon le débit
            if supply > 0:
                node_colors.append("#27AE60")    # Vert : Source
            elif supply < 0:
                node_colors.append("#E67E22")    # Orange : Extraction
            else:
                node_colors.append("#BDC3C7")    # Gris : Transit

        # 2. DESSIN DES CONDUITS (PATCHES)
        for d in self.ducts:                                                                          
            p1 = np.array(pos[d.n1.name])                                                              
            p2 = np.array(pos[d.n2.name])    
            
            # Calcul des vecteurs géométriques
            v = p2 - p1                                                                               
            angle = np.degrees(np.arctan2(v[1], v[0]))                                                 
            length = np.linalg.norm(v)                                                                
            
            # Distinction visuelle : Rouge (Rect) vs Bleu (Circ)
            # Comparaison section réelle vs théorique circulaire
            is_rect = abs(d.section_reelle - (math.pi * (d.D**2) / 4)) > 0.001                          
            color = '#C0392B' if is_rect else '#2980B9'                                                             
            width = d.D * 0.15                                                                         

            # Création du patch Rectangle orienté
            rect = patches.Rectangle(                                                                  
                (p1[0], p1[1] - width/2), length, width,                                               
                angle=angle, rotation_point='xy',                                                      
                linewidth=1, edgecolor='black', facecolor=color, alpha=0.9                          
            )
            ax.add_patch(rect)                                                                         
            
            # Annotations techniques (Débit et Vitesse) au centre du conduit
            mid = (p1 + p2) / 2                                                                        
            plt.text(mid[0], mid[1] + 0.0, f"{d.name}\n{round(abs(d.flow*3600))} m3/h",                
                     ha='center', fontsize=11, fontweight='bold', color='black')                                       
            
            vitesse_val = abs(d.flow) / max(d.section_reelle, 1e-6)                                                 
            plt.text(mid[0], mid[1] - 0.06, f"{vitesse_val:.2f} m/s",                                   
                     ha='center', fontsize=11, fontstyle='italic', color='black')                                       

        # 3. RENDU FINAL DES NŒUDS ET LABELS
        nx.draw_networkx_nodes(
            G, pos, 
            node_size=3000, 
            node_color=node_colors, 
            edgecolors="black", 
            linewidths=1
        )                                          
        
        # Labels des nœuds en noir pour la lisibilité sur fond de couleur
        nx.draw_networkx_labels(G, pos, font_size=14, font_color="black", font_weight="bold")           
        
        #plt.title("Schéma du Réseau de Ventilation", fontsize=14, fontweight='bold', pad=20)                    
        plt.axis('equal')                                                                              
        plt.axis('off')                                                                                
        plt.tight_layout()
        
        # Sauvegarder en haute résolution avec recadrage auto 
        if save_path:            
            plt.savefig(save_path, format="png", dpi=300, bbox_inches='tight')

        # Fermer peut libérer la mémoire
        plt.close(fig)
        