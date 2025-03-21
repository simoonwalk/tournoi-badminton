import streamlit as st
import pandas as pd
import re

# Initialisation des variables de suppression
if 'match_to_delete' not in st.session_state:
    st.session_state.match_to_delete = None
if 'just_deleted' not in st.session_state:
    st.session_state.just_deleted = False

# Initialisation des données
if 'matchs' not in st.session_state:
    st.session_state.matchs = []

# Initialisation des champs pour la réinitialisation après enregistrement
for key in ["text_joueur1", "select_joueur1", "text_joueur2", "select_joueur2", "set1", "set2", "set3"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Fonction pour extraire les joueurs existants
def get_all_players():
    players = set()
    for match in st.session_state.matchs:
        players.add(match['joueur1'])
        players.add(match['joueur2'])
    return sorted(players)

# Fonction pour créer un champ de saisie hybride (texte + liste déroulante)
def joueur_input(label, key):
    players = get_all_players()
    col1, col2 = st.columns([3, 1])

    with col1:
        joueur = st.text_input(label, value=st.session_state[f"text_{key}"], key=f"text_{key}")

    with col2:
        selection = st.selectbox(" ", ["Sélectionner"] + players, index=0, key=f"select_{key}")

    return selection if selection != "Sélectionner" else joueur

# Fonction pour calculer le classement
def calculer_classement():
    joueurs = {}
    victoires = {}

    for match in st.session_state.matchs:
        j1 = match['joueur1']
        j2 = match['joueur2']
        gagnant = match['vainqueur']
        scores = match['scores']

        for joueur in [j1, j2]:
            if joueur not in joueurs:
                joueurs[joueur] = {
                    'Nom du joueur': joueur,
                    'Points de victoire': 0,
                    'Matchs joués': 0,
                    'Points totaux': 0
                }

        joueurs[j1]['Matchs joués'] += 1
        joueurs[j2]['Matchs joués'] += 1

        for s in scores:
            score_j1, score_j2 = map(int, s.split('-'))
            joueurs[j1]['Points totaux'] += score_j1
            joueurs[j2]['Points totaux'] += score_j2

        key = tuple(sorted([j1, j2]))
        if key not in victoires:
            victoires[key] = {j1: 0, j2: 0}

        victoires[key][gagnant] += 1
        nb_victoires = victoires[key][gagnant]

        if nb_victoires == 1:
            joueurs[gagnant]['Points de victoire'] += 5
        elif nb_victoires == 2:
            joueurs[gagnant]['Points de victoire'] += 3
        else:
            joueurs[gagnant]['Points de victoire'] += 1

    classement = pd.DataFrame(joueurs.values())
    classement = classement.sort_values(
        by=['Points de victoire', 'Matchs joués'],
        ascending=[False, True]
    ).reset_index(drop=True)
    return classement

# Fonction pour déterminer le gagnant
def determiner_vainqueur(sets):
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

# ---- INTERFACE PRINCIPALE ----
st.title("🏸 Gestion de Tournoi de Badminton")

tab1, tab2 = st.tabs(["🏸 Tournoi", "📜 Historique"])

# --- Onglet 1 : Enregistrement + Classement ---
with tab1:
    st.subheader("1. Enregistrement d'un match")

    joueur1 = joueur_input("Joueur 1", "joueur1")
    joueur2 = joueur_input("Joueur 2", "joueur2")

    col1, col2, col3 = st.columns(3)
    with col1:
        set1 = st.text_input("Set 1 (ex: 21-15)", value=st.session_state["set1"], key="set1")
    with col2:
        set2 = st.text_input("Set 2 (ex: 19-21)", value=st.session_state["set2"], key="set2")
    with col3:
        set3 = st.text_input("Set 3 (ex: 21-19)", value=st.session_state["set3"], key="set3")

    if st.button("✅ Enregistrer le match"):
        sets = [s for s in [set1, set2, set3] if re.match(r'^\d{1,2}-\d{1,2}$', s)]
        if joueur1 and joueur2 and joueur1 != joueur2 and sets:
            vainqueur = determiner_vainqueur(sets)
            if vainqueur:
                st.session_state.matchs.append({
                    'joueur1': joueur1,
                    'joueur2': joueur2,
                    'scores': sets,
                    'vainqueur': vainqueur
                })
                st.success(f"Match enregistré ! Vainqueur : {vainqueur}")

                # 🔄 Réinitialisation des champs après l'enregistrement
                for key in ["text_joueur1", "select_joueur1", "text_joueur2", "select_joueur2", "set1", "set2", "set3"]:
                    st.session_state[key] = ""

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

# --- Onglet 2 : Historique des matchs ---
with tab2:
    st.subheader("📜 Historique des matchs")

    if st.session_state.matchs:
        selected_to_delete = []

        for i, match in enumerate(st.session_state.matchs):
            j1, j2 = match["joueur1"], match["joueur2"]

            col1, col2, col3 = st.columns([7, 2, 1])

            with col1:
                st.markdown(f"**{j1} vs {j2}** — Scores : {', '.join(match['scores'])} — **Vainqueur : {match['vainqueur']}**")

            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    del st.session_state.matchs[i]
                    st.rerun()

            with col3:
                if st.checkbox(" ", key=f"check_{i}"):
                    selected_to_delete.append(i)

        if selected_to_delete:
            if st.button("🗑️ Supprimer la sélection"):
                for index in sorted(selected_to_delete, reverse=True):
                    del st.session_state.matchs[index]
                st.success(f"{len(selected_to_delete)} match(s) supprimé(s)")
                st.rerun()

    else:
        st.info("Aucun match enregistré.")
