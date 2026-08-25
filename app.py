import streamlit as st
import pandas as pd
from datetime import date

CAPACIDADE_CHAO = 1000

if 'cadastro' not in st.session_state:
    st.session_state.cadastro = []
if 'mov' not in st.session_state:
    st.session_state.mov = []

st.set_page_config(page_title="Controle Armazem 1000 Posicoes", layout="wide")
st.title("📦 Controle de Armazém - 1000 Posições 100x120")

with st.expander("1️⃣ CADASTRO MANUAL", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        id_prod = st.text_input("ID")
        desc = st.text_input("Descrição")
        marca = st.text_input("Marca")
    with col2:
        unidade = st.text_input("Unidade (kg, peças, m²...)")
        emp = st.selectbox("Empilhamento", [1,2,3])
        fab = st.date_input("Fabricação", value=date.today())
    with col3:
        val = st.date_input("Validade", value=date.today())
        qtd_por_palete = st.number_input("QTD por Palete", min_value=0.0, value=0.0)
    
    if st.button("Salvar Cadastro"):
        st.session_state.cadastro.append({
            "ID": id_prod, "Descrição": desc.upper(), "Marca": marca.upper(),
            "Unidade": unidade, "Empilhamento": int(emp),
            "Fabricação": fab, "Validade": val, "QTD_por_palete": qtd_por_palete
        })
        st.success("Cadastrado!")

if st.session_state.cadastro:
    st.dataframe(pd.DataFrame(st.session_state.cadastro), use_container_width=True)

st.divider()
st.subheader("2️⃣ MOVIMENTAÇÃO")

if st.session_state.cadastro:
    df_cad = pd.DataFrame(st.session_state.cadastro)
    colA, colB, colC = st.columns(3)
    with colA:
        tipo = st.selectbox("Tipo", ["ENTRADA","SAIDA"])
        id_sel = st.selectbox("ID", df_cad["ID"].unique())
        marca_sel = st.selectbox("Marca", df_cad[df_cad["ID"]==id_sel]["Marca"].unique())
    with colB:
        prod = df_cad[(df_cad["ID"]==id_sel) & (df_cad["Marca"]==marca_sel)].iloc[-1]
        st.info(f"{prod['Descrição']} | {prod['Unidade']} | Emp: {prod['Empilhamento']}")
        qtd_paletes = st.number_input("QTD Paletes", min_value=0, step=1, value=1)
    with colC:
        qtd_unid = st.number_input(f"QTD em {prod['Unidade']}", min_value=0.0, value=0.0)
        pos = qtd_paletes / prod['Empilhamento']
        st.metric("Posições ocupadas", f"{pos:.2f}")

    if st.button("Adicionar Movimentação"):
        st.session_state.mov.append({
            "ID": id_sel, "Descrição": prod["Descrição"], "Marca": marca_sel,
            "Unidade": prod["Unidade"], "Empilhamento": prod["Empilhamento"],
            "Fabricação": prod["Fabricação"], "Validade": prod["Validade"],
            "QTD_Paletes": qtd_paletes if tipo=="ENTRADA" else -qtd_paletes,
            "QTD_Unidade": qtd_unid if tipo=="ENTRADA" else -qtd_unid
        })

if st.button("🔄 ATUALIZAR ESTOQUE", type="primary", use_container_width=True):
    st.rerun()

if st.session_state.mov:
    df_mov = pd.DataFrame(st.session_state.mov)
    saldo = df_mov.groupby(["ID","Descrição","Marca","Unidade","Empilhamento","Fabricação","Validade"], as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"), QTD_Unidade=("QTD_Unidade","sum"))
    saldo = saldo[saldo["QTD_Paletes"]>0]
    saldo["Posições_Ocupadas"] = saldo["QTD_Paletes"] / saldo["Empilhamento"]
    
    total_pos = saldo["Posições_Ocupadas"].sum()
    total_pal = saldo["QTD_Paletes"].sum()
    taxa = total_pos / CAPACIDADE_CHAO * 100

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Paletes Físicos", int(total_pal))
    c2.metric("Posições Ocupadas", f"{total_pos:.2f} / 1000")
    c3.metric("Livres", f"{1000-total_pos:.2f}")
    c4.metric("TAXA OCUPAÇÃO", f"{taxa:.2f}%")
    st.progress(min(taxa/100,1.0))
    
    st.dataframe(saldo, use_container_width=True)

    st.subheader("📊 Gráficos")
    id_g = st.selectbox("ID para gráficos", saldo["ID"].unique())
    df_g = saldo[saldo["ID"]==id_g]
    st.bar_chart(df_g.set_index("Marca")["QTD_Unidade"])
    st.bar_chart(df_g.set_index("Marca")["Posições_Ocupadas"])
