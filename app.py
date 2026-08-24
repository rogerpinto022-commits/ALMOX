import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox Filtro Validade", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")
ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"
ARQ_FORN = "fornecedores.csv"

def init():
    if not os.path.exists(ARQ_DADOS):
        lista = [
            {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"-","LOCAL":"BARRACAO","SALDO":0,"VALIDADE_PADRAO":90},
            {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"-","LOCAL":"OFICINA","SALDO":0,"VALIDADE_PADRAO":90},
        ]
        pd.DataFrame(lista).to_csv(ARQ_DADOS,index=False)
    if not os.path.exists(ARQ_MOV):
        pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","MARCA","FORNECEDOR","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
    if not os.path.exists(ARQ_EMAILS):
        pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","PERFIL":"ADMINISTRADOR"}]).to_csv(ARQ_EMAILS,index=False)
    if not os.path.exists(ARQ_FORN):
        pd.DataFrame([{"ID_FORN":i+1,"NOME":n,"MARCA":n} for i,n in enumerate(["FONDU","SHINAGAWA","TECNOFIRE","CABOFRAX","IBAR","BIOLA"])]).to_csv(ARQ_FORN,index=False)

init()

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("Login")
    e = st.text_input("Email").lower().strip()
    s = st.text_input("Senha",type="password")
    if st.button("Entrar"):
        df_e = pd.read_csv(ARQ_EMAILS)
        u = df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"]==s)]
        if not u.empty:
            st.session_state.logado = True
            st.session_state.usuario = e
            st.session_state.dados = pd.read_csv(ARQ_DADOS).to_dict('records')
            try:
                df_m = pd.read_csv(ARQ_MOV)
                st.session_state.mov = [] if df_m.empty or "IDX" not in df_m.columns else df_m.to_dict('records')
            except:
                st.session_state.mov = []
            st.rerun()
    st.stop()

agora = datetime.now(FUSO)
hoje = date.today()

with st.sidebar.expander("EDITAR VALIDADE PADRAO", expanded=True):
    df_tmp = pd.DataFrame(st.session_state.dados).drop_duplicates("ID")[["ID","NOME","VALIDADE_PADRAO"]].sort_values("ID")
    st.dataframe(df_tmp, use_container_width=True, hide_index=True)
    if not df_tmp.empty:
        id_val = st.selectbox("ID material", df_tmp["ID"].tolist(), key="idval")
        linha_val = df_tmp[df_tmp["ID"]==id_val].iloc[0]
        novos_dias = st.number_input(f"Dias - {linha_val['NOME']}", min_value=1, max_value=3650, value=int(linha_val["VALIDADE_PADRAO"]), step=1)
        if st.button("Salvar validade padrao"):
            for d in st.session_state.dados:
                if d["ID"] == id_val: d["VALIDADE_PADRAO"] = novos_dias
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            st.rerun()

if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

# ESTOQUE
df_est = pd.DataFrame(st.session_state.dados)
pivot = df_est.pivot_table(index=["ID","NOME","VALIDADE_PADRAO"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACAO" not in pivot.columns: pivot["BARRACAO"] = 0
if "OFICINA" not in pivot.columns: pivot["OFICINA"] = 0
pivot["TOTAL"] = pivot["BARRACAO"] + pivot["OFICINA"]
st.title(f"TOTAL: {pivot['TOTAL'].sum():.0f}")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)

# LANCAMENTO
st.divider()
ids = sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa = {d["ID"]:(d["NOME"],d["UNIDADE"],d.get("VALIDADE_PADRAO",180)) for d in st.session_state.dados}
id_sel = st.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa[x][0]} - {mapa[x][2]} dias")
local_sel = st.selectbox("Local", ["BARRACAO","OFICINA"])
c1,c2,c3,c4,c5 = st.columns(5)
lote = c1.text_input("LOTE")
data_fab = c2.date_input("DATA FAB", value=hoje)
validade_default = data_fab + timedelta(days=int(mapa[id_sel][2]))
validade = c3.date_input("VALIDADE", value=validade_default)
qtd = c4.number_input("QTD",value=1.0)
ent = c5.number_input("Paletes",value=1.0)
dias_validade = (validade - data_fab).days
dias_restantes = (validade - hoje).days
status = "VENCIDO" if dias_restantes<0 else "A VENCER 30d" if dias_restantes<=30 else "A VENCER 90d" if dias_restantes<=90 else "OK"
st.info(f"Padrao: {mapa[id_sel][2]} dias | Calculado: {dias_validade} | Restam: {dias_restantes} | {status}")

