import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from core_engine import FragilityEngine

# Configuration de la page
st.set_page_config(page_title="SFS Live Arbitrage Bot", layout="wide")
st.title("🤖 Système d'Arbitrage Topologique & SFS")

# Initialisation du moteur
engine = FragilityEngine(alpha=0.6, beta=0.4)

# --- PANNEAU DE CONTRÔLE LATÉRAL ---
st.sidebar.header("📋 Configuration du Match")

# NOUVEAU : Choix des équipes
equipe_favori = st.sidebar.text_input("Nom de l'équipe favorite :", "Paris SG")
equipe_outsider = st.sidebar.text_input("Nom de l'équipe adverse :", "Stade Rennais")

# NOUVEAU : Saisie des joueurs clés (séparés par des virgules)
joueurs_saisie = st.sidebar.text_input(
    "Joueurs clés de l'équipe favorite (séparés par une virgule) :", 
    "Marquinhos, Vitinha, Hakimi, Dembélé, Barcola, Zaïre-Emery"
)
# Transformation de la saisie en liste propre
players = [j.strip() for j in joueurs_saisie.split(",")]

st.sidebar.markdown("---")
st.sidebar.header("🕹️ Flux Contextuel & Marché")
sentiment = st.sidebar.slider("NLP Sentiment Local (Entourage/Blessures)", 0.0, 1.0, 0.8, step=0.05)
market_odds = st.sidebar.slider(f"Cote Live de {equipe_favori} (Bookmaker)", 1.10, 3.50, 1.35, step=0.05)

# Génération du flux de passes basé sur VOS joueurs
def generate_mock_match_data(player_list):
    passes = []
    # Phase 1 : Jeu fluide (0-45 min)
    for _ in range(30):
        p1, p2 = np.random.choice(player_list, 2, replace=False)
        passes.append({"minute": np.random.randint(1, 45), "from": p1, "to": p2})
    # Phase 2 : Jeu bloqué/stéréotypé sur le 4ème joueur de la liste (45-90 min)
    cible = player_list[3] if len(player_list) > 3 else player_list[0]
    for _ in range(45):
        p1 = np.random.choice([p for p in player_list if p != cible])
        passes.append({"minute": np.random.randint(46, 90), "from": p1, "to": cible})
    return sorted(passes, key=lambda x: x['minute'])

# Mettre à jour les passes si les joueurs changent
st.session_state.match_passes = generate_mock_match_data(players)

# --- ZONE D'EXÉCUTION DU MATCH ---
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("📊 Métriques Système")
    sfs_metric = st.empty()
    status_indicator = st.empty()
    entropy_metric = st.empty()

with col2:
    st.subheader(f"📈 Risque systémique sur {equipe_favori}")
    chart_slot = st.empty()

with col3:
    st.subheader("⚡ Terminal d'Ordres")
    order_log = st.empty()

# Simulation du flux de temps
start_btn = st.button(f"▶️ Lancer l'analyse de {equipe_favori} vs {equipe_outsider}")

if start_btn:
    history_sfs = []
    history_minutes = []
    log_messages = []

    for current_min in range(1, 95, 2):
        current_passes = [p for p in st.session_state.match_passes if p['minute'] <= current_min]
        recent_passes = [p for p in current_passes if p['minute'] >= current_min - 15]
        
        current_sentiment = sentiment if current_min < 60 else max(0.1, sentiment - 0.5)
        
        sfs = engine.calculate_sfs(recent_passes, current_sentiment)
        entropy = engine.compute_network_entropy(recent_passes)
        fair_odds = market_odds * (1 + (sfs / 120))
        
        history_minutes.append(current_min)
        history_sfs.append(sfs)

        sfs_metric.metric("Score de Fragilité (SFS)", f"{sfs} / 100")
        entropy_metric.metric("Entropie du jeu", f"{round(entropy, 2)}")
        
        if sfs < 45:
            status_indicator.success("🟢 Sécurisé : Alignement tactique normal")
        elif sfs < 70:
            status_indicator.warning("🟡 Attention : Rigidité du jeu détectée")
        else:
            status_indicator.error("🔴 ALERTE : Équipe surévaluée !")
            if f"[{current_min}']" not in "".join(log_messages):
                log_messages.insert(0, f"⚠️ **{current_min}' -- ANOMALIE** (Marché: {market_odds} | Réel: {round(fair_odds, 2)})")
                log_messages.insert(0, f"📥 *{current_min}' -- Action : LAY {equipe_favori} exécuté*")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=history_minutes, y=history_sfs, name="SFS %", line=dict(color='firebrick', width=3)))
        fig.update_layout(title=f"Match en cours : {current_min}'", xaxis_title="Minutes", yaxis_title="SFS Risk %")
        chart_slot.plotly_chart(fig, use_container_width=True)
        
        order_log.write("\n\n".join(log_messages) if log_messages else "Analyse en cours...")
        time.sleep(0.2)

