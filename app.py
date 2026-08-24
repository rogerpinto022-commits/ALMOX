import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")

ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"

MATERIAIS = [(1,"CIMENTO"),(2,"CARBETO"),(3,"ARGAMASSA"),(4,"PLACIBAR"),(5,"LÃ ROCHA"),(6,"TIJOLO SEMI SUPRA"),(7,"TIJOLO ISOLANTE"),(8,"TIJOLO REFRATARIO"),(9,"GAXETAS"),(10,"PLACAS BANHO"),(11,"CHAMOTE"),(12,"PASTA FRIA"),(14,"BLOCO LATERAL"),(15,"BLOCO FUNDO"),(16,"BARRAS CATODICAS"),(17,"BLOCOS FUNDO")]

def init():
    if not os.path.exists(ARQ_EMAILS):
        pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","ENTRADA":True,"SAIDA":True,"GRAFICO":True,"STATUS":"LIBERADO","PERFIL":"ADMINISTRADOR"}]).to_csv(ARQ_EMAILS, index=False)
    if not os.path.exists(ARQ_DADOS):
        lista=[]
        for id_,nome in MATERIAIS:
            lista.append({"ID":id_,"NOME":nome,"LOCAL":"BARRACÃO","SALDO":0})
            lista.append({"ID":id_,"NOME":nome,"LOCAL":"OFICINA","SALDO":0})
        pd.DataFrame(lista).to_csv(ARQ_DADOS, index=False)
    if not os.path.exists(ARQ_MOV):
        pd.DataFrame(columns=["DATA_HORA","LOTE","VALIDADE","QTD_PALETE","ENTRADA","TOTAL","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV, index=False)
init()

if "logado" not in st.session_state:
    st.session_state.logado=False

if not st.session_state.logado:
    st.title("Login")
    email=st.text_input("Email").lower().strip()
    senha=st.text_input("Senha", type="password")
    if st.button("Entrar"):
        df_e=pd.read_csv(ARQ_EMAILS)
        user=df_e[(df_e["EMAIL"]==email)&(df_e["SENHA"]==senha)]
        if not user.empty:
            st.session_state.logado=True
            st.session_state.usuario=email
            st.session_state.perfil=user.iloc[0]["PERFIL"]
            st.session_state.local_acesso=user.iloc[0]["LOCAL"]
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records') if os.path.exists(ARQ_MOV) else []
            st.rerun()
        else:
            st.error("Login inválido")
    st.stop()

agora=datetime.now(FUSO)
df_estoque=pd.DataFrame(st.session_state.dados)
pivot=df_estoque.pivot_table(index=["ID","NOME"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACÃO" not in pivot.columns: pivot["BARRACÃO"]=0
if "OFICINA" not in pivot.columns: pivot["OFICINA"]=0
pivot["TOTAL GERAL"]=pivot["BARRACÃO"]+pivot["OFICINA"]

st.title(f"TOTAL GERAL: {pivot['TOTAL GERAL'].sum()} | {agora.strftime('%d/%m/%Y %H:%M')} Brasília - {st.session_state.usuario}")
st.dataframe(pivot, use_container_width=True)

# Lançamento
st.divider()
ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
nomes={d["ID"]:d["NOME"] for d in st.session_state.dados}
id_sel=st.selectbox("Material", ids, format_func=lambda x: f"{x}-{nomes[x]}")
c1,c2,c3,c4=st.columns(4)
lote=c1.text_input("LOTE")
validade=c2.date_input("VALIDADE")
qtd=c3.number_input("QTD/PALETE", value=1.0)
ent=c4.number_input("ENTRADA paletes", value=1.0)
resp=st.text_input("Responsável", value=st.session_state.usuario)
local_sel=st.selectbox("Local", ["BARRACÃO","OFICINA"])
tipo_sel=st.selectbox("Tipo", ["Entrada","Saída"])

if st.button("Salvar", type="primary"):
    total=qtd*ent
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACÃO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    obs=""
    if local_sel=="BARRACÃO" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]+=total
        obs="ENTRADA REAL BARRACÃO - aumenta TOTAL GERAL"
    elif local_sel=="OFICINA" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]-=total
        st.session_state.dados[idx_of]["SALDO"]+=total
        obs="TRANSFER AUTO BARRACÃO->OFICINA - Total não muda"
    elif local_sel=="OFICINA" and tipo_sel=="Saída":
        st.session_state.dados[idx_of]["SALDO"]-=total
        obs="SAÍDA REAL OFICINA - desconta TOTAL GERAL"
    else:
        st.session_state.dados[idx_ba]["SALDO"]-=total
        st.session_state.dados[idx_of]["SALDO"]+=total
        obs="TRANSFER AUTO"

    novo={"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"LOTE":lote,"VALIDADE":validade.strftime("%d/%m/%Y"),"QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total,"LOCAL":local_sel,"TIPO":tipo_sel,"ID_MAT":id_sel,"NOME_MAT":nomes[id_sel],"RESPONSAVEL":resp,"OBS":obs}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS, index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False)
    st.success(obs)
    st.rerun()

# Gráficos
if st.session_state.mov:
    df_mov=pd.DataFrame(st.session_state.mov)
    st.plotly_chart(px.bar(df_mov, x="NOME_MAT", y="TOTAL", color="LOCAL", barmode="group", title="Estoque Barracão vs Oficina"), use_container_width=True)
    st.plotly_chart(px.pie(pivot, values="TOTAL GERAL", names="NOME", title="Curva ABC - TOTAL GERAL"), use_container_width=True)
    st.dataframe(df_mov, use_container_width=True)
