import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox Visual Destaque", layout="wide")

# VISUAL COM DESTAQUE
st.markdown("""
<style>
.vencido {background:linear-gradient(90deg,#ff0000,#cc0000); color:white; padding:15px; border-radius:12px; font-weight:bold; font-size:18px; text-align:center; border:2px solid white}
.a30 {background:linear-gradient(90deg,#ff9800,#ff6a00); color:white; padding:15px; border-radius:12px; font-weight:bold; font-size:18px; text-align:center}
.a90 {background:linear-gradient(90deg,#ffcc00,#ffaa00); color:black; padding:15px; border-radius:12px; font-weight:bold; font-size:18px; text-align:center}
.ok {background:linear-gradient(90deg,#00c853,#009624); color:white; padding:15px; border-radius:12px; font-weight:bold; font-size:18px; text-align:center}
.card-total {background:#111; border:2px solid #00ff00; padding:20px; border-radius:15px; text-align:center}
</style>
""", unsafe_allow_html=True)

FUSO = ZoneInfo("America/Sao_Paulo")
ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"

if os.path.exists(ARQ_MOV):
    try:
        df_old = pd.read_csv(ARQ_MOV)
        if "UNIDADE" not in df_old.columns: os.remove(ARQ_MOV)
    except: pass

if not os.path.exists(ARQ_DADOS):
    pd.DataFrame([
        {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"VOTORAN","LOCAL":"BARRACAO","SALDO":100,"VALIDADE_PADRAO":90,"FORNECEDOR":"LEROY"},
        {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"VOTORAN","LOCAL":"OFICINA","SALDO":20,"VALIDADE_PADRAO":90,"FORNECEDOR":"LEROY"},
    ]).to_csv(ARQ_DADOS,index=False)

if not os.path.exists(ARQ_MOV):
    pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","MARCA","FORNECEDOR","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)

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
            st.session_state.logado=True; st.session_state.usuario=e
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            df_m=pd.read_csv(ARQ_MOV)
            st.session_state.mov=[] if df_m.empty else df_m.to_dict('records')
            st.rerun()
    st.stop()

agora=datetime.now(FUSO); hoje=date.today()
if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

for d in st.session_state.dados:
    try: d["SALDO"]=float(d["SALDO"])
    except: d["SALDO"]=0.0

