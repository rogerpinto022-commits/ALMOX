with tab_cad:
    st.header("3 - CADASTRO DE MATERIAIS - SELECIONE LOCAIS - AUTO PREENCHE ID")
    
    # AUTO PREENCHIMENTO AO DIGITAR ID
    id_in = st.text_input("DIGITE ID DO MATERIAL* - AO DIGITAR AUTO PREENCHE DESCRICAO E MARCA SE JA EXISTIR", key="id_cad_auto")
    
    desc_auto = ""
    marca_auto = ""
    qtd_auto = 1250.0
    encontrou = False
    
    if id_in:
        id_in_upper = id_in.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip() == id_in_upper:
                desc_auto = r.get('DESCRICAO','')
                marca_auto = r.get('MARCA','')
                qtd_auto = safe_float(r.get('QTD_PALETE',1250.0), 1250.0)
                encontrou = True
                break
        if encontrou:
            st.success(f"ID {id_in_upper} ENCONTRADO - Auto preenchido: {desc_auto} - {marca_auto} - {qtd_auto} UN/PAL")
        else:
            st.info(f"ID {id_in_upper} NOVO - Cadastre descricao e marca")
    
    with st.form("form_cadastro_mat"):
        # Campos ja com auto preenchimento
        st.text_input("ID CONFIRMADO*", value=id_in.upper() if id_in else "", disabled=True, key="id_confirm")
        desc_in=st.text_input("DESCRICAO DO REFRATARIO* - AUTO PREENCHE AO DIGITAR ID", value=desc_auto, key="desc_cad")
        marca_in=st.text_input("MARCA / FABRICANTE* - AUTO PREENCHE AO DIGITAR ID", value=marca_auto, key="marca_cad")
        lote_in=st.text_input("LOTE INICIAL OPCIONAL", key="lote_cad")
        locais_sel=st.multiselect("SELECIONE EM QUAIS LOCAIS CADASTRAR* (PODE MARCAR VARIOS)", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad")
        qtd_in=st.number_input("QTD UNIDADES POR PALETE - AUTO PREENCHE SE ID JA EXISTE", value=qtd_auto, key="qtd_cad")
        ent_in=st.number_input("PALETES POR LOCAL - 0=SO CADASTRO BASE", value=0.0, key="ent_cad")
        
        if st.form_submit_button("CADASTRAR NOS LOCAIS SELECIONADOS", type="primary"):
            if not id_in or not desc_in or not marca_in:
                st.error("Preencha ID, DESCRICAO e MARCA - Digite ID acima para auto preencher")
            elif not locais_sel:
                st.error("Selecione pelo menos 1 LOCAL")
            else:
                for local_cad in locais_sel:
                    total=qtd_in*ent_in
                    st.session_state.cad.append({
                        "ID":id_in.upper(),
                        "DESCRICAO":desc_in.upper(),
                        "MARCA":marca_in.upper(),
                        "LOTE":lote_in.upper(),
                        "QTD_PALETE":qtd_in,
                        "ENTRADA":ent_in,
                        "TOTAL":total,
                        "LOCAL":local_cad,
                        "FABRICACAO":date.today().strftime("%d/%m/%Y")
                    })
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.success(f"Material {id_in.upper()} - {desc_in} cadastrado em {len(locais_sel)} local(is): {', '.join(locais_sel)} com {ent_in} paletes em cada")
                st.rerun()
    
    st.divider()
    st.write("Materiais cadastrados por local:")
    filtro_cad = st.text_input("FILTRAR CADASTRO POR ID/DESCRICAO", key="filtro_cad_lista")
    for i,r in enumerate(st.session_state.cad):
        if filtro_cad and filtro_cad.upper() not in str(r.get('ID','')).upper() and filtro_cad.upper() not in str(r.get('DESCRICAO','')).upper():
            continue
        c1,c2=st.columns([4,1])
        with c1: 
            st.write(f"**LOCAL: {r.get('LOCAL')}** | ID {r.get('ID')} - {r.get('DESCRICAO')} - MARCA {r.get('MARCA')} - LOTE {r.get('LOTE')} - {r.get('QTD_PALETE')} UN/PAL - {r.get('ENTRADA')} PAL")
        with c2:
            if st.button("Excluir", key=f"del_cad_{i}"):
                st.session_state.cad.pop(i)
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.rerun()
