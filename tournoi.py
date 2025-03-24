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
        for joueur in [match['joueur1'], match['joueur2']]:
            if joueur not in joueurs:
                joueurs[joueur] = {'Nom': joueur, 'Points': 0, 'Matchs': 0, 'Total': 0}

        joueurs[match['vainqueur']]['Points'] += 3
        joueurs[match['joueur1']]['Matchs'] += 1
        joueurs[match['joueur2']]['Matchs'] += 1

        for set_score in match['scores']:
            s1, s2 = map(int, set_score.split('-'))
            joueurs[match['joueur1']]['Total'] += s1
            joueurs[match['joueur2']]['Total'] += s2

    classement = pd.DataFrame(joueurs.values()).sort_values(by=['Points', 'Total'], ascending=[False, False])
    classement.index += 1
    classement.insert(0, "Rang", [medal(i) for i in classement.index])
    return classement

def medal(rank):
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}ᵉ")

# --- INTERFACE STREAMLIT ---
st.title("🏸 Tournoi de Badminton")
tab1, tab2 = st.tabs(["🏸 Tournoi", "📜 Historique"])

# --- Ton interface reste inchangée (suite de ton code précédent) ---
# (le reste du code précédent Streamlit demeure identique ici)

# --- Style CSS personnalisé ---
st.markdown("""
    <style>
    .stElementToolbar {
        display:none!important;
    }
        /* --- Mise en page compacte --- */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    .stMarkdown, .stTextInput, .stNumberInput, .stSelectbox {
        margin-bottom: 0.25rem !important;
    }

    html, body, [class*="st-"] {
        font-size: 15px;
    }

    h1, h2, h3 {
        font-size: 1.3em !important;
        margin-bottom: 0.2em;
    }

    button[kind="primary"] {
        padding: 0.3rem 1rem;
        font-size: 14px;
    }

    .stColumns {
        gap: 0.5rem !important;
    }

    /* --- Cacher éléments natifs Streamlit --- */
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }

    /* --- Masquer le footer même sur Streamlit Cloud --- */
    footer { visibility: hidden; }
    .st-emotion-cache-1v0mbdj { display: none !important; }
    .st-emotion-cache-1dp5vir, .st-emotion-cache-q8sbsg { display: none !important; }
    [data-testid="stFooter"] { display: none !important; }

    /* Cacher toute balise contenant “streamlit” dans le texte */
    div:has(> a[href*="streamlit.io"]) {
        display: none !important;
    }
    .block-container {
    padding-top: 1rem;
    padding-bottom: 5rem; /* <- Ajout ici */
}
    </style>
""", unsafe_allow_html=True)

# --- Initialisation ---
if 'matchs' not in st.session_state:
    st.session_state.matchs = []

if 'reset_pending' not in st.session_state:
    st.session_state.reset_pending = False

# --- Extraction des joueurs existants ---
def get_all_players():
    players = set()
    for match in st.session_state.matchs:
        players.add(match['joueur1'])
        players.add(match['joueur2'])
    return sorted(players)

# --- Champ de saisie hybride (dropdown + texte) ---
def joueur_input(label, key):
    players = get_all_players()
    options = ["Sélectionner"] + players

    col1, col2 = st.columns([1, 2.5])
    with col1:
        selection = st.selectbox(
            " ",
            options,
            key=f"select_{key}",
            index=0 if st.session_state.reset_pending else options.index(
                st.session_state.get(f"select_{key}", "Sélectionner")
            ) if st.session_state.get(f"select_{key}") in options else 0
        )
    with col2:
        joueur = st.text_input(
            label,
            key=f"text_{key}",
            value="" if st.session_state.reset_pending else st.session_state.get(f"text_{key}", "")
        )

    return selection if selection != "Sélectionner" else joueur

