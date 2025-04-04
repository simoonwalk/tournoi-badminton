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
        selection = st.selectbox(" ", options, key=f"select_{key}", index=0 if st.session_state.reset_pending else options.index(st.session_state.get(f"select_{key}", "Sélectionner")))
    with col2:
        joueur = st.text_input(label, key=f"text_{key}", value="" if st.session_state.reset_pending else st.session_state.get(f"text_{key}", ""))

    return selection if selection != "Sélectionner" else joueur

def set_input(set_num, joueur1, joueur2):
    st.markdown(f"**🏸 Set {set_num}**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{joueur1 or 'Joueur 1'}**")
        s1 = st.number_input(f"Set {set_num} - {joueur1 or 'Joueur 1'}", min_value=0, max_value=30, step=1, key=f"set{set_num}_j1", value=0 if st.session_state.reset_pending else st.session_state.get(f"set{set_num}_j1", 0))
    with col2:
        st.markdown(f"**{joueur2 or 'Joueur 2'}**")
        s2 = st.number_input(f"Set {set_num} - {joueur2 or 'Joueur 2'}", min_value=0, max_value=30, step=1, key=f"set{set_num}_j2", value=0 if st.session_state.reset_pending else st.session_state.get(f"set{set_num}_j2", 0))
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
    return classement

# --- INTERFACE STREAMLIT ---
st.title("🏸 Tournoi de Badminton")
tab1, tab2 = st.tabs(["🏸 Tournoi", "📜 Historique"])

with tab1:
    st.subheader("1. Enregistrement d'un match")

    joueur1 = joueur_input("Joueur 1", "joueur1")
    joueur2 = joueur_input("Joueur 2", "joueur2")

    st.markdown("**🎯 Résultats des sets :**")
    set1 = set_input(1, joueur1, joueur2)
    set2 = set_input(2, joueur1, joueur2)
    set3 = set_input(3, joueur1, joueur2)

    if st.button("✅ Enregistrer le match"):
        sets = [s for s in [set1, set2, set3] if re.match(r'^\d{1,2}-\d{1,2}$', s)]
        if joueur1 and joueur2 and joueur1 != joueur2 and sets:
            vainqueur = determiner_vainqueur(sets, joueur1, joueur2)
            if vainqueur:
                sauvegarder_match({
                    'joueur1': joueur1,
                    'joueur2': joueur2,
                    'scores': sets,
                    'vainqueur': vainqueur
                })
                st.cache_data.clear()
                st.session_state.matchs = charger_matchs()
                st.success(f"Match enregistré ! Vainqueur : {vainqueur}")
                st.session_state.reset_pending = True
                st.rerun()
            else:
                st.error("Aucun joueur n’a gagné un set valide.")
        else:
            st.error("Veuillez saisir deux joueurs différents et au moins un set valide.")

    if st.session_state.reset_pending:
        st.session_state.reset_pending = False

    st.subheader("2. Classement des joueurs")
    if st.session_state.matchs:
        classement_df = calculer_classement()
        st.dataframe(classement_df)
    else:
        st.info("Aucun match enregistré pour le moment.")

with tab2:
    st.subheader("📜 Historique des matchs")

    if st.session_state.matchs:
        rencontre_compteur = {}
        for match in st.session_state.matchs:
            j1, j2 = match["joueur1"], match["joueur2"]
            key = tuple(sorted([j1, j2]))
            rencontre_compteur[key] = rencontre_compteur.get(key, 0) + 1
            scores = match['scores'] if isinstance(match['scores'], list) else json.loads(match['scores'])

            with st.container():
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(f"**{j1} vs {j2}** — {rencontre_compteur[key]}ᵉ rencontre")
                    st.markdown(f"**Scores :** {', '.join(scores)} — **Vainqueur : {match['vainqueur']}**")
                with col2:
                    if st.button("🗑️", key=f"del_{match['id']}"):
                        supprimer_match(match['id'])
                        st.cache_data.clear()
                        st.session_state.matchs = charger_matchs()
                        st.rerun()

        if st.button("♻️ Réinitialiser tous les matchs"):
            reinitialiser_matchs()
            st.cache_data.clear()
            st.session_state.matchs = []
            st.success("Tous les matchs ont été réinitialisés.")
            st.rerun()
    else:
        st.info("Aucun match enregistré.")
