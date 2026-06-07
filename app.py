import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from core_engine import FragilityEngine

# Configuration de la page
st.set_page_config(page_title="SFS Live Arbitrage Bot", layout="wide")
st.title("🤖 Système d'Arbitrage Topologique & SFS (Live Trading)")

# Initialisation du moteur
engine = FragilityEngine(alpha=0.6, beta=0.4)

# Génération d'un faux flux de données de match pour la démo
def generate_mock_match_data():
    players = ["Marquinhos", "Vitinha", "Hakimi", "Dembélé", "Barcola", "Zaïre-Emery"]
    passes = []
    # Phase 1 : Jeu fluide (0-45 min)
    for _ in range(30):
        p1, p2 = np.random.choice(players, 2, replace=False)
        passes.append({"minute": np.random.randint(1, 45), "from": p1, "to": p2})
    # Phase 2 : Jeu bloqué/stéréotypé sur Dembélé (45-90 min)
    for _ in range(45):
        p1 = np.random.choice([p for p in players if p != "Dembélé"])
        passes.append({"minute": np.random.randint(46, 90), "from": p1, "to": "Dembélé"})
    return sorted(passes, key=lambda x: x['minute'])

if 'match_passes' not in st.session_state:
    st.session_state.match_passes = generate_mock_match_data()

# --- PANNEAU DE CONTRÔLE LATÉRAL ---
st.sidebar.header("🕹️ Flux Contextuel & Marché")
sentiment = st.sidebar.slider("NLP Sentiment Local (Entourage/Blessures)", 0.0, 1.0, 0.8, step=0.05, 
                              help="1.0 = Sérénité totale, 0.0 = Crise interne / Alerte blessure masquée")
market_odds = st.sidebar.slider("Cote Live du Favori (Bookmaker)", 1.10, 3.50, 1.35, step=0.05)

# --- ZONE D'EXÉCUTION DU MATCH ---
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("📊 Métriques Système")
    sfs_metric = st.empty()
    status_indicator = st.empty()
    entropy_metric = st.empty()

with col2:
    st.subheader("📈 Évolution Temporelle du Risque")
    chart_slot = st.empty()

with col3:
    st.subheader("⚡ Terminal d'Ordres Automatiques")
    order_log = st.empty()

# Simulation du flux de temps
start_btn = st.button("▶️ Lancer l'analyse du match en direct")

if start_btn:
    history_sfs = []
    history_minutes = []
    history_odds = []
    history_fair_odds = []
    
    log_messages = []

    for current_min in range(1, 95, 2):
        # Filtrer les passes effectuées jusqu'à la minute courante
        current_passes = [p for p in st.session_state.match_passes if p['minute'] <= current_min]
        # On ne garde que les passes des 15 dernières minutes pour coller à la dynamique récente
        recent_passes = [p for p in current_passes if p['minute'] >= current_min - 15]
        
        # Dynamique sémantique forcée à la 60e minute pour la simulation réelle
        current_sentiment = sentiment if current_min < 60 else max(0.1, sentiment - 0.5)
        
        # Calcul des scores
        sfs = engine.calculate_sfs(recent_passes, current_sentiment)
        entropy = engine.compute_network_entropy(recent_passes)
        
        # Calcul de la "vraie cote" théorique selon l'indice de fragilité
        fair_odds = market_odds * (1 + (sfs / 120))
        
        # Sauvegarde historique
        history_minutes.append(current_min)
        history_sfs.append(sfs)
        history_odds.append(market_odds)
        history_fair_odds.append(fair_odds)

        # 1. Mise à jour des Widgets Textes / Métriques
        sfs_metric.metric("Score de Fragilité (SFS)", f"{sfs} / 100")
        entropy_metric.metric("Entropie du jeu", f"{round(entropy, 2)}")
        
        # Gestion de l'état d'alerte d'arbitrage
        if sfs < 45:
            status_indicator.success("🟢 Sécurisé : Alignement tactique normal")
        elif sfs < 70:
            status_indicator.warning("🟡 Attention : Rigidité du jeu détectée")
        else:
            status_indicator.error("🔴 ALERTE ARBITRAGE : Équipe surévaluée par le marché !")
            if f"[{current_min}'] Ordre de LAY envoyé" not in "".join(log_messages):
                log_messages.insert(0, f"⚠️ **{current_min}' -- ANOMALIE DÉTECTÉE** (Marché: {market_odds} | Réel: {round(fair_odds, 2)})")
                log_messages.insert(0, f"📥 *{current_min}' -- Action : Ordre automatique LAY exécuté*")

        # 2. Mise à jour du graphique en direct via Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=history_minutes, y=history_sfs, name="Indicateur SFS (%)", line=dict(color='firebrick', width=3)))
        fig.update_layout(title=f"Match en cours : {current_min}'", xaxis_title="Minutes", yaxis_title="SFS Risk %", ylim=[0, 100])
        chart_slot.plotly_chart(fig, use_container_width=True)
        
        # 3. Affichage du journal d'ordres
        order_log.write("\n\n".join(log_messages) if log_messages else "En attente de configuration critique...")
        
        time.sleep(0.3)  # Accélération du temps pour la simulation
