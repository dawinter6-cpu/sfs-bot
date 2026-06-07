import networkx as nx
import numpy as np

class FragilityEngine:
    def __init__(self, alpha=0.6, beta=0.4):
        self.alpha = alpha  # Importance de la tactique (graphe)
        self.beta = beta    # Importance du contexte (NLP)
        
    def compute_network_entropy(self, pass_events):
        """
        Construit le réseau de passes et calcule son entropie de centralité.
        """
        G = nx.DiGraph()
        
        # Ingestion des passes dans le graphe dynamique
        for p in pass_events:
            u, v = p['from'], p['to']
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1)
                
        if len(G.nodes) < 3:  # Pas assez de joueurs connectés pour analyser
            return 3.0  # Entropie de base (jeu fluide par défaut)
            
        try:
            # Calcul de la centralité des joueurs (Vecteur propre)
            centrality = nx.eigenvector_centrality_numpy(G, weight='weight')
            values = np.array(list(centrality.values()))
            
            # Normalisation en probabilités
            probabilities = values / np.sum(values)
            # Calcul de l'entropie de Shannon
            entropy = -np.sum(probabilities * np.log2(probabilities + 1e-9))
            return float(entropy)
        except:
            return 2.5

    def calculate_sfs(self, pass_events, local_sentiment_score):
        """
        Calcule le Score de Fragilité Systémique final (0 à 100).
        """
        entropy = self.compute_network_entropy(pass_events)
        
        # Plus l'entropie baisse (jeu stéréotypé), plus H_topo augmente
        H_topo = max(0.0, 3.5 - entropy) / 3.5
        
        # Plus le sentiment est proche de 0 (tensions), plus S_local augmente
        S_local = 1.0 - local_sentiment_score
        
        # Combinaison linéaire pondérée
        sfs_score = (self.alpha * H_topo) + (self.beta * S_local)
        return min(100.0, max(0.0, round(sfs_score * 100, 1)))