df_est=pd.DataFrame(st.session_state.dados)
pivot=df_est.pivot_table(index=["ID","NOME","UNIDADE"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
for c in ["BARRACAO","OFICINA"]:
    if c not in pivot.columns: pivot[c]=0.0
pivot["TOTAL"]=pivot["BARRACAO"]+pivot["OFICINA"]

st.markdown(f'<div class="card-total"><h1>📦 TOTAL ESTOQUE: {pivot["TOTAL"].sum():.0f}</h1></div>', unsafe_allow_html=True)
st.dataframe(pivot.sort_values("ID"), use_container_width=True)
c1,c2=st.columns(2)
with c1: st.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACAO","OFICINA"], barmode="group", title="G1 - Estoque por Local"), use_container_width=True)
with c2: st.plotly_chart(px.pie(pivot, names="NOME", values="TOTAL", title="G2 - Pizza"), use_container_width=True)

st.divider()
st.header("📝 LANÇAMENTO - TODOS OS CAMPOS")
ids=sorted(list(set([int(d["ID"]) for d in st.session_state.dados])))
mapa={int(d["ID"]):(d["NOME"],d["UNIDADE"],int(d.get("VALIDADE_PADRAO",90)),d.get("MARCA",""),d.get("FORNECEDOR","")) for d in st.session_state.dados}
id_sel=st.selectbox("MATERIAL", ids, format_func=lambda x: f"{x} - {mapa[x][0]}")

cA,cB,cC,cD,cE=st.columns(5)
marca=cA.text_input("MARCA", value=mapa[id_sel][3])
fornecedor=cB.text_input("FORNECEDOR *", value=mapa[id_sel][4])
lote=cC.text_input("LOTE *")
unidade=cD.text_input("UNIDADE *", value=mapa[id_sel][1])
obs=cE.text_input("OBS / NF")

c1,c2,c3,c4,c5,c6=st.columns(6)
local_sel=c1.selectbox("LOCAL *", ["BARRACAO","OFICINA"])
data_fab=c2.date_input("FAB *", value=hoje)
validade=c3.date_input("VAL *", value=data_fab+timedelta(days=int(mapa[id_sel][2])))
qtd_palete=c4.number_input("QTD POR PALETE *", value=1.0)
entrada=c5.number_input("QTD ENTRADA/SAIDA *", value=1.0)
tipo=c6.selectbox("TIPO *", ["Entrada","Saida"])

total=qtd_palete*entrada
dias_validade=(validade-data_fab).days
dias_rest=(validade-hoje).days
status="VENCIDO" if dias_rest<0 else "A VENCER 30d" if dias_rest<=30 else "A VENCER 90d" if dias_rest<=90 else "OK"

# DESTAQUE VISUAL
if status=="VENCIDO":
    st.markdown(f'<div class="vencido">⛔ VENCIDO - FALTAM {dias_rest} DIAS | {fornecedor} | LOTE {lote} | {total} {unidade}</div>', unsafe_allow_html=True)
elif status=="A VENCER 30d":
    st.markdown(f'<div class="a30">⚠️ VENCE EM 30 DIAS - {dias_rest} DIAS RESTANTES | {fornecedor}</div>', unsafe_allow_html=True)
elif status=="A VENCER 90d":
    st.markdown(f'<div class="a90">⚠️ VENCE EM 90 DIAS - {dias_rest} DIAS</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="ok">✅ OK - {dias_rest} DIAS RESTANTES | {fornecedor} | {total} {unidade}</div>', unsafe_allow_html=True)

m1,m2,m3,m4=st.columns(4)
m1.metric("TOTAL LOTE", f"{total} {unidade}")
m2.metric("DIAS RESTAM", f"{dias_rest} dias", delta=status, delta_color="inverse" if status=="VENCIDO" else "normal")
m3.metric("VALIDADE LOTE", f"{dias_validade} dias")
m4.metric("FORNECEDOR", fornecedor)

if st.button(f"💾 SALVAR {tipo.upper()} - {status}", type="primary", use_container_width=True):
    if not fornecedor or not lote or not unidade:
        st.error("FORNECEDOR, LOTE e UNIDADE obrigatórios"); st.stop()
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==id_sel and d["LOCAL"]=="BARRACAO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==id_sel and d["LOCAL"]=="OFICINA"),None)
    if idx_ba is None:
        st.session_state.dados.append({"ID":id_sel,"NOME":mapa[id_sel][0],"UNIDADE":unidade.upper(),"MARCA":marca.upper(),"LOCAL":"BARRACAO","SALDO":0.0,"VALIDADE_PADRAO":mapa[id_sel][2],"FORNECEDOR":fornecedor.upper()})
        idx_ba=len(st.session_state.dados)-1
    if idx_of is None:
        st.session_state.dados.append({"ID":id_sel,"NOME":mapa[id_sel][0],"UNIDADE":unidade.upper(),"MARCA":marca.upper(),"LOCAL":"OFICINA","SALDO":0.0,"VALIDADE_PADRAO":mapa[id_sel][2],"FORNECEDOR":fornecedor.upper()})
        idx_of=len(st.session_state.dados)-1
    st.session_state.dados[idx_ba]["SALDO"]=float(st.session_state.dados[idx_ba].get("SALDO",0))
    st.session_state.dados[idx_of]["SALDO"]=float(st.session_state.dados[idx_of].get("SALDO",0))
    st.session_state.dados[idx_ba]["UNIDADE"]=unidade.upper()
    st.session_state.dados[idx_of]["UNIDADE"]=unidade.upper()
    if tipo=="Entrada":
        if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]+=total
        else: st.session_state.dados[idx_ba]["SALDO"]-=total; st.session_state.dados[idx_of]["SALDO"]+=total
    else:
        if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]-=total
        else: st.session_state.dados[idx_of]["SALDO"]-=total
    novo_id=max([int(m.get("IDX",0)) for m in st.session_state.mov])+1 if st.session_state.mov else 1
    novo={"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_FAB":data_fab.strftime("%d/%m/%Y"),"VALIDADE":validade.strftime("%d/%m/%Y"),"DIAS_VALIDADE":dias_validade,"STATUS_VAL":status,"LOTE":lote.upper(),"MARCA":marca.upper(),"FORNECEDOR":fornecedor.upper(),"QTD_PALETE":qtd_palete,"ENTRADA":entrada,"TOTAL":total,"UNIDADE":unidade.upper(),"LOCAL":local_sel,"TIPO":tipo,"ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":st.session_state.usuario,"OBS":obs.upper()}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
    st.success(f"Salvo {total} {unidade} - {status}"); st.rerun()

