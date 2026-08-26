with tab5:
    st.markdown("### 📈 GRAFICOS - ATUALIZADO EM TEMPO REAL - GALPÃO vs OFICINA")
    if not st.session_state.get('lista_cadastro'):
        st.warning("Sem dados")
    else:
        saldos=get_saldos_completos()
        if not saldos:
            st.warning("Sem saldo")
        else:
            lista=[]
            for chave,d in saldos.items():
                lista.append({
                    "LOTE": str(d.get('LOTE_ORIG')),
                    "DESCRICAO": f"ID {d.get('ID','?')} - {str(d.get('DESCRICAO','SEM DESC'))[:20]}",
                    "ID": str(d.get('ID','?')),
                    "LOCAL": str(d.get('LOCAL')),
                    "VALIDO_ATE": str(d.get('VALIDO_ATE','00/00/0000')),
                    "UNIDADE": str(d.get('UNIDADE','KG')),
                    "SALDO_QTD": safe_float(d.get('SALDO_QTD',0)),
                    "SALDO_PAL": safe_float(d.get('SALDO_PALETES',0)),
                    "TEXTO_QTD": f"{safe_float(d.get('SALDO_QTD',0)):,.0f} {str(d.get('UNIDADE','KG'))}",
                    "TEXTO_PAL": f"{safe_float(d.get('SALDO_PALETES',0)):.1f} PAL"
                })
            df=pd.DataFrame(lista)
            df=df[df["SALDO_QTD"]>0]

            if df.empty:
                st.info("Sem saldo positivo para grafico")
            else:
                # METRICAS BEM VISIVEIS
                col1,col2,col3,col4 = st.columns(4)
                total_geral_qtd = df["SALDO_QTD"].sum()
                total_geral_pal = df["SALDO_PAL"].sum()
                total_galpao = df[df["LOCAL"]==LOCAL_GALPAO]["SALDO_QTD"].sum()
                total_oficina = df[df["LOCAL"]==LOCAL_OFICINA]["SALDO_QTD"].sum()
                col1.metric("TOTAL GERAL QTD", f"{total_geral_qtd:,.0f}")
                col2.metric("TOTAL GERAL PAL", f"{total_geral_pal:.1f} PAL")
                col3.metric("GALPÃO", f"{total_galpao:,.0f}")
                col4.metric("OFICINA", f"{total_oficina:,.0f}")

                # GRAFICO 1 - POR DESCRIÇÃO - COM VALOR EM CIMA
                fig1=px.bar(df, x='DESCRICAO', y='SALDO_QTD', color='LOCAL', barmode="group", 
                           text='TEXTO_QTD', title="SALDO QTD POR PRODUTO - GALPÃO vs OFICINA")
                fig1.update_traces(textposition='outside', textfont_size=14, textfont_family="Arial Black", textfont_color="black")
                fig1.update_layout(font=dict(size=14, family="Arial Black"), height=600, plot_bgcolor='#A8C5A2', title_font_size=20)
                st.plotly_chart(fig1, use_container_width=True, key="graf1")

                c1,c2=st.columns(2)
                with c1:
                    # GRAFICO 2 - PALETES
                    fig2=px.bar(df, x='LOTE', y='SALDO_PAL', color='LOCAL', text='TEXTO_PAL', 
                               title="SALDO EM PALETES POR LOTE")
                    fig2.update_traces(textposition='outside', textfont_size=16, textfont_family="Arial Black")
                    fig2.update_layout(font=dict(size=12, family="Arial Black"), height=500, plot_bgcolor='#E2E2E2')
                    st.plotly_chart(fig2, use_container_width=True, key="graf2")
                with c2:
                    # GRAFICO 3 - PIZZA POR LOCAL
                    df_pizza = df.groupby("LOCAL")[["SALDO_QTD"]].sum().reset_index()
                    fig_pizza = px.pie(df_pizza, values='SALDO_QTD', names='LOCAL', title="DISTRIBUIÇÃO GALPÃO vs OFICINA",
                                       hole=0.3)
                    fig_pizza.update_traces(textinfo='value+percent', textfont_size=18, textfont_family="Arial Black")
                    fig_pizza.update_layout(height=500)
                    st.plotly_chart(fig_pizza, use_container_width=True, key="graf_pizza")

                # GRAFICO 4 - LOTE A LOTE COM VALIDADE E TUDO VISIVEL
                df_sorted = df.sort_values(by="VALIDO_ATE")
                fig3=px.bar(df_sorted, x='LOTE', y='SALDO_QTD', color='LOCAL', barmode="group", 
                           text='TEXTO_QTD', hover_data=["DESCRICAO","VALIDO_ATE","UNIDADE","SALDO_PAL"],
                           title="SALDO QTD POR LOTE - TOTAL GERAL = GALPÃO + OFICINA - COM VALIDADE")
                fig3.update_traces(textposition='outside', textfont_size=13, textfont_family="Arial Black")
                fig3.update_layout(font=dict(size=12, family="Arial Black"), height=700, plot_bgcolor='#A8C5A2', xaxis_tickangle=-45)
                st.plotly_chart(fig3, use_container_width=True, key="graf3")

                # TABELA BEM VISIVEL
                st.markdown("#### 📋 TABELA DE SALDOS ATUALIZADA")
                st.dataframe(df[["LOTE","ID","DESCRICAO","LOCAL","VALIDO_ATE","UNIDADE","SALDO_PAL","SALDO_QTD"]].sort_values(by="SALDO_QTD", ascending=False), use_container_width=True, height=600)