if st.button(f"SALVAR - {status}", type="primary", use_container_width=True):
    idx_ba = next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACAO"),None)
    idx_of = next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    total_calc = qtd*ent
    if idx_ba is not None:
        if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]+=total_calc
        else: st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc
        novo_id = max([int(m.get("IDX",0)) for m in st.session_state.mov])+1 if st.session_state.mov else 1
        novo = {"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_FAB":data_fab.strftime("%d/%m/%Y"),"VALIDADE":validade.strftime("%d/%m/%Y"),"DIAS_VALIDADE":dias_validade,"STATUS_VAL":status,"LOTE":lote.upper(),"MARCA":"-","FORNECEDOR":"-","QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total_calc,"UNIDADE":mapa[id_sel][1],"LOCAL":local_sel,"TIPO":"Entrada","ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":st.session_state.usuario,"OBS":status}
        st.session_state.mov.append(novo)
        pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
        st.rerun()

# GRAFICOS COM FILTRO DE MATERIAIS
if st.session_state.mov and len(st.session_state.mov)>0:
    df_mov = pd.DataFrame(st.session_state.mov)
    if not df_mov.empty and "IDX" in df_mov.columns:
        df_mov["VAL_DT"] = pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
        df_mov["FAB_DT"] = pd.to_datetime(df_mov["DATA_FAB"], format="%d/%m/%Y", errors='coerce')
        df_mov["DIAS_REST"] = (df_mov["VAL_DT"] - pd.Timestamp(hoje)).dt.days
        def stt(d):
            if pd.isna(d): return "SEM"
            if d<0: return "VENCIDO"
            if d<=30: return "A VENCER 30d"
            if d<=90: return "A VENCER 90d"
            return "OK"
        df_mov["STATUS_ATUAL"] = df_mov["DIAS_REST"].apply(stt)

        st.divider()
        st.subheader("Controle Validade - SELECIONE MATERIAIS")

        # AQUI O FILTRO QUE VOCE QUER
        lista_materiais = sorted(df_mov["NOME_MAT"].dropna().unique().tolist())
        materiais_selecionados = st.multiselect(
            "Escolha os materiais para mostrar no grafico (deixe vazio = todos)",
            options=lista_materiais,
            default=[],
            placeholder="Selecione CIMENTO, CAL, etc"
        )

        if materiais_selecionados:
            df_filtrado = df_mov[df_mov["NOME_MAT"].isin(materiais_selecionados)]
        else:
            df_filtrado = df_mov

        if df_filtrado.empty:
            st.warning("Nenhum dado para os materiais selecionados")
        else:
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("VENCIDOS", len(df_filtrado[df_filtrado["STATUS_ATUAL"]=="VENCIDO"]))
            m2.metric("30d", len(df_filtrado[df_filtrado["STATUS_ATUAL"]=="A VENCER 30d"]))
            m3.metric("90d", len(df_filtrado[df_filtrado["STATUS_ATUAL"]=="A VENCER 90d"]))
            m4.metric("OK", len(df_filtrado[df_filtrado["STATUS_ATUAL"]=="OK"]))

            st.plotly_chart(px.bar(df_filtrado, x="NOME_MAT", color="STATUS_ATUAL", title=f"VENCIDOS E A VENCER - {', '.join(materiais_selecionados) if materiais_selecionados else 'TODOS'}", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)
            st.plotly_chart(px.scatter(df_filtrado, x="FAB_DT", y="VAL_DT", color="STATUS_ATUAL", size="TOTAL", hover_data=["LOTE","DIAS_REST","NOME_MAT"], title="FABRICACAO vs VENCIMENTO - FILTRADO"), use_container_width=True)
            st.dataframe(df_filtrado.sort_values("VAL_DT")[["IDX","NOME_MAT","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","LOTE","TOTAL","LOCAL"]], use_container_width=True)
