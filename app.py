if "GRAFICO POS 1" in tab_dict:
    with tab_dict["GRAFICO POS 1"]:
        st.subheader("📊 GRAFICO POSIÇÃO DOS MATERIAIS")

        opcao_graf = st.radio("SELEÇÃO:", ["1 - ID", "2 - TODOS"], horizontal=True, key="op_graf")

        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]

        if not lista:
            st.info("Sem estoque")
        else:
            if opcao_graf == "1 - ID":
                # GRAFICO POR ID
                id_graf=st.text_input("DIGITE A ID", key="id_graf", placeholder="Ex: 7 e aperte ENTER")
                if id_graf:
                    id_graf=id_graf.upper().strip()
                    lotes_id = [s for s in lista if s['ID']==id_graf]
                    lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
                    if not lotes_id:
                        st.error(f"ID {id_graf} sem estoque")
                    else:
                        pos1 = lotes_id[0]
                        st.markdown(f"## ⭐ ID {id_graf} - POS 1 AGORA")
                        st.markdown(f"# LOTE {pos1['LOTE']} - {pos1['SALDO']:,.0f}")
                        st.markdown(f"### {pos1['DESCRICAO']} - POSIÇÃO {pos1['ORDEM']}")

                        # Grafico POS 1 do ID
                        df_pos1=pd.DataFrame([pos1])
                        df_pos1['TEXTO']=f"LOTE {pos1['LOTE']} | {pos1['SALDO']:,.0f}"
                        df_pos1['LABEL']=f"ID {id_graf} - POS 1"
                        fig=px.bar(df_pos1, x='SALDO', y='LABEL', color='LOTE', text='TEXTO', orientation='h', title=f"ID {id_graf} - POS 1 - LOTE {pos1['LOTE']} - USAR AGORA")
                        fig.update_traces(textposition='outside', textfont=dict(size=20, color='black'))
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)

                        # Grafico FILA COMPLETA do ID
                        st.divider()
                        df_fila=pd.DataFrame(lotes_id)
                        df_fila['LABEL']=df_fila.apply(lambda r: f"POS {r['ORDEM']} - LOTE {r['LOTE']}", axis=1)
                        df_fila['TEXTO']=df_fila.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                        df_fila['COR']=df_fila.apply(lambda r: "⭐ POS 1" if r['ORDEM']==1 else f"POS {r['ORDEM']}", axis=1)

                        fig2=px.bar(df_fila, x='SALDO', y='LABEL', color='COR', text='TEXTO', orientation='h',
                                   title=f"ID {id_graf} - TODAS POSIÇÕES ORDINAIS - FILA FIFO",
                                   color_discrete_map={"⭐ POS 1":"green"})
                        fig2.update_traces(textposition='outside')
                        fig2.update_layout(height=350 + len(df_fila)*35)
                        st.plotly_chart(fig2, use_container_width=True)

                        st.dataframe(df_fila[['ORDEM','POSICAO','LOTE','DESCRICAO','MARCA','SALDO']].sort_values('ORDEM'), use_container_width=True, hide_index=True)
                else:
                    st.info("Digite a ID acima para ver o gráfico por ID")

            else: # 2 - TODOS
                st.markdown("### 📊 TODOS OS IDS - POSIÇÃO ATUAL")

                # Junta POS 1 de cada ID
                pos1_todos=[]
                filas_todas=[]
                for id_ in sorted(set([s['ID'] for s in lista])):
                    lotes_id = [s for s in lista if s['ID']==id_]
                    lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
                    if lotes_id:
                        pos1 = lotes_id[0]
                        pos1_todos.append(pos1)
                        # adiciona todos da fila com ID
                        for l in lotes_id:
                            filas_todas.append(l)

                if pos1_todos:
                    # GRAFICO 1: Só POS 1 de todos IDS
                    st.markdown("#### ⭐ POS 1 DE TODOS OS IDS - MATERIAL A USAR AGORA")
                    df_all_pos1=pd.DataFrame(pos1_todos)
                    df_all_pos1['LABEL']=df_all_pos1.apply(lambda r: f"ID {r['ID']} - LOTE {r['LOTE']}", axis=1)
                    df_all_pos1['TEXTO']=df_all_pos1.apply(lambda r: f"ID {r['ID']} LOTE {r['LOTE']} {r['SALDO']:,.0f}", axis=1)
                    df_all_pos1 = df_all_pos1.sort_values('ID')

                    fig_all=px.bar(df_all_pos1, x='SALDO', y='LABEL', color='ID', text='TEXTO', orientation='h',
                                  title="TODOS IDS - LOTE NA POS 1 - A USAR AGORA")
                    fig_all.update_traces(textposition='outside')
                    fig_all.update_layout(height=400 + len(df_all_pos1)*35)
                    st.plotly_chart(fig_all, use_container_width=True)

                    st.divider()
                    # GRAFICO 2: TODAS POSIÇÕES DE TODOS IDS
                    st.markdown("#### 📦 TODAS POSIÇÕES ORDINAIS - TODOS IDS - FILA COMPLETA")
                    df_todas=pd.DataFrame(filas_todas)
                    df_todas['LABEL']=df_todas.apply(lambda r: f"ID {r['ID']} POS {r['ORDEM']} LOTE {r['LOTE']}", axis=1)
                    df_todas['TEXTO']=df_todas.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                    df_todas['COR']=df_todas.apply(lambda r: "⭐ POS 1" if r['ORDEM']==1 else f"POS {r['ORDEM']}", axis=1)
                    df_todas = df_todas.sort_values(['ID','ORDEM'])

                    fig_todas=px.bar(df_todas, x='SALDO', y='LABEL', color='COR', text='TEXTO', orientation='h',
                                    title="TODOS IDS - TODAS POSIÇÕES ORDINAIS",
                                    color_discrete_map={"⭐ POS 1":"green"})
                    fig_todas.update_traces(textposition='outside')
                    fig_todas.update_layout(height=500 + len(df_todas)*30, showlegend=True)
                    st.plotly_chart(fig_todas, use_container_width=True)

                    st.dataframe(df_todas[['ID','ORDEM','POSICAO','LOTE','DESCRICAO','SALDO']].sort_values(['ID','ORDEM']), use_container_width=True, height=500, hide_index=True)
