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

# --- INTERFACE STREAMLIT ---
st.title("🏸 Tournoi de Badminton")
tab1, tab2 = st.tabs(["🏸 Tournoi", "📜 Historique"])

# --- Ton interface existante reste inchangée (fonctions joueur_input, set_input, determiner_vainqueur...) ---
# Ici pour alléger, tu reprends tes fonctions existantes directement depuis ton ancien fichier.

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
                nouveau_match = {
                    'joueur1': joueur1,
                    'joueur2': joueur2,
                    'scores': sets,
                    'vainqueur': vainqueur
                }
                sauvegarder_match(nouveau_match)
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
        for match in st.session_state.matchs:
            with st.container():
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.markdown(f"**{match['joueur1']} vs {match['joueur2']}** - Vainqueur : {match['vainqueur']}")
                    st.markdown(f"**Scores :** {', '.join(match['scores'])}")
                with col2:
                    if st.button("🗑️", key=f"del_{match['id']}"):
                        supprimer_match(match['id'])
                        st.session_state.matchs = charger_matchs()
                        st.rerun()

        st.markdown("---")
        if st.button("♻️ Réinitialiser tous les matchs"):
            reinitialiser_matchs()
            st.session_state.matchs = []
            st.success("Tous les matchs ont été réinitialisés.")
            st.rerun()
    else:
        st.info("Aucun match enregistré.")