# GRAFICOS 3-11 COM DESTAQUE
st.divider()
if st.session_state.mov:
    df_mov=pd.DataFrame(st.session_state.mov)
    df_mov["VAL_DT"]=pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
    df_mov["FAB_DT"]=pd.to_datetime(df_mov["DATA_FAB"], format="%d/%m/%Y", errors='coerce')
    df_mov["DATA_HORA_DT"]=pd.to_datetime(df_mov["DATA_HORA"], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    df_mov["DIAS_REST"]=(df_mov["VAL_DT"]-pd.Timestamp(hoje)).dt.days
    df_mov["STATUS_ATUAL"]=df_mov["DIAS_REST"].apply(lambda d: "VENCIDO" if d<0 else "A VENCER 30d" if d<=30 else "A VENCER 90d" if d<=90 else "OK")
    sel=st.multiselect("FILTRO MATERIAL", options=sorted(df_mov["NOME_MAT"].unique()), default=sorted(df_mov["NOME_MAT"].unique()))
    df_f=df_mov[df_mov["NOME_MAT"].isin(sel)] if sel else df_mov

    st.plotly_chart(px.bar(df_f, x="NOME_MAT", color="STATUS_ATUAL", title="G3 - Vencidos por Material", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)
    st.plotly_chart(px.bar(df_f, x="FORNECEDOR", color="STATUS_ATUAL", title="G4 - Vencidos por Fornecedor"), use_container_width=True)
    st.plotly_chart(px.scatter(df_f, x="FAB_DT", y="VAL_DT", color="STATUS_ATUAL", size="TOTAL", title="G5 - Fab vs Val", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)

    df_f["DIA"]=df_f["DATA_HORA_DT"].dt.date
    df_f["SEMANA"]=df_f["DATA_HORA_DT"].dt.isocalendar().week.astype(str)
    df_f["MES"]=df_f["DATA_HORA_DT"].dt.to_period("M").astype(str)
    df_f["SEMESTRE"]=df_f["DATA_HORA_DT"].dt.year.astype(str)+"-S"+((df_f["DATA_HORA_DT"].dt.month-1)//6+1).astype(str)
    df_f["ANO"]=df_f["DATA_HORA_DT"].dt.year.astype(str)
    df_saida=df_f[df_f["TIPO"]=="Saida"]

    if not df_saida.empty:
        st.plotly_chart(px.line(df_saida.groupby("DIA")["TOTAL"].sum().reset_index(), x="DIA", y="TOTAL", title="G6 - Consumo Diario", markers=True), use_container_width=True)
        st.plotly_chart(px.bar(df_saida.groupby("SEMANA")["TOTAL"].sum().reset_index(), x="SEMANA", y="TOTAL", title="G7 - Semanal"), use_container_width=True)
        st.plotly_chart(px.bar(df_saida.groupby("MES")["TOTAL"].sum().reset_index(), x="MES", y="TOTAL", title="G8 - Mensal"), use_container_width=True)
        st.plotly_chart(px.bar(df_saida.groupby("SEMESTRE")["TOTAL"].sum().reset_index(), x="SEMESTRE", y="TOTAL", title="G9 - Semestral"), use_container_width=True)
        st.plotly_chart(px.bar(df_saida.groupby("ANO")["TOTAL"].sum().reset_index(), x="ANO", y="TOTAL", title="G10 - Anual"), use_container_width=True)
        st.plotly_chart(px.bar(df_saida.groupby(["MES","NOME_MAT"])["TOTAL"].sum().reset_index(), x="MES", y="TOTAL", color="NOME_MAT", title="G11 - Mensal por Material"), use_container_width=True)

    st.dataframe(df_f.sort_values("VAL_DT")[["IDX","DATA_HORA","TIPO","NOME_MAT","UNIDADE","FORNECEDOR","MARCA","LOTE","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","QTD_PALETE","ENTRADA","TOTAL","LOCAL"]], use_container_width=True)
