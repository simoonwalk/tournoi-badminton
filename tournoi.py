import streamlit as st
from supabase_client import init_supabase
import re
import pandas as pd
import json
from collections import defaultdict

supabase = init_supabase()

# --- Charger les matchs depuis Supabase ---
@st.cache_data(ttl=60)
def charger_matchs():
    response = supabase.table('matchs').select('*').execute()
    return response.data or []

# --- Sauvegarder un match sur Supabase ---
def sauvegarder_match(match):
    supabase.table('matchs').insert(match).execute()

# --- Supprimer un match par ID ---
def supprimer_match(match_id):
    supabase.table('matchs').delete().eq('id', match_id).execute()

# --- Réinitialiser les matchs ---
def reinitialiser_matchs():
    supabase.table('matchs').delete().neq('id', 0).execute()

# --- Initialisation session state ---
if 'matchs' not in st.session_state:
    st.session_state.matchs = charger_matchs()

if 'reset_pending' not in st.session_state:
    st.session_state.reset_pending = False

# --- Fonctions reprises de ton ancien fichier ---
def joueur_input(label, key):
    joueurs = list({match['joueur1'] for match in st.session_state.matchs} | {match['joueur2'] for match in st.session_state.matchs})
    options = ["Sélectionner"] + joueurs

    col1, col2 = st.columns([1, 2.5])
    with col1:
        selection = st.selectbox(" ", options, key=f"select_{key}", index=0 if st.session_state.reset_pending else None)
    with col2:
        joueur = st.text_input(label, key=f"text_{key}", value="" if st.session_state.reset_pending else None)

    return selection if selection != "Sélectionner" else joueur

def set_input(set_num, joueur1, joueur2):
    st.markdown(f"**🏸 Set {set_num}**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{joueur1 or 'Joueur 1'}**")
        s1 = st.number_input(f"Set {set_num} - {joueur1 or 'Joueur 1'}", min_value=0, max_value=30, step=1, key=f"set{set_num}_j1", value=0 if st.session_state.reset_pending else None)
    with col2:
        st.markdown(f"**{joueur2 or 'Joueur 2'}**")
        s2 = st.number_input(f"Set {set_num} - {joueur2 or 'Joueur 2'}", min_value=0, max_value=30, step=1, key=f"set{set_num}_j2", value=0 if st.session_state.reset_pending else None)
    return f"{s1}-{s2}" if (s1 != 0 or s2 != 0) else ""

def determiner_vainqueur(sets, joueur1, joueur2):
    j1, j2 = 0, 0
    for s in sets:
        try:
            score1, score2 = map(int, s.split('-'))
            if score1 > score2:
                j1 += 1
            elif score2 > score1:
                j2 += 1
        except:
            continue

    if j1 == 0 and j2 == 0:
        return None
    return joueur1 if j1 > j2 else joueur2

def calculer_classement():
    joueurs = defaultdict(lambda: {'Nom': '', 'Points': 0, 'Matchs': 0, 'Total': 0})
    victoires = {}

    for match in st.session_state.matchs:
        j1, j2 = match['joueur1'], match['joueur2']
        gagnant = match['vainqueur']
        scores = match['scores'] if isinstance(match['scores'], list) else json.loads(match['scores'])

        joueurs[j1]['Nom'] = j1
        joueurs[j2]['Nom'] = j2

        joueurs[j1]['Matchs'] += 1
        joueurs[j2]['Matchs'] += 1

        for score in scores:
            s1, s2 = map(int, score.split('-'))
            joueurs[j1]['Total'] += s1
            joueurs[j2]['Total'] += s2

        adversaires = tuple(sorted([j1, j2]))
        if adversaires not in victoires:
            victoires[adversaires] = {j1: 0, j2: 0}

        victoires[adversaires][gagnant] += 1
        nb_victoires = victoires[adversaires][gagnant]

        if nb_victoires == 1:
            joueurs[gagnant]['Points'] += 5
        elif nb_victoires == 2:
            joueurs[gagnant]['Points'] += 3
        else:
            joueurs[gagnant]['Points'] += 1

    classement = pd.DataFrame(joueurs.values()).sort_values(by=['Points', 'Total'], ascending=[False, False])
    classement.index += 1
    classement.insert(0, "Rang", [medal(i) for i in classement.index])
    return classement

def medal(rank):
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}ᵉ")

# --- INTERFACE STREAMLIT ---
st.title("🏸 Tournoi de Badminton")
tab1, tab2 = st.tabs(["🏸 Tournoi", "📜 Historique"])

# Le reste de l'interface complète est ajouté ci-dessous, intégrant les appels à st.cache_data.clear() après chaque opération importante.
