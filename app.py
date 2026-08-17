import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(page_title="Sistema ALMOX - Controle de Estoque", layout="wide", page_icon="🏭")

st.markdown("""
    <style>
   .main-title { font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
   .subtitle { font-size: 1.1rem; color: #4B5563; margin-bottom: 25px; }
   .card-alerta { background-color: #FEE2E2; padding: 15px; border-radius: 8px; border-left: 5px solid #EF4444; font-weight: bold; color: #991B1B; }
    </style>""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏭 Sistema de Controle de Estoque - ALMOX V2</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Módulos avançados: Edição de histórico, cadastro completo e rastreamento de saldo real.</div>', unsafe_allow_html=True)

if 'df_estoque' not in st.session_state:
    dados_iniciais = [
        {"ID": 1, "DESCRIÇÃO": "CIMENTO", "MARCA": "FONDU", "LOTE": "9999999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1250, "TOTAL": 13750, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 1, "DESCRIÇÃO": "CIMENTO", "MARCA": "FONDU", "LOTE": "9999999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 200, "TOTAL": 200, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 2, "DESCRIÇÃO": "CARBETO DE SILICIO", "MARCA": "SHINAGAWA", "LOTE": "9999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1000, "TOTAL": 5000, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 3, "DESCRIÇÃO": "ARGAMASSA REFRATARIA", "MARCA": "CABOFRAX", "LOTE": "221027970", "VALIDADE": "07/05/2023", "QTD/PALETE": 1, "TOTAL": 1, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 3, "DESCRIÇÃO": "ARGAMASSA REFRATARIA", "MARCA": "CABOFRAX", "LOTE": "231000196", "VALIDADE": "02/07/2023", "QTD/PALETE": 1, "TOTAL": 1, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 4, "DESCRIÇÃO": "PLACIBAR SG", "MARCA": "IBAR", "LOTE": "9999999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1000, "TOTAL": 15000, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 5, "DESCRIÇÃO": "CONCRETO CASTIBAR PSI UG", "MARCA": "IBAR", "LOTE": "9999999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1250, "TOTAL": 5000, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 5, "DESCRIÇÃO": "LÃ DE ROCHA", "MARCA": "BIOLÃ", "LOTE": "9999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1, "TOTAL": 103, "UNIDADE DE MEDIDA": "PACOTES"},
        {"ID": 6, "DESCRIÇÃO": "TIJOLO SEMI ISOLANTE SUPRA", "MARCA": "SKAMOL ALUPOR", "LOTE": "9999999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 912, "TOTAL": 9120, "UNIDADE DE MEDIDA": "UNIDADES"},
        {"ID": 7, "DESCRIÇÃO": "TIJOLO ISOLANTE AB70", "MARCA": "MOSCONI AB70", "LOTE": "9999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1020, "TOTAL": 31620, "UNIDADE DE MEDIDA": "UNIDADES"},
        {"ID": 7, "DESCRIÇÃO": "TIJOLO ISOLANTE", "MARCA": "SKAMOL ALUPOR", "LOTE": "9999", "VALIDADE": "00/00/0000", "QTD/PALETE": 912, "TOTAL": 128592, "UNIDADE DE MEDIDA": "UNIDADES"},
        {"ID": 8, "DESCRIÇÃO": "TIJOLO REFRATARIO", "MARCA": "IBAR SA ALUM", "LOTE": "9999999999", "VALIDADE": "00/00/0000", "QTD/PALETE": 512, "TOTAL": 160256, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 9, "DESCRIÇÃO": "GAXETAS", "MARCA": "CRD", "LOTE": "9999", "VALIDADE": "00/00/0000", "QTD/PALETE": 0, "TOTAL": 0, "UNIDADE DE MEDIDA": "ROLOS"},
        {"ID": 11, "DESCRIÇÃO": "CHAMOTE", "MARCA": "IBAR", "LOTE": "9999", "VALIDADE": "00/00/0000", "QTD/PALETE": 1000, "TOTAL": 15000, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 12, "DESCRIÇÃO": "PASTA FRIA", "MARCA": "ELKEN", "LOTE": "75074_75075", "VALIDADE": "00/00/0000", "QTD/PALETE": 1000, "TOTAL": 4000, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 14, "DESCRIÇÃO": "BLOCO LATERAL M", "MARCA": "CARBON", "LOTE": "9999", "VALIDADE": "00/00/0000", "QTD/PALETE": 27, "TOTAL": 2484, "UNIDADE DE MEDIDA": "KILOS"},
        {"ID": 15, "DESCRIÇÃO": "BLOCO DE FUNDO", "MARCA": "TOKAY", "LOTE": "25/05/2026", "VALIDADE": "25/05/2026", "QTD/PALETE": 1, "TOTAL": 2, "UNIDADE DE MEDIDA": "UNIDADES"}
    ]
    df_criado = pd.DataFrame(dados_iniciais)
    df_criado['CHAVE_INTERNA'] = range(len(df_criado))
    st.session_state.df_estoque = df_criado

if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=["Mov_ID", "Data/Hora", "CHAVE_INTERNA", "Item", "Tipo", "Quantidade", "Responsável"])

aba_operacoes, aba_edicao, aba_alertas, aba_novo = st.tabs(["📊 Painel & Estoque Atual", "✏️ Editar Entradas/Saídas", "⚠️ Alertas Críticos", "➕ Cadastrar Novo Item"])

with aba_operacoes:
    df_atual = st.session_state.df_estoque.copy()
    c_filtro1, c_filtro2 = st.columns(2)
    with c_filtro1:
        busca_inicial = st.text_input("🔍 Rastrear pela Inicial do Produto:", "").strip().upper()
        if busca_inicial:
            df_atual = df_atual[df_atual['DESCRIÇÃO'].astype(str).str.startswith(busca_inicial)]
    with c_filtro2:
        lista_materiais = sorted(df_atual['DESCRIÇÃO'].unique())
        material_selecionado = st.selectbox("🎯 Filtrar por Material Específico:", ["Todos os Materiais"] + lista_materiais)
        if material_selecionado!= "Todos os Materiais":
            df_atual = df_atual[df_atual['DESCRIÇÃO'] == material_selecionado]

    st.markdown("### 📦 Posição de Estoque Atual")
    st.dataframe(df_atual.drop(columns=['CHAVE_INTERNA']), use_container_width=True, hide_index=True)
    st.markdown("---")
    col_lancamento, col_grafico = st.columns([1, 1.2])

    with col_lancamento:
        st.subheader("🔄 Registrar Nova Movimentação")
        with st.form("form_movimentacao", clear_on_submit=True):
            opcoes_produtos = {linha['CHAVE_INTERNA']: f"ID {linha['ID']} | {linha['DESCRIÇÃO']} (Marca: {linha['MARCA']} | Lote: {linha['LOTE']})" for _, linha in st.session_state.df_estoque.iterrows()}
            chave_selecionada = st.selectbox("Selecione o produto/lote exato:", options=list(opcoes_produtos.keys()), format_func=lambda x: opcoes_produtos[x])
            tipo_mov = st.radio("Tipo de Operação:", ["Entrada de Material", "Saída (Consumo)"], horizontal=True)
            qtd_mov = st.number_input("Quantidade Operada:", min_value=1, step=1, value=1)
            resp = st.text_input("Responsável pela Operação:", "Almoxarifado")
            confirmar = st.form_submit_button("Confirmar Operação")

            if confirmar:
                idx_sistema = st.session_state.df_estoque[st.session_state.df_estoque['CHAVE_INTERNA'] == chave_selecionada].index
                estoque_atual = int(st.session_state.df_estoque.loc[idx_sistema, 'TOTAL'].values[0])
                nome_prod = str(st.session_state.df_estoque.loc[idx_sistema, 'DESCRIÇÃO'].values[0])
                operacao_valida = False

                if "Entrada" in tipo_mov:
                    novo_total = estoque_atual + qtd_mov
                    st.session_state.df_estoque.loc[idx_sistema, 'TOTAL'] = novo_total
                    st.success(f"Estoque atualizado! Novo saldo de {nome_prod}: {novo_total}")
                    operacao_valida = True
                    tipo_hist = "Entrada"
                else:
                    if estoque_atual >= qtd_mov:
                        novo_total = estoque_atual - qtd_mov
                        st.session_state.df_estoque.loc[idx_sistema, 'TOTAL'] = novo_total
                        st.success(f"Estoque atualizado! Novo saldo de {nome_prod}: {novo_total}")
                        operacao_valida = True
                        tipo_hist = "Saída"
                    else:
                        st.error(f"Erro: Saldo insuficiente! Estoque atual é de {estoque_atual}.")

                if operacao_valida:
                    mov_id = int(st.session_state.historico["Mov_ID"].max() + 1) if not st.session_state.historico.empty else 1
                    novo_registro = pd.DataFrame([{"Mov_ID": mov_id, "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), "CHAVE_INTERNA": chave_selecionada, "Item": nome_prod, "Tipo": tipo_hist, "Quantidade": qtd_mov, "Responsável": resp}])
                    st.session_state.historico = pd.concat([st.session_state.historico, novo_registro], ignore_index=True)
                    st.rerun()

    with col_grafico:
        st.subheader("📊 Gráfico de Consumo Consolidado")
        if not st.session_state.historico.empty:
            df_agrupado = st.session_state.historico.groupby(["Item", "Tipo"], as_index=False)["Quantidade"].sum()
            fig = px.bar(df_agrupado, x="Item", y="Quantidade", color="Tipo", barmode="group", color_discrete_map={"Entrada": "#10B981", "Saída": "#EF4444"}, labels={"Quantidade": "Volume Acumulado", "Item": "Material"})
            fig.update_layout(height=290, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma movimentação ou consumo registrado até o momento.")

with aba_edicao:
    st.subheader("✏️ Painel de Ajuste e Exclusão de Movimentações")
    if not st.session_state.historico.empty:
        opcoes_historico = {linha['Mov_ID']: f"Reg #{linha['Mov_ID']} | {linha['Data/Hora']} - {linha['Item']} ({linha['Tipo']}: {linha['Quantidade']})" for _, linha in st.session_state.historico.iterrows()}
        mov_selecionada = st.selectbox("Escolha o registro para modificar:", options=list(opcoes_historico.keys()), format_func=lambda x: opcoes_historico[x])
        df_filtrado = st.session_state.historico[st.session_state.historico['Mov_ID'] == mov_selecionada]

        if not df_filtrado.empty: # TUDO AQUI DENTRO AGORA
            linha_hist = df_filtrado.index
            chave_prod = int(df_filtrado['CHAVE_INTERNA'].values[0])
            tipo_atual = str(df_filtrado['Tipo'].values[0])
            qtd_atual = int(df_filtrado['Quantidade'].values[0])
            resp_atual = str(df_filtrado['Responsável'].values[0])

            c_ed1, c_ed2 = st.columns(2)
            with c_ed1:
                nova_qtd = st.number_input("Alterar Quantidade para:", min_value=1, value=qtd_atual, step=1)
            with c_ed2:
                novo_resp = st.text_input("Alterar Responsável para:", value=resp_atual)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Salvar Alterações de Quantidade"):
                    idx_est = st.session_state.df_estoque[st.session_state.df_estoque['CHAVE_INTERNA'] == chave_prod].index
                    est_atual = int(st.session_state.df_estoque.loc[idx_est, 'TOTAL'].values[0])
                    if tipo_atual == "Entrada":
                        est_recalculado = est_atual - qtd_atual + nova_qtd
                    else:
                        est_recalculado = est_atual + qtd_atual - nova_qtd
                    if est_recalculado >= 0:
                        st.session_state.df_estoque.loc[idx_est, 'TOTAL'] = est_recalculado
                        st.session_state.historico.loc[linha_hist, 'Quantidade'] = nova_qtd
                        st.session_state.historico.loc[linha_hist, 'Responsável'] = novo_resp
                        st.success("Lançamento e Estoque Atual atualizados com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro crítico: A alteração causaria estoque negativo para este material.")
            with col_btn2:
                if st.button("🗑️ Excluir e Estornar Registro"):
                    idx_est = st.session_state.df_estoque[st.session_state.df_estoque['CHAVE_INTERNA'] == chave_prod].index
                    est_atual = int(st.session_state.df_estoque.loc[idx_est, 'TOTAL'].values[0])
                    if tipo_atual == "Entrada":
                        est_recalculado = est_atual - qtd_atual
                    else:
                        est_recalculado = est_atual + qtd_atual
                    if est_recalculado >= 0:
                        st.session_state.df_estoque.loc[idx_est, 'TOTAL'] = est_recalculado
                        st.session_state.historico = st.session_state.historico[st.session_state.historico['Mov_ID']!= mov_selecionada]
                        st.success("Movimentação removida e estoque estornado!")
                        st.rerun()
                    else:
                        st.error("Não é possível estornar esta entrada pois o estoque atual ficaria negativo.")
    else:
        st.info("Nenhuma movimentação realizada nesta sessão para habilitar o módulo de edição.")

    st.markdown("#### 📜 Registro Geral de Auditoria")
    if not st.session_state.historico.empty:
        st.dataframe(st.session_state.historico.drop(columns=['CHAVE_INTERNA']), use_container_width=True, hide_index=True)

with aba_alertas:
    st.subheader("🛡️ Relatório de Segurança de Estoque")
    df_zerados = st.session_state.df_estoque[st.session_state.df_estoque['TOTAL'] <= 0]
    if not df_zerados.empty:
        st.markdown('⚠️ ATENÇÃO: Os materiais listados abaixo estão com o estoque zerado!', unsafe_allow_html=True)
        st.dataframe(df_zerados.drop(columns=['CHAVE_INTERNA']), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Estoque seguro! Todos os materiais cadastrados possuem saldo positivo.")

with aba_novo:
    st.subheader("➕ Cadastrar Novo Material do Zero")
    with st.form("form_novo_item", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            n_desc = st.text_input("Descrição do Material (Ex: TIJOLO):").upper()
            n_marca = st.text_input("Marca/Fabricante:").upper()
        with c2:
            n_lote = st.text_input("Número do Lote:", value="9999")
            n_val = st.text_input("Data de Validade (DD/MM/AAAA):", value="00/00/0000")
        with c3:
            n_qtd = st.number_input("Estoque Inicial Atual:", min_value=0, value=0)
            n_pal = st.number_input("Quantidade por Palete:", min_value=0, value=1)
            n_uni = st.text_input("Unidade de Medida:", value="KILOS").upper()
        botao_salvar = st.form_submit_button("Salvar Novo Item no Almoxarifado")
        if botao_salvar:
            if not n_desc:
                st.error("O campo 'Descrição do Material' é obrigatório!")
            else:
                proximo_id = int(st.session_state.df_estoque["ID"].max() + 1)
                proxima_chave = int(st.session_state.df_estoque["CHAVE_INTERNA"].max() + 1)
                novo_item = {"ID": proximo_id, "DESCRIÇÃO": n_desc, "MARCA": n_marca, "LOTE": n_lote, "VALIDADE": n_val, "QTD/PALETE": n_pal, "TOTAL": n_qtd, "UNIDADE DE MEDIDA": n_uni, "CHAVE_INTERNA": proxima_chave}
                st.session_state.df_estoque = pd.concat([st.session_state.df_estoque, pd.DataFrame([novo_item])], ignore_index=True)
                st.success(f"Sucesso: Material '{n_desc}' integrado com saldo inicial de {n_qtd} {n_uni}!")
                st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📥 Exportar Backup")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    st.session_state.df_estoque.drop(columns=['CHAVE_INTERNA']).to_excel(writer, sheet_name='Estoque_Atual', index=False)
    if not st.session_state.historico.empty:
        st.session_state.historico.drop(columns=['CHAVE_INTERNA']).to_excel(writer, sheet_name='Historico_Movimentacoes', index=False)
st.sidebar.download_button(label="📥 Baixar Planilha Master (.XLSX)", data=buffer.getvalue(), file_name=f"inventario_almox_{datetime.now().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")