import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox 11 Graficos", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")
ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"

# AUTO LIMPA MOV VELHO
if os.path.exists(ARQ_MOV):
    try:
        df_old = pd.read_csv(ARQ_MOV)
        if "DATA_FAB" not in df_old.columns or "FORNECEDOR" not in df_old.columns:
            os.remove(ARQ_MOV)
    except:
        try: os.remove(ARQ_MOV)
        except: pass

if not os.path.exists(ARQ_DADOS):
    pd.DataFrame([
        {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"VOTORAN","LOCAL":"BARRACAO","SALDO":100,"VALIDADE_PADRAO":90,"FORNECEDOR":"LEROY"},
        {"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"VOTORAN","LOCAL":"OFICINA","SALDO":0,"VALIDADE_PADRAO":90,"FORNECEDOR":"LEROY"},
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
            st.session_state.logado=True
            st.session_state.usuario=e
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            df_m=pd.read_csv(ARQ_MOV)
            st.session_state.mov=[] if df_m.empty else df_m.to_dict('records')
            st.rerun()
    st.stop()

agora=datetime.now(FUSO)
hoje=date.today()
if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

df_est=pd.DataFrame(st.session_state.dados)
pivot=df_est.pivot_table(index=["ID","NOME"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
for c in ["BARRACAO","OFICINA"]:
    if c not in pivot.columns: pivot[c]=0
pivot["TOTAL"]=pivot["BARRACAO"]+pivot["OFICINA"]
st.title(f"TOTAL: {pivot['TOTAL'].sum():.0f}")
st.dataframe(pivot, use_container_width=True)

# GRAFICO 1 e 2
col1,col2=st.columns(2)
with col1:
    st.subheader("Grafico 1 - Estoque por Local")
    st.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACAO","OFICINA"], barmode="group"), use_container_width=True)
with col2:
    st.subheader("Grafico 2 - Pizza Total")
    st.plotly_chart(px.pie(pivot, names="NOME", values="TOTAL"), use_container_width=True)

# LANCAMENTO
st.divider()
ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa={d["ID"]:(d["NOME"],d["UNIDADE"],d.get("VALIDADE_PADRAO",90),d.get("MARCA","-"),d.get("FORNECEDOR","-")) for d in st.session_state.dados}
id_sel=st.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa[x][0]}")
cA,cB,cC=st.columns(3)
marca=cA.text_input("MARCA", value=mapa[id_sel][3])
fornecedor=cB.text_input("FORNECEDOR", value=mapa[id_sel][4])
lote=cC.text_input("LOTE")
c1,c2,c3,c4,c5,c6=st.columns(6)
local_sel=c1.selectbox("Local", ["BARRACAO","OFICINA"])
data_fab=c2.date_input("FAB", value=hoje)
validade=c3.date_input("VALIDADE", value=data_fab+timedelta(days=int(mapa[id_sel][2])))
qtd=c4.number_input("QTD",value=1.0)
ent=c5.number_input("PALETES",value=1.0)
tipo=c6.selectbox("TIPO",["Entrada","Saida"])

dias_rest=(validade-hoje).days
status="VENCIDO" if dias_rest<0 else "A VENCER 30d" if dias_rest<=30 else "A VENCER 90d" if dias_rest<=90 else "OK"
st.info(f"{dias_rest} dias - {status} | {fornecedor}")

if st.button(f"SALVAR {status}", type="primary", use_container_width=True):
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACAO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    total=qtd*ent
    if tipo=="Entrada":
        if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]+=total
        else: st.session_state.dados[idx_ba]["SALDO"]-=total; st.session_state.dados[idx_of]["SALDO"]+=total
    else:
        if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]-=total
        else: st.session_state.dados[idx_of]["SALDO"]-=total

    novo_id=max([int(m.get("IDX",0)) for m in st.session_state.mov])+1 if st.session_state.mov else 1
    novo={"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_FAB":data_fab.strftime("%d/%m/%Y"),"VALIDADE":validade.strftime("%d/%m/%Y"),"DIAS_VALIDADE":(validade-data_fab).days,"STATUS_VAL":status,"LOTE":lote.upper(),"MARCA":marca.upper(),"FORNECEDOR":fornecedor.upper(),"QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total,"UNIDADE":mapa[id_sel][1],"LOCAL":local_sel,"TIPO":tipo,"ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":st.session_state.usuario,"OBS":status}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
    st.rerun()

# TODOS OS GRAFICOS
st.divider()
st.header("📅 VALIDADE E CONSUMO")

if not st.session_state.mov:
    st.warning("Lance lotes para ver os graficos 3 ao 11")
else:
    df_mov=pd.DataFrame(st.session_state.mov)
    df_mov["VAL_DT"]=pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
    df_mov["FAB_DT"]=pd.to_datetime(df_mov["DATA_FAB"], format="%d/%m/%Y", errors='coerce')
    df_mov["DATA_HORA_DT"]=pd.to_datetime(df_mov["DATA_HORA"], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    df_mov["DIAS_REST"]=(df_mov["VAL_DT"]-pd.Timestamp(hoje)).dt.days
    def stt(d):
        if pd.isna(d): return "SEM"
        if d<0: return "VENCIDO"
        if d<=30: return "A VENCER 30d"
        if d<=90: return "A VENCER 90d"
        return "OK"
    df_mov["STATUS_ATUAL"]=df_mov["DIAS_REST"].apply(stt)

    # FILTROS
    lista_mat=sorted(df_mov["NOME_MAT"].dropna().unique().tolist())
    sel=st.multiselect("FILTRO MATERIAL (afeta todos):", options=lista_mat, default=lista_mat)
    df_f=df_mov[df_mov["NOME_MAT"].isin(sel)] if sel else df_mov

    # GRAFICO 3 e 4
    c1,c2=st.columns(2)
    with c1:
        st.subheader("Grafico 3 - Vencidos por Material")
        st.plotly_chart(px.bar(df_f, x="NOME_MAT", color="STATUS_ATUAL", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)
    with c2:
        st.subheader("Grafico 4 - Vencidos por Fornecedor")
        st.plotly_chart(px.bar(df_f, x="FORNECEDOR", color="STATUS_ATUAL", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)

    # GRAFICO 5
    st.subheader("Grafico 5 - Fab vs Val")
    st.plotly_chart(px.scatter(df_f, x="FAB_DT", y="VAL_DT", color="FORNECEDOR", size="TOTAL", hover_data=["LOTE"]), use_container_width=True)

    # PREPARA CONSUMO
    df_f["DIA"]=df_f["DATA_HORA_DT"].dt.date
    df_f["SEMANA"]=df_f["DATA_HORA_DT"].dt.isocalendar().week
    df_f["MES"]=df_f["DATA_HORA_DT"].dt.to_period("M").astype(str)
    df_f["SEMESTRE"]=df_f["DATA_HORA_DT"].dt.year.astype(str) + "-S" + ((df_f["DATA_HORA_DT"].dt.month-1)//6+1).astype(str)
    df_f["ANO"]=df_f["DATA_HORA_DT"].dt.year

    df_saida=df_f[df_f["TIPO"]=="Saida"]
    if df_saida.empty:
        st.info("Ainda sem Saidas. Lance uma Saida para ver os graficos de consumo 6 ao 10")
    else:
        # GRAFICO 6 - DIARIO
        st.subheader("Grafico 6 - Consumo Diario")
        g_dia=df_saida.groupby("DIA")["TOTAL"].sum().reset_index()
        st.plotly_chart(px.line(g_dia, x="DIA", y="TOTAL", markers=True, title="Consumo Diario"), use_container_width=True)

        # GRAFICO 7 - SEMANAL
        st.subheader("Grafico 7 - Consumo Semanal")
        g_sem=df_saida.groupby("SEMANA")["TOTAL"].sum().reset_index()
        st.plotly_chart(px.bar(g_sem, x="SEMANA", y="TOTAL", title="Consumo Semanal"), use_container_width=True)

        # GRAFICO 8 - MENSAL
        st.subheader("Grafico 8 - Consumo Mensal")
        g_mes=df_saida.groupby("MES")["TOTAL"].sum().reset_index()
        st.plotly_chart(px.bar(g_mes, x="MES", y="TOTAL", title="Consumo Mensal"), use_container_width=True)

        # GRAFICO 9 - SEMESTRAL
        st.subheader("Grafico 9 - Consumo Semestral")
        g_semest=df_saida.groupby("SEMESTRE")["TOTAL"].sum().reset_index()
        st.plotly_chart(px.bar(g_semest, x="SEMESTRE", y="TOTAL", title="Consumo Semestral"), use_container_width=True)

        # GRAFICO 10 - ANUAL
        st.subheader("Grafico 10 - Consumo Anual")
        g_ano=df_saida.groupby("ANO")["TOTAL"].sum().reset_index()
        st.plotly_chart(px.bar(g_ano, x="ANO", y="TOTAL", title="Consumo Anual"), use_container_width=True)

        # GRAFICO 11 - CONSUMO POR MATERIAL MENSAL
        st.subheader("Grafico 11 - Consumo Mensal por Material")
        g_mat_mes=df_saida.groupby(["MES","NOME_MAT"])["TOTAL"].sum().reset_index()
        st.plotly_chart(px.bar(g_mat_mes, x="MES", y="TOTAL", color="NOME_MAT", barmode="group", title="Consumo Mensal por Material"), use_container_width=True)

    st.dataframe(df_f.sort_values("VAL_DT")[["IDX","DATA_HORA","NOME_MAT","FORNECEDOR","LOTE","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","TOTAL","TIPO","LOCAL"]], use_container_width=True)