# --- Saisie des scores set par set ---
def set_input(set_num, joueur1, joueur2):
    st.markdown(f"**🏸 Set {set_num}**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{joueur1 or 'Joueur 1'}**")
        s1 = st.number_input(
            f"Set {set_num} - {joueur1 or 'Joueur 1'}",
            min_value=0, max_value=30, step=1,
            key=f"set{set_num}_j1",
            label_visibility="collapsed"
        )
    with col2:
        st.markdown(f"**{joueur2 or 'Joueur 2'}**")
        s2 = st.number_input(
            f"Set {set_num} - {joueur2 or 'Joueur 2'}",
            min_value=0, max_value=30, step=1,
            key=f"set{set_num}_j2",
            label_visibility="collapsed"
        )
    return f"{s1}-{s2}" if (s1 != 0 or s2 != 0) else ""

# --- Calcul du classement ---
def calculer_classement():
    from collections import defaultdict
    joueurs = defaultdict(lambda: {
        'Nom du joueur': "",
        'Points de victoire': 0,
        'Matchs joués': 0,
        'Points totaux': 0
    })
    victoires = {}

    for match in st.session_state.matchs:
        j1 = match['joueur1']
        j2 = match['joueur2']
        gagnant = match['vainqueur']
        scores = match['scores']

        joueurs[j1]['Nom du joueur'] = j1
        joueurs[j2]['Nom du joueur'] = j2

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
        by=['Points de victoire', 'Matchs joués', 'Points totaux'],
        ascending=[False, True, False]
    ).reset_index(drop=True)

    classement.index += 1
    classement.insert(0, "Rang", [medal(i) for i in classement.index])
    return classement

def medal(rank):
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}ᵉ")

# --- Déterminer le vainqueur ---
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

# --- INTERFACE ---
st.title("🏸 Tournoi de Badminton")

tab1, tab2 = st.tabs(["🏸 Tournoi", "📜 Historique"])

# --- Onglet 1 ---
with tab1:
    st.subheader("1. Enregistrement d'un match")

    joueur1 = joueur_input("Joueur 1", "joueur1")
    joueur2 = joueur_input("Joueur 2", "joueur2")

    st.markdown("**🎯 Résultats des sets :**")
    set1 = set_input(1, joueur1, joueur2)
    set2 = set_input(2, joueur1, joueur2)
    set3 = set_input(3, joueur1, joueur2)

    if st.session_state.reset_pending:
        st.session_state.reset_pending = False

    if st.button("✅ Enregistrer le match"):
        sets = [s for s in [set1, set2, set3] if re.match(r'^\d{1,2}-\d{1,2}$', s)]
        if joueur1 and joueur2 and joueur1 != joueur2 and sets:
            vainqueur = determiner_vainqueur(sets, joueur1, joueur2)
            if vainqueur:
                st.session_state.matchs.append({
                    'joueur1': joueur1,
                    'joueur2': joueur2,
                    'scores': sets,
                    'vainqueur': vainqueur
                })
                st.success(f"Match enregistré ! Vainqueur : {vainqueur}")
                st.session_state.reset_pending = True
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

# --- Onglet 2 ---
with tab2:
    st.subheader("📜 Historique des matchs")

    if st.session_state.matchs:
        rencontre_compteur = {}
        selected_to_delete = []

        for i, match in enumerate(st.session_state.matchs):
            j1, j2 = match["joueur1"], match["joueur2"]
            key = tuple(sorted([j1, j2]))
            rencontre_compteur[key] = rencontre_compteur.get(key, 0) + 1

            with st.container():
                col1, col2, col3 = st.columns([7, 2, 1])
                with col1:
                    st.markdown(f"**{j1} vs {j2}** — {rencontre_compteur[key]}ᵉ rencontre")
                    st.markdown(f"**Scores :** {', '.join(match['scores'])} — **Vainqueur : {match['vainqueur']}**")
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

        st.markdown("---")
        if st.button("♻️ Réinitialiser tous les matchs"):
            st.session_state.matchs.clear()
            st.success("Tous les matchs ont été réinitialisés.")
            st.rerun()
    else:
        st.info("Aucun match enregistré.")
