st.title("🏸 Gestion de Tournoi de Badminton")

tab_tournoi, tab_historique = st.tabs(["🏸 Tournoi", "📜 Historique"])

# --- Onglet 1 : Enregistrement + Classement ---
with tab_tournoi:
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

# --- Onglet 2 : Historique uniquement ---
with tab_historique:
    st.subheader("Historique des matchs")
    if st.session_state.matchs:
        for i, match in enumerate(st.session_state.matchs):
            with st.expander(f"{match['joueur1']} vs {match['joueur2']}"):
                st.write("**Scores :**", ", ".join(match['scores']))
                st.write("**Vainqueur :**", match['vainqueur'])
                if st.button("🗑️ Supprimer ce match", key=f"del_{i}"):
                    st.session_state.match_to_delete = i
                    st.session_state.just_deleted = True
                    break

        if st.session_state.just_deleted and st.session_state.match_to_delete is not None:
            del st.session_state.matchs[st.session_state.match_to_delete]
            st.session_state.match_to_delete = None
            st.session_state.just_deleted = False
            st.rerun()
    else:
        st.info("Aucun match enregistré.")
