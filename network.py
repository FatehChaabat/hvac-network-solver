import math
from calculs import section_circulaire, calculer_R, pression_dynamique, calcul_cout_annuel, puissance_ventilateur_reelle 
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

class Node:
    """Représente un point de connexion ou une bouche d'air"""
    def __init__(self, name, supply=0):
        self.name = name
        self.supply = float(supply) # m3/h (Positif=Injecté, Négatif=Extrait)
        self.P = 0.0                # Pression calculée au nœud (Pa)

class Duct:
    """Représente un tronçon de gaine"""
    def __init__(self, name, n1, n2, L, D, coeffs=None, section_reelle=None, is_smooth=False):
        self.name = name
        self.n1, self.n2 = n1, n2   # Objets Node
        self.L, self.D = float(L), float(D) # Longueur et Diamètre Hydraulique
        self.coeffs = coeffs or []  # Liste des Zeta (coudes, tés...)

        # Paramètre pour choisir l'algorithme de friction
        self.is_smooth = is_smooth 

        # La section réelle sert au calcul précis de la vitesse
        self.section_reelle = section_reelle or section_circulaire(D)
        self.flow = 0.0             # Débit calculé (m3/s)


class HVACNetwork:
    """Moteur de résolution du réseau complet"""
    def __init__(self):
        self.nodes = {}
        self.ducts = []
        self.efficiency = 0.75   # Rendement global du ventilateur (ajustable) 

    def add_node(self, name, supply=0):
        self.nodes[name] = Node(name, supply)

    def add_duct(self, name, n1, n2, L, D, coeffs=None, section_reelle=None, is_smooth=False):
        self.ducts.append(Duct(
            name, self.nodes[n1], self.nodes[n2], 
            L, D, coeffs, section_reelle, is_smooth
        ))

    def get_resistance(self, d):
        """Appelle la fonction physique centralisée"""
        return calculer_R(d.L, d.D, d.section_reelle, d.flow, d.coeffs, d.is_smooth)

    def solve(self, iterations=100000, alpha=0.1): # Alpha réduit pour stabilité avec Haaland
        if not self.ducts: return
        
        nodes_list = list(self.nodes.values())
        # Le premier nœud est la référence (Ventilateur ou Atmosphère = 0 Pa)
        
        for i in range(iterations):
            # Mise à jour des débits en fonction des pressions actuelles
            for d in self.ducts:
                dp = d.n1.P - d.n2.P
                R = self.get_resistance(d)
                # Loi de débit : Q = sqrt(DeltaP / R)
                d.flow = math.sqrt(abs(dp) / max(R, 1e-9)) * (1 if dp >= 0 else -1)
            
            # Calcul de l'imbalance de masse à chaque nœud (Kirchhoff)
            imb = {n.name: (n.supply / 3600.0) for n in nodes_list}
            for d in self.ducts:
                imb[d.n1.name] -= d.flow
                imb[d.n2.name] += d.flow
            
            # Ajustement des pressions pour réduire l'imbalance
            # On ne change pas P du nœud 0 (nœud de référence)
            for j in range(1, len(nodes_list)):
                nodes_list[j].P += alpha * imb[nodes_list[j].name]
            
            # Convergence douce
            if i > iterations * 0.8: alpha *= 0.5
    
    def get_results(self):
        """Génère les résultats détaillés et le bilan cumulé du chemin critique"""
        
        # 1. Créer un graphe orienté pour calculer les cumuls
        G = nx.DiGraph()
        for d in self.ducts:
            dp = abs(d.n1.P - d.n2.P)
            # On stocke dp comme un 'poids' sur l'arête
            G.add_edge(d.n1.name, d.n2.name, weight=dp, name=d.name)

        # 2. Trouver le nœud "source" (celui qui a supply=0 ou pas d'entrée)
        # On suppose que le premier nœud ajouté est la source (le ventilateur)
        source_node = list(self.nodes.keys())[0]

        # 3. Calculer les pertes cumulées vers chaque nœud
        # nx.single_source_dijkstra_path_length calcule la somme des poids (DP)
        all_cumulated_losses = nx.single_source_dijkstra_path_length(G, source_node, weight='weight')
        
        # Le nœud critique est celui qui a la perte CUMULÉE la plus élevée
        critical_node = max(all_cumulated_losses, key=all_cumulated_losses.get)
        max_static_loss = all_cumulated_losses[critical_node]

        # 4. Construire la liste des résultats détaillés
        results_list = []
        for d in self.ducts:
            vitesse = abs(d.flow) / d.section_reelle
            dp_statique = abs(d.n1.P - d.n2.P)
            model_used = "Blasius (Lisse)" if d.is_smooth else "Haaland (Rugueux)"

            results_list.append({
                "duct": d.name,
                "n1": d.n1.name,
                "n2": d.n2.name,
                "flow_m3h": round(abs(d.flow * 3600), 2),
                "velocity_ms": round(vitesse, 2),
                "delta_p_pa": round(dp_statique, 2),
                "friction_model": model_used
            })

        # 5. Vitesse de sortie au nœud critique
        v_exit = 0
        for res in results_list:
            if res["n2"] == critical_node:
                v_exit = res["velocity_ms"]
                break

        # 6. Synthèse finale
        total_flow_h = sum(n.supply for n in self.nodes.values() if n.supply > 0)
        fan_power = puissance_ventilateur_reelle(
            debit_m3h=total_flow_h,
            somme_pertes_pa=max_static_loss, # C'est maintenant bien la SOMME
            vitesse_sortie=v_exit,
            rendement=self.efficiency
        )
        
        cost_annual = calcul_cout_annuel(fan_power)
        dp_dyn = pression_dynamique(v_exit)

        return {
            "summary": {
                "total_flow_m3h": round(total_flow_h, 2),
                "critical_node": critical_node,
                "static_pressure_loss_pa": round(max_static_loss, 2), # SOMME des DP
                "dynamic_pressure_at_exit_pa": round(dp_dyn, 2),
                "total_pressure_fan_pa": round(max_static_loss + dp_dyn, 2),
                "total_fan_power_watts": round(fan_power, 2),
                "efficiency_used": self.efficiency,
                "estimated_annual_cost_euros": cost_annual
            },
            "results": results_list
        }

    def draw_network(self):
        """Génère le schéma technique avec distinction Circulaire / Rectangulaire"""
        plt.clf()
        G = nx.DiGraph()
        for d in self.ducts:
            G.add_edge(d.n1.name, d.n2.name)

        pos = nx.spring_layout(G, seed=42, k=1.5)
        ax = plt.gca()

        for d in self.ducts:
            p1 = np.array(pos[d.n1.name])
            p2 = np.array(pos[d.n2.name])
            v = p2 - p1
            angle = np.degrees(np.arctan2(v[1], v[0]))
            length = np.linalg.norm(v)
            
            # Détection visuelle Circulaire (bleu) vs Rectangulaire (gris)
            # Comparaison section réelle vs section d'un cercle parfait
            is_rect = abs(d.section_reelle - (math.pi * (d.D**2) / 4)) > 0.001
            color = "#bdc3c7" if is_rect else "#3498db"
            width = d.D * 0.15 

            rect = patches.Rectangle(
                (p1[0], p1[1] - width/2), length, width,
                angle=angle, rotation_point='xy',
                linewidth=1, edgecolor='#2c3e50', facecolor=color, alpha=0.9
            )
            ax.add_patch(rect)
            
            mid = (p1 + p2) / 2
            plt.text(mid[0], mid[1] + 0.05, f"{d.name}\n{round(abs(d.flow*3600))} m3/h", 
                     ha='center', fontsize=8, fontweight='bold')
            
            vitesse_val = abs(d.flow) / max(d.section_reelle, 1e-6)
            plt.text(mid[0], mid[1] - 0.05, f"{vitesse_val:.2f} m/s", 
                     ha='center', fontsize=7, fontstyle='italic')

        nx.draw_networkx_nodes(G, pos, node_size=600, node_color="#e67e22")
        nx.draw_networkx_labels(G, pos, font_size=10, font_color="white", font_weight="bold")
        plt.axis('off')

