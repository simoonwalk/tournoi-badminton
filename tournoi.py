import streamlit as st
import pandas as pd
import re

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
                    'Jeux marqués': 0
                }

        joueurs[j1]['Matchs joués'] += 1
        joueurs[j2]['Matchs joués'] += 1

        for s in scores:
            score_j1, score_j2 = map(int, s.split('-'))
            joueurs[j1]['Jeux marqués'] += score_j1
            joueurs[j2]['Jeux marqués'] += score_j2

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

# Section 1 : Enregistrement de match
st.title("🏸 Gestion de Tournoi de Badminton")

st.header("1. Enregistrement d'un match")

players = get_all_players()
# Suggestions basées sur les joueurs connus
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

# Section 2 : Classement dynamique
st.header("2. Classement des joueurs")

if st.session_state.matchs:
    classement_df = calculer_classement()
    st.dataframe(classement_df)
else:
    st.info("Aucun match enregistré pour le moment.")

# Section 3 : Historique des matchs
st.header("3. Historique des matchs")

if st.session_state.matchs:
    for i, match in enumerate(st.session_state.matchs):
        with st.expander(f"{match['joueur1']} vs {match['joueur2']}"):
            st.write("**Scores :**", ", ".join(match['scores']))
            st.write("**Vainqueur :**", match['vainqueur'])
            if st.button("🗑️ Supprimer ce match", key=f"del_{i}"):
                st.session_state.matchs.pop(i)
                st.experimental_rerun()
else:
    st.info("Aucun match enregistré.")
