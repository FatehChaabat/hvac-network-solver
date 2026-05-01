import math
from calculs import RHO, section_circulaire
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
    def __init__(self, name, n1, n2, L, D, coeffs=None, section_reelle=None):
        self.name = name
        self.n1, self.n2 = n1, n2   # Objets Node
        self.L, self.D = float(L), float(D) # Longueur et Diamètre Hydraulique
        self.coeffs = coeffs or []  # Liste des Zeta (coudes, tés...)
        # La section réelle sert au calcul précis de la vitesse
        self.section_reelle = section_reelle or section_circulaire(D)
        self.flow = 0.0             # Débit calculé (m3/s)


class HVACNetwork:
    """Moteur de résolution du réseau complet"""
    def __init__(self):
        self.nodes = {}
        self.ducts = []

    def add_node(self, name, supply=0):
        self.nodes[name] = Node(name, supply)

    def add_duct(self, name, n1, n2, L, D, coeffs=None, section_reelle=None):
        self.ducts.append(Duct(name, self.nodes[n1], self.nodes[n2], L, D, coeffs, section_reelle))

    def get_resistance(self, d):
        f_friction = 0.02
        facteur = RHO / (2 * d.section_reelle**2)
        return (f_friction * (d.L / d.D) + sum(d.coeffs)) * facteur

    def solve(self, iterations=20000, alpha=0.5):
        if not self.ducts: return
        nodes_list = list(self.nodes.values())
        nodes_list[0].P = 0.0
        for i in range(iterations):
            for d in self.ducts:
                dp = d.n1.P - d.n2.P
                R = self.get_resistance(d)
                d.flow = math.sqrt(abs(dp) / R) * (1 if dp >= 0 else -1)
            imb = {n.name: (n.supply / 3600.0) for n in nodes_list}
            for d in self.ducts:
                imb[d.n1.name] -= d.flow
                imb[d.n2.name] += d.flow
            for j in range(1, len(nodes_list)):
                nodes_list[j].P += alpha * imb[nodes_list[j].name]
            if i > 10000: alpha *= 0.8

    # --- INDENTATION CRITIQUE ICI : 4 espaces devant 'def' ---
    def draw_network(self):
        """Génère le schéma technique avec distinction Circulaire / Rectangulaire"""
        plt.clf() # Nettoie la figure
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
            
            # Détection de la forme
            is_rect = abs(d.section_reelle - (np.pi * (d.D**2) / 4)) > 0.001
            color = "#bdc3c7" if is_rect else "#3498db"
            width = d.D * 0.12 # Épaisseur visuelle basée sur le diamètre

            rect = patches.Rectangle(
                (p1[0], p1[1] - width/2), length, width,
                angle=angle, rotation_point='xy',
                linewidth=1, edgecolor='#2c3e50', facecolor=color, alpha=0.9
            )
            ax.add_patch(rect)
            
            mid = (p1 + p2) / 2
            plt.text(mid[0], mid[1] + 0.05, f"{d.name}\n{int(abs(d.flow*3600))} m3/h", 
                     ha='center', fontsize=8, fontweight='bold')

        nx.draw_networkx_nodes(G, pos, node_size=600, node_color="#e67e22")
        nx.draw_networkx_labels(G, pos, font_size=10, font_color="white", font_weight="bold")
        plt.axis('off')