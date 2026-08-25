with tab1:
    st.subheader("🔒 Backup - Seus dados já lançados estão salvos")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if os.path.exists(ARQ_DADOS):
            with open(ARQ_DADOS, "rb") as f:
                st.download_button("⬇️ BAIXAR BACKUP ESTOQUE (dados.csv)", f, file_name="backup_dados.csv")
    with col_b2:
        if os.path.exists(ARQ_MOV):
            with open(ARQ_MOV, "rb") as f:
                st.download_button("⬇️ BAIXAR BACKUP LANÇAMENTOS (mov.csv)", f, file_name="backup_mov.csv")
    st.divider()
    # ... resto do seu código de estoque
