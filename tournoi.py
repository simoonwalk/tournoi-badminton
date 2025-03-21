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

# Fonction pour extraire les joueurs existants
def get_all_players():
    players = set()
    for match in st.session_state.matchs:
        players.add(match['joueur1'])
        players.add(match['joueur2'])
    return sorted(players)

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

        perdant = j2 if gagnant == j1 else j1

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

    players = get_all_players()

    joueur1 = st.text_input("Joueur 1", placeholder="Nom du joueur 1")
    if joueur1 and players:
        suggestions1 = [p for p in players if joueur1.lower() in p.lower() and p.lower() != joueur1.lower()]
        if suggestions1:
            st.caption(f"Suggestions : {', '.join(suggestions1)}")

    joueur2 = st.text_input("Joueur 2", placeholder="Nom du joueur 2")
    if joueur2 and players:
        suggestions2 = [p for p in players if joueur2.lower() in p.lower() and p.lower() != joueur2.lower()]
        if suggestions2:
            st.caption(f"Suggestions : {', '.join(suggestions2)}")

    col1, col2, col3 = st.columns(3)
    with col1:
        set1 = st.text_input("Set 1 (ex: 21-15)", key="set1")
    with col2:
        set2 = st.text_input("Set 2 (ex: 19-21)", key="set2")
    with col3:
        set3 = st.text_input("Set 3 (ex: 21-19)", key="set3")

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
    st.subheader("Historique des matchs")

    if st.session_state.matchs:
        matches = st.session_state.matchs

        # Pour gestion des suppressions groupées
        selected = []

        # Dictionnaire pour compter les rencontres entre deux joueurs
        rencontre_compteur = {}

        for i, match in enumerate(matches):
            j1 = match["joueur1"]
            j2 = match["joueur2"]
            key = tuple(sorted([j1, j2]))

            if key not in rencontre_compteur:
                rencontre_compteur[key] = 1
            else:
                rencontre_compteur[key] += 1

            num_rencontre = rencontre_compteur[key]

            col1, col2, col3, col4 = st.columns([4, 3, 3, 1])
            with col1:
                st.markdown(f"**{j1} vs {j2}** — *{num_rencontre}ᵉ rencontre*")
            with col2:
                st.markdown("**Scores :** " + ", ".join(match["scores"]))
            with col3:
                st.markdown(f"**Vainqueur :** {match['vainqueur']}")
            with col4:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.match_to_delete = i
                    st.session_state.just_deleted = True
                    break  # Sortir de la boucle pour éviter conflit state

            # Checkbox pour suppression groupée
            selected.append(st.checkbox("Sélectionner", key=f"check_{i}"))

        # Bouton pour supprimer en masse
        if any(selected):
            indices_to_delete = [i for i, checked in enumerate(selected) if checked]
            if st.button("🗑️ Supprimer la sélection"):
                for index in sorted(indices_to_delete, reverse=True):
                    del st.session_state.matchs[index]
                st.success(f"{len(indices_to_delete)} match(s) supprimé(s)")
                st.rerun()

        # Suppression unique en fin de boucle
        if st.session_state.just_deleted and st.session_state.match_to_delete is not None:
            del st.session_state.matchs[st.session_state.match_to_delete]
            st.session_state.match_to_delete = None
            st.session_state.just_deleted = False
            st.rerun()

    else:
        st.info("Aucun match enregistré.")
