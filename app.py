import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import os

st.set_page_config(page_title="Reforma de Fornos - Refratários", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao_refratario.csv"
CAPACIDADE = 1000

st.markdown("""
<style>
.main-header { background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 28px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
.main-header h1 { color: #ff6b35; font-size: 36px; font-weight: 800; margin:0; }
.main-header h2 { color: white; font-size: 16px; margin-top:6px; opacity:0.9; }
</style>
""", unsafe_allow_html=True)

def carregar():
    cad, mov = [], []
    if os.path.exists(ARQ_CAD):
        try: cad = pd.read_csv(ARQ_CAD).to_dict('records')
        except: pass
    if os.path.exists(ARQ_MOV):
        try: mov = pd.read_csv(ARQ_MOV).to_dict('records')
        except: pass
    return cad, mov

def salvar_cad(): pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD, index=False)
def salvar_mov(): pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False)

if 'cadastro' not in st.session_state or 'mov' not in st.session_state:
    c,m = carregar()
    st.session_state.cadastro = c
    st.session_state.mov = m

st.markdown("""
<div class="main-header">
    <h1>🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</h1>
    <h2>1000 Posições (100x120) | Empilhamento 1-2-3 | Gestão por Posição de Chão | LOTE + Validade Editável</h2>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📝 CADASTRO", "🔄 MOVIMENTAÇÃO", "📦 SALDO", "📈 DASHBOARD"])

with tab1:
    st.subheader("Cadastro com Validade Corrigida")
    st.caption("Agora você define FABRICAÇÃO + DIAS DE VALIDADE e o app calcula a data certa. Ou edita a data direto.")

    with st.form("form_cad", clear_on_submit=True):
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            id_p = st.text_input("ID *", placeholder="01")
            desc = st.text_input("DESCRIÇÃO *", placeholder="BLOCO ESTRELA")
            marca = st.text_input("MARCA *", placeholder="ESTRELA")
            lote = st.text_input("LOTE *", placeholder="L2024-001")
        with c2:
            unidade = st.selectbox("UNIDADE *", ["peças","kg","m²","m³","ton","rolos","caixas","sacos"])
            emp = st.selectbox("EMPILHAMENTO *", [1,2,3])
            qtd_pad = st.number_input("QTD por Palete", value=500.0)
        with c3:
            fab = st.date_input("FABRICAÇÃO", value=date.today())
            dias_val = st.number_input("DIAS DE VALIDADE", min_value=1, value=365, help="Ex: 365 dias = 1 ano. O app soma na fabricação")
            # CALCULO CORRETO DA VALIDADE
            val_calc = fab + timedelta(days=int(dias_val))
            st.success(f"Validade calculada: {val_calc.strftime('%d/%m/%Y')}")
            val_manual = st.date_input("Ou ajuste a VALIDADE manual", value=val_calc)
        with c4:
            st.info(f"Emp {emp}: {emp} pal = 1 pos\n20 pos = {20*emp} paletes")
            if st.form_submit_button("💾 SALVAR E GRAVAR", type="primary", use_container_width=True):
                if id_p and desc and marca and lote:
                    st.session_state.cadastro.append({
                        "ID": id_p.strip().upper(), "Descrição": desc.strip().upper(), "Marca": marca.strip().upper(),
                        "LOTE": lote.strip().upper(), "Unidade": unidade, "Empilhamento": int(emp),
                        "Fabricação": str(fab), "Validade": str(val_manual), "Dias_Validade": int(dias_val),
                        "QTD_por_palete": qtd_pad
                    })
                    salvar_cad()
                    st.success(f"Salvo! Validade: {val_manual}")
                else:
                    st.error("Preencha ID, Descrição, Marca e LOTE")

    if st.session_state.cadastro:
        st.divider()
        st.markdown("#### 📋 Editar Validade e Excluir")
        df_cad = pd.DataFrame(st.session_state.cadastro)
        # EDITOR DE TABELA PARA EDITAR VALIDADE
        df_edit = st.data_editor(
            df_cad,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
                "Fabricação": st.column_config.DateColumn("Fabricação", format="DD/MM/YYYY"),
            },
            key="editor_cad"
        )
        c_save, c_del = st.columns(2)
        with c_save:
            if st.button("💾 GRAVAR ALTERAÇÕES DE VALIDADE", type="primary", use_container_width=True):
                st.session_state.cadastro = df_edit.to_dict('records')
                # Recalcula Dias_Validade corretamente
                for item in st.session_state.cadastro:
                    try:
                        f = pd.to_datetime(item['Fabricação'])
                        v = pd.to_datetime(item['Validade'])
                        item['Dias_Validade'] = (v - f).days
                    except: pass
                salvar_cad()
                st.success("Validade atualizada e gravada!")
                st.rerun()
        with c_del:
            if st.button("🗑️ APAGAR TODO CADASTRO", use_container_width=True):
                st.session_state.cadastro = []
                if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
                st.rerun()

with tab2:
    st.subheader("Movimentação")
    if not st.session_state.cadastro: st.warning("Cadastre primeiro")
    else:
        df_cad = pd.DataFrame(st.session_state.cadastro)
        ca, cb = st.columns([1.2,1.8])
        with ca:
            tipo = st.radio("TIPO", ["ENTRADA","SAÍDA"], horizontal=True)
            data_mov = st.date_input("Data Movimento", value=date.today())
            id_sel = st.selectbox("ID", sorted(df_cad["ID"].unique()))
            marca_sel = st.selectbox("MARCA", df_cad[df_cad["ID"]==id_sel]["Marca"].unique())
            df_f = df_cad[(df_cad["ID"]==id_sel) & (df_cad["Marca"]==marca_sel)]
            lote_sel = st.selectbox("LOTE", df_f["LOTE"].unique())
            prod = df_f[df_f["LOTE"]==lote_sel].iloc[-1]
        with cb:
            st.info(f"**{prod['Descrição']}** | {prod['Marca']} | LOTE {prod['LOTE']} | Fab {prod['Fabricação']} | Val {prod['Validade']} | Emp {prod['Empilhamento']}")
            c1,c2,c3 = st.columns(3)
            with c1: qtd_pal = st.number_input("QTD PALETES", min_value=1, value=20, step=1)
            with c2: qtd_unid = st.number_input(f"QTD {prod['Unidade']}", value=float(prod['QTD_por_palete']*qtd_pal))
            with c3:
                pos_calc = qtd_pal / int(prod['Empilhamento'])
                st.metric("POSIÇÕES CHÃO", f"{pos_calc:.1f}")
            if st.button("➕ LANÇAR E GRAVAR", type="primary", use_container_width=True):
                st.session_state.mov.append({
                    "Data": str(data_mov), "Tipo": tipo, "ID": id_sel, "Descrição": prod["Descrição"], "Marca": marca_sel, "LOTE": lote_sel,
                    "Unidade": prod["Unidade"], "Empilhamento": int(prod["Empilhamento"]),
                    "Fabricação": str(prod["Fabricação"]), "Validade": str(prod["Validade"]),
                    "QTD_Paletes": int(qtd_pal) if tipo=="ENTRADA" else -int(qtd_pal),
                    "QTD_Unidade": float(qtd_unid) if tipo=="ENTRADA" else -float(qtd_unid),
                    "Posições": pos_calc if tipo=="ENTRADA" else -pos_calc
                })
                salvar_mov()
                st.success("Gravado!")

        if st.session_state.mov:
            st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)
            if st.button("🗑️ APAGAR MOVIMENTAÇÕES"): 
                st.session_state.mov = []
                if os.path.exists(ARQ_MOV): os.remove(ARQ_MOV)
                st.rerun()

with tab3:
    st.subheader("Saldo e Ocupação")
    if st.button("🔄 ATUALIZAR", type="primary"): st.rerun()
    if not st.session_state.mov: st.info("Vazio 0/1000")
    else:
        df_mov = pd.DataFrame(st.session_state.mov)
        # CORREÇÃO CALCULO VALIDADE
        df_mov["Validade_dt"] = pd.to_datetime(df_mov["Validade"])
        df_mov["Fabricação_dt"] = pd.to_datetime(df_mov["Fabricação"])
        df_mov["Dias_para_vencer"] = (df_mov["Validade_dt"] - pd.to_datetime(date.today())).dt.days

        saldo = df_mov.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"], as_index=False).agg(
            QTD_Paletes=("QTD_Paletes","sum"), QTD_Unidade=("QTD_Unidade","sum"), Posições=("Posições","sum"),
            Dias_para_vencer=("Dias_para_vencer","min")
        )
        saldo = saldo[saldo["QTD_Paletes"]>0]
        saldo["Posições_Ocupadas"] = saldo["QTD_Paletes"] / saldo["Empilhamento"]
        
        # Alerta validade
        saldo["Status_Val"] = saldo["Dias_para_vencer"].apply(lambda x: "🔴 VENCIDO" if x<0 else "🟡 VENCE <30d" if x<=30 else "🟢 OK")

        total_pos = saldo["Posições_Ocupadas"].sum()
        taxa = total_pos/1000*100
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("PALETES", int(saldo["QTD_Paletes"].sum()))
        m2.metric("POSIÇÕES", f"{total_pos:.1f}/1000", f"{taxa:.1f}%")
        m3.metric("LIVRES", f"{1000-total_pos:.1f}")
        m4.metric("VENCIDOS", len(saldo[saldo["Dias_para_vencer"]<0]))

        st.dataframe(saldo.sort_values("Dias_para_vencer"), use_container_width=True)

with tab4:
    st.subheader("Dashboard Validade Corrigida")
    if not st.session_state.mov: st.warning("Sem dados")
    else:
        df_mov = pd.DataFrame(st.session_state.mov)
        df_mov["Validade_dt"] = pd.to_datetime(df_mov["Validade"])
        df_mov["Fabricação_dt"] = pd.to_datetime(df_mov["Fabricação"])
        df_mov["Dias_para_vencer"] = (df_mov["Validade_dt"] - pd.to_datetime(date.today())).dt.days

        saldo = df_mov.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"], as_index=False).agg(
            QTD_Paletes=("QTD_Paletes","sum"), QTD_Unidade=("QTD_Unidade","sum"), Dias_para_vencer=("Dias_para_vencer","min")
        )
        saldo = saldo[saldo["QTD_Paletes"]>0]
        saldo["Posições_Ocupadas"] = saldo["QTD_Paletes"]/saldo["Empilhamento"]
        saldo = saldo.sort_values("Validade")

        id_v = st.selectbox("Filtrar ID", sorted(saldo["ID"].unique()))
        df_v = saldo[saldo["ID"]==id_v]

        fig = px.scatter(df_v, x="Validade", y="Marca", size="QTD_Paletes", color="LOTE", 
                         hover_data=["Dias_para_vencer","Fabricação"], 
                         title=f"Timeline Validade - {id_v} | Cálculo Correto Dias para Vencer")
        fig.add_vline(x=pd.to_datetime(date.today()), line_dash="dash", line_color="red", annotation_text="HOJE")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.bar(df_v, x="LOTE", y="Dias_para_vencer", color="Marca", 
                      title="Dias para vencer por Lote - Quanto menor, sai primeiro (FIFO)",
                      color_continuous_scale="RdYlGn")
        st.plotly_chart(fig2, use_container_width=True)
