import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox Certo", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")
ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"

# CRIA ARQUIVOS SE NAO EXISTEM
if not os.path.exists(ARQ_DADOS):
    pd.DataFrame([
        {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","LOCAL":"BARRACAO","SALDO":0,"VALIDADE_PADRAO":90},
        {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","LOCAL":"OFICINA","SALDO":0,"VALIDADE_PADRAO":90},
    ]).to_csv(ARQ_DADOS,index=False)

if not os.path.exists(ARQ_MOV):
    pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","TOTAL","UNIDADE","LOCAL","ID_MAT","NOME_MAT","RESPONSAVEL"]).to_csv(ARQ_MOV,index=False)

if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin"}]).to_csv(ARQ_EMAILS,index=False)

if "logado" not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.title("Login")
    e=st.text_input("Email").lower().strip()
    s=st.text_input("Senha",type="password")
    if st.button("Entrar"):
        df_e=pd.read_csv(ARQ_EMAILS)
        if not df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"]==s)].empty:
            st.session_state.logado=True
            st.session_state.usuario=e
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            try:
                df_m=pd.read_csv(ARQ_MOV)
                st.session_state.mov=[] if df_m.empty or "IDX" not in df_m.columns else df_m.to_dict('records')
            except: st.session_state.mov=[]
            st.rerun()
    st.stop()

agora=datetime.now(FUSO)
hoje=date.today()
if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

# ESTOQUE
df_est=pd.DataFrame(st.session_state.dados)
pivot=df_est.pivot_table(index=["ID","NOME","VALIDADE_PADRAO"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACAO" not in pivot.columns: pivot["BARRACAO"]=0
if "OFICINA" not in pivot.columns: pivot["OFICINA"]=0
pivot["TOTAL"]=pivot["BARRACAO"]+pivot["OFICINA"]
st.title(f"TOTAL: {pivot['TOTAL'].sum():.0f}")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)

# GRAFICO 1 - SEMPRE APARECE
st.subheader("Grafico 1 - Estoque por Local")
st.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACAO","OFICINA"], barmode="group", title="Estoque Barracão x Oficina"), use_container_width=True)

# LANCAMENTO
st.divider()
st.subheader("Lançamento com Validade")
ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa={d["ID"]:(d["NOME"],d["UNIDADE"],d.get("VALIDADE_PADRAO",180)) for d in st.session_state.dados}
id_sel=st.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa[x][0]}")
local_sel=st.selectbox("Local", ["BARRACAO","OFICINA"])
c1,c2,c3,c4,c5=st.columns(5)
lote=c1.text_input("LOTE")
data_fab=c2.date_input("FAB", value=hoje)
validade=c3.date_input("VALIDADE", value=data_fab+timedelta(days=int(mapa[id_sel][2])))
qtd=c4.number_input("QTD",value=1.0)
ent=c5.number_input("Paletes",value=1.0)
dias_rest=(validade-hoje).days
status="VENCIDO" if dias_rest<0 else "A VENCER 30d" if dias_rest<=30 else "A VENCER 90d" if dias_rest<=90 else "OK"
st.info(f"Restam {dias_rest} dias - {status}")

if st.button(f"SALVAR - {status}", type="primary", use_container_width=True):
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACAO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    total=qtd*ent
    if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]+=total
    else: st.session_state.dados[idx_ba]["SALDO"]-=total; st.session_state.dados[idx_of]["SALDO"]+=total
    novo_id=max([int(m.get("IDX",0)) for m in st.session_state.mov])+1 if st.session_state.mov else 1
    novo={"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M"),"DATA_FAB":data_fab.strftime("%d/%m/%Y"),"VALIDADE":validade.strftime("%d/%m/%Y"),"DIAS_VALIDADE":(validade-data_fab).days,"STATUS_VAL":status,"LOTE":lote.upper(),"TOTAL":total,"UNIDADE":mapa[id_sel][1],"LOCAL":local_sel,"ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":st.session_state.usuario}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
    st.rerun()

# GRAFICOS VALIDADE COM FILTRO
st.divider()
st.header("📅 VALIDADE - VENCIDOS E A VENCER")

if not st.session_state.mov:
    st.warning("Ainda sem lotes. Lance 1 lote para ver os graficos de validade aqui.")
else:
    df_mov=pd.DataFrame(st.session_state.mov)
    df_mov["VAL_DT"]=pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
    df_mov["FAB_DT"]=pd.to_datetime(df_mov["DATA_FAB"], format="%d/%m/%Y", errors='coerce')
    df_mov["DIAS_REST"]=(df_mov["VAL_DT"]-pd.Timestamp(hoje)).dt.days
    def stt(d):
        if pd.isna(d): return "SEM"
        if d<0: return "VENCIDO"
        if d<=30: return "A VENCER 30d"
        if d<=90: return "A VENCER 90d"
        return "OK"
    df_mov["STATUS_ATUAL"]=df_mov["DIAS_REST"].apply(stt)

    # FILTRO QUE VOCE PEDIU
    lista=sorted(df_mov["NOME_MAT"].dropna().unique().tolist())
    sel=st.multiselect("SELECIONE OS MATERIAIS PARA MOSTRAR NO GRAFICO:", options=lista, default=lista)

    df_f=df_mov[df_mov["NOME_MAT"].isin(sel)] if sel else df_mov

    c1,c2,c3,c4=st.columns(4)
    c1.metric("VENCIDOS", len(df_f[df_f["STATUS_ATUAL"]=="VENCIDO"]))
    c2.metric("30d", len(df_f[df_f["STATUS_ATUAL"]=="A VENCER 30d"]))
    c3.metric("90d", len(df_f[df_f["STATUS_ATUAL"]=="A VENCER 90d"]))
    c4.metric("OK", len(df_f[df_f["STATUS_ATUAL"]=="OK"]))

    st.subheader("Grafico 2 - Vencidos e a Vencer (Filtrado)")
    st.plotly_chart(px.bar(df_f, x="NOME_MAT", color="STATUS_ATUAL", title="Vencidos e a Vencer", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)

    st.subheader("Grafico 3 - Fabricacao vs Vencimento (Filtrado)")
    st.plotly_chart(px.scatter(df_f, x="FAB_DT", y="VAL_DT", color="STATUS_ATUAL", size="TOTAL", hover_data=["LOTE","DIAS_REST","NOME_MAT"], title="Fab vs Validade"), use_container_width=True)

    st.dataframe(df_f.sort_values("VAL_DT")[["IDX","NOME_MAT","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","LOTE","TOTAL","LOCAL"]], use_container_width=True)
