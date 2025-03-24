import streamlit as st
from supabase_client import init_supabase
import re
import pandas as pd

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

# --- Fonctions reprises de ton ancien fichier ---
def joueur_input(label, key):
    joueurs = list({match['joueur1'] for match in st.session_state.matchs} | {match['joueur2'] for match in st.session_state.matchs})
    options = ["Sélectionner"] + joueurs

    col1, col2 = st.columns([1, 2.5])
    with col1:
        selection = st.selectbox(" ", options, key=f"select_{key}")
    with col2:
        joueur = st.text_input(label, key=f"text_{key}")

    return selection if selection != "Sélectionner" else joueur

def set_input(set_num, joueur1, joueur2):
    st.markdown(f"**🏸 Set {set_num}**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{joueur1 or 'Joueur 1'}**")
        s1 = st.number_input(f"Set {set_num} - {joueur1 or 'Joueur 1'}", min_value=0, max_value=30, step=1, key=f"set{set_num}_j1")
    with col2:
        st.markdown(f"**{joueur2 or 'Joueur 2'}**")
        s2 = st.number_input(f"Set {set_num} - {joueur2 or 'Joueur 2'}", min_value=0, max_value=30, step=1, key=f"set{set_num}_j2")
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
    joueurs = {}
    for match in st.session_state.matchs:
        j1 = match['joueur1']
        j2 = match['joueur2']
        vainqueur = match['vainqueur']
        scores = match['scores'] if isinstance(match['scores'], list) else eval(match['scores'])

        for joueur in [j1, j2]:
            if joueur not in joueurs:
                joueurs[joueur] = {'Nom': joueur, 'Points': 0, 'Matchs': 0, 'Total': 0}

        joueurs[vainqueur]['Points'] += 3
        joueurs[j1]['Matchs'] += 1
        joueurs[j2]['Matchs'] += 1

        for set_score in scores:
            s1, s2 = map(int, set_score.split('-'))
            joueurs[j1]['Total'] += s1
            joueurs[j2]['Total'] += s2

    classement = pd.DataFrame(joueurs.values()).sort_values(by=['Points', 'Total'], ascending=[False, False])
    classement.index += 1
    classement.insert(0, "Rang", [medal(i) for i in classement.index])
    return classement

def medal(rank):
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}ᵉ")

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
                st.session_state.matchs = charger_matchs()
                st.success(f"Match enregistré ! Vainqueur : {vainqueur}")
                st.rerun()
            else:
                st.error("Aucun joueur n’a gagné un set valide.")
        else:
            st.error("Veuillez saisir deux joueurs différents et au moins un set valide.")

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
            scores = match['scores'] if isinstance(match['scores'], list) else eval(match['scores'])

            with st.container():
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(f"**{j1} vs {j2}** — {rencontre_compteur[key]}ᵉ rencontre")
                    st.markdown(f"**Scores :** {', '.join(scores)} — **Vainqueur : {match['vainqueur']}**")
                with col2:
                    if st.button("🗑️", key=f"del_{match['id']}"):
                        supprimer_match(match['id'])
                        st.session_state.matchs = charger_matchs()
                        st.rerun()

        if st.button("♻️ Réinitialiser tous les matchs"):
            reinitialiser_matchs()
            st.session_state.matchs = []
            st.success("Tous les matchs ont été réinitialisés.")
            st.rerun()
    else:
        st.info("Aucun match enregistré.")

