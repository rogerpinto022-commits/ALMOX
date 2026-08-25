import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os

st.set_page_config(page_title="Reforma de Fornos - Refratários", layout="wide", page_icon="🔥")

ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao_refratario.csv"

st.markdown("""
<style>
.main-header { background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 28px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
.main-header h1 { color: #ff6b35; font-size: 38px; font-weight: 800; margin:0; }
.main-header h2 { color: white; font-size: 17px; margin:8px 0 0 0; opacity:0.9; }
.card-ocupacao { background: white; border-radius: 12px; padding: 18px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 6px solid #ff6b35; }
</style>
""", unsafe_allow_html=True)

CAPACIDADE = 1000

def carregar():
    cad, mov = [], []
    if os.path.exists(ARQ_CAD):
        try: cad = pd.read_csv(ARQ_CAD).to_dict('records')
        except: pass
    if os.path.exists(ARQ_MOV):
        try: mov = pd.read_csv(ARQ_MOV).to_dict('records')
        except: pass
    return cad, mov

def salvar_cad():
    pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD, index=False)

def salvar_mov():
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False)

if 'cadastro' not in st.session_state or 'mov' not in st.session_state:
    c,m = carregar()
    st.session_state.cadastro = c
    st.session_state.mov = m

st.markdown("""
<div class="main-header">
    <h1>🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</h1>
    <h2>Controle de Armazém | 1000 Posições (100x120) | Empilhamento 1-2-3 | Gestão por Posição de Chão com LOTE</h2>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📝 CADASTRO", "🔄 MOVIMENTAÇÃO", "📦 SALDO E OCUPAÇÃO", "📈 DASHBOARD"])

with tab1:
    col_t1, col_t2, col_t3 = st.columns([2,1,1])
    with col_t1: st.subheader("Cadastro de Material")
    with col_t2:
        if os.path.exists(ARQ_CAD): st.success(f"✅ Gravados: {len(st.session_state.cadastro)} itens")
    with col_t3:
        if st.button("🗑️ APAGAR TUDO CADASTRO", use_container_width=True):
            st.session_state.cadastro = []
            if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
            st.rerun()
    
    with st.form("form_cad", clear_on_submit=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            id_p = st.text_input("ID *", placeholder="01")
            desc = st.text_input("DESCRIÇÃO *", placeholder="BLOCO, TIJOLO...")
            marca = st.text_input("MARCA *", placeholder="REFRATEC...")
        with c2:
            unidade = st.selectbox("UNIDADE *", ["peças","kg","m²","m³","ton","rolos","caixas","sacos","unidades"])
            emp = st.selectbox("EMPILHAMENTO *", [1,2,3])
            lote = st.text_input("LOTE *", placeholder="L2024-001")
        with c3:
            fab = st.date_input("FABRICAÇÃO", value=date.today())
            val = st.date_input("VALIDADE", value=date.today())
            qtd_pad = st.number_input("QTD por Palete", min_value=0.0, value=500.0)
        with c4:
            st.info(f"Emp {emp}: {emp} paletes = 1 posição\n20 pos = {20*emp} paletes")
            if st.form_submit_button("💾 SALVAR E GRAVAR", type="primary", use_container_width=True):
                if id_p and desc and marca and lote:
                    st.session_state.cadastro.append({
                        "ID": id_p.strip().upper(), "Descrição": desc.strip().upper(), "Marca": marca.strip().upper(),
                        "LOTE": lote.strip().upper(), "Unidade": unidade, "Empilhamento": int(emp),
                        "Fabricação": str(fab), "Validade": str(val), "QTD_por_palete": qtd_pad
                    })
                    salvar_cad()
                    st.success("Gravado!")
                else: st.error("ID, Descrição, Marca e LOTE obrigatórios")

    if st.session_state.cadastro:
        df_cad = pd.DataFrame(st.session_state.cadastro)
        for i, row in df_cad.iterrows():
            cc1, cc2, cc3, cc4, cc5, cc6 = st.columns([1,2,1.5,1,1,0.7])
            cc1.write(f"**{row['ID']}**")
            cc2.write(f"{row['Descrição']} | {row['Marca']}")
            cc3.write(f"Lote: {row['LOTE']} | Emp:{row['Empilhamento']}")
            cc4.write(f"{row['Unidade']}")
            cc5.write(f"Fab:{row['Fabricação']} Val:{row['Validade']}")
            if cc6.button("🗑️", key=f"del_cad_{i}"):
                st.session_state.cadastro.pop(i)
                salvar_cad()
                st.rerun()

with tab2:
    st.subheader("Movimentação")
    if not st.session_state.cadastro: st.warning("Cadastre primeiro")
    else:
        df_cad = pd.DataFrame(st.session_state.cadastro)
        ca, cb = st.columns([1.2,1.8])
        with ca:
            tipo = st.radio("TIPO", ["ENTRADA","SAÍDA"], horizontal=True)
            data_mov = st.date_input("Data", value=date.today())
            id_sel = st.selectbox("ID", sorted(df_cad["ID"].unique()))
            marca_sel = st.selectbox("MARCA", df_cad[df_cad["ID"]==id_sel]["Marca"].unique())
            df_f = df_cad[(df_cad["ID"]==id_sel) & (df_cad["Marca"]==marca_sel)]
            lote_sel = st.selectbox("LOTE", df_f["LOTE"].unique())
            prod = df_f[df_f["LOTE"]==lote_sel].iloc[-1]
        with cb:
            st.markdown(f"<div class='card-ocupacao'><b>{prod['Descrição']}</b> | {prod['Marca']} | LOTE {prod['LOTE']}<br>Unid: {prod['Unidade']} Emp: {prod['Empilhamento']}</div>", unsafe_allow_html=True)
            c1,c2,c3 = st.columns(3)
            with c1: qtd_pal = st.number_input("QTD PALETES", min_value=1, value=20, step=1)
            with c2: qtd_unid = st.number_input(f"QTD EM {prod['Unidade']}", value=float(prod['QTD_por_palete']*qtd_pal))
            with c3:
                pos_calc = qtd_pal / int(prod['Empilhamento'])
                st.metric("POSIÇÕES CHÃO", f"{pos_calc:.1f}")
            if st.button("➕ LANÇAR E GRAVAR", type="primary", use_container_width=True):
                st.session_state.mov.append({
                    "Data": str(data_mov), "Tipo": tipo, "ID": id_sel, "Descrição": prod["Descrição"], "Marca": marca_sel, "LOTE": lote_sel,
                    "Unidade": prod["Unidade"], "Empilhamento": int(prod["Empilhamento"]),
                    "Fabricação": prod["Fabricação"], "Validade": prod["Validade"],
                    "QTD_Paletes": int(qtd_pal) if tipo=="ENTRADA" else -int(qtd_pal),
                    "QTD_Unidade": float(qtd_unid) if tipo=="ENTRADA" else -float(qtd_unid),
                    "Posições": pos_calc if tipo=="ENTRADA" else -pos_calc
                })
                salvar_mov()
                st.success("Gravado!")
        
        if st.session_state.mov:
            if st.button("🗑️ APAGAR HISTÓRICO", use_container_width=True):
                st.session_state.mov = []
                if os.path.exists(ARQ_MOV): os.remove(ARQ_MOV)
                st.rerun()
            df_mov = pd.DataFrame(st.session_state.mov)
            for i, row in df_mov.reset_index().iterrows():
                cc1, cc2, cc3, cc4, cc5 = st.columns([1.5,2.5,1.5,1,0.6])
                cc1.write(f"{row['Data']} {row['Tipo']}")
                cc2.write(f"{row['ID']} {row['Marca']} L:{row['LOTE']}")
                cc3.write(f"{row['QTD_Paletes']} pal | {row['Posições']:.1f} pos")
                cc4.write(f"{row['QTD_Unidade']} {row['Unidade']}")
                if cc5.button("🗑️", key=f"del_mov_{i}"):
                    st.session_state.mov.pop(i)
                    salvar_mov()
                    st.rerun()

with tab3:
    if st.button("🔄 ATUALIZAR ESTOQUE", type="primary", use_container_width=True): st.rerun()
    if not st.session_state.mov: st.info("Vazio - 0/1000")
    else:
        df_mov = pd.DataFrame(st.session_state.mov)
        saldo = df_mov.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"], as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"), QTD_Unidade=("QTD_Unidade","sum"), Posições=("Posições","sum"))
        saldo = saldo[saldo["QTD_Paletes"]>0]
        saldo["Posições_Ocupadas"] = saldo["QTD_Paletes"] / saldo["Empilhamento"]
        total_pal = int(saldo["QTD_Paletes"].sum())
        total_pos = float(saldo["Posições_Ocupadas"].sum())
        taxa = total_pos / 1000 * 100
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("PALETES", total_pal)
        m2.metric("POSIÇÕES OCUPADAS", f"{total_pos:.1f}/1000", f"{taxa:.1f}%")
        m3.metric("LIVRES", f"{1000-total_pos:.1f}")
        m4.metric("TAXA", f"{taxa:.1f}%")
        st.progress(min(taxa/100,1.0))
        st.dataframe(saldo.sort_values(["ID","Validade"]), use_container_width=True)

with tab4:
    if not st.session_state.mov: st.warning("Sem dados")
    else:
        df_mov = pd.DataFrame(st.session_state.mov)
        saldo = df_mov.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"], as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"), QTD_Unidade=("QTD_Unidade","sum"))
        saldo = saldo[saldo["QTD_Paletes"]>0]
        saldo["Posições_Ocupadas"] = saldo["QTD_Paletes"]/saldo["Empilhamento"]
        saldo["Dias_para_vencer"] = (pd.to_datetime(saldo["Validade"]) - pd.to_datetime(date.today())).dt.days
        g1,g2 = st.columns(2)
        with g1:
            id_g = st.selectbox("ID Estoque", sorted(saldo["ID"].unique()), key="g1")
            df_f = saldo[saldo["ID"]==id_g]
            st.plotly_chart(px.pie(df_f, values="QTD_Unidade", names="Marca", color="LOTE", title=f"{id_g} por Marca/Lote", hole=0.4), use_container_width=True)
            st.plotly_chart(px.bar(df_f, x="Marca", y="QTD_Unidade", color="LOTE", barmode="stack", text="QTD_Paletes"), use_container_width=True)
        with g2:
            id_v = st.selectbox("ID Validade", sorted(saldo["ID"].unique()), key="g2")
            df_v = saldo[saldo["ID"]==id_v].sort_values("Validade")
            fig = px.scatter(df_v, x="Validade", y="Marca", size="QTD_Paletes", color="LOTE", title="Timeline Validade")
            fig.add_vline(x=pd.to_datetime(date.today()), line_dash="dash", line_color="red", annotation_text="HOJE")
            st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(px.bar(df_v, x="LOTE", y="Dias_para_vencer", color="Marca", title="Dias para vencer - FIFO"), use_container_width=True)
        total_pos = saldo["Posições_Ocupadas"].sum()
        df_occ = pd.DataFrame({"Status":["Ocupado","Livre"], "Pos":[total_pos, 1000-total_pos]})
        st.plotly_chart(px.pie(df_occ, values="Pos", names="Status", hole=0.6, title=f"Ocupação {total_pos:.0f}/1000"), use_container_width=True)
