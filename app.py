import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox Total", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")

ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"
ARQ_FORN = "fornecedores.csv"

UNIDADES = ["UN","KG","TON","M²","M³","PÇ","LT","CX","SC","MILHEIRO"]

def init():
    if not os.path.exists(ARQ_EMAILS):
        pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","PERFIL":"ADMINISTRADOR","STATUS":"LIBERADO"}]).to_csv(ARQ_EMAILS,index=False)
    if not os.path.exists(ARQ_FORN):
        pd.DataFrame([
            {"ID_FORN":1,"NOME":"FONDU","CNPJ":"","CONTATO":"","MARCA":"FONDU"},
            {"ID_FORN":2,"NOME":"SHINAGAWA","CNPJ":"","CONTATO":"","MARCA":"SHINAGAWA"},
            {"ID_FORN":3,"NOME":"TECNOFIRE","CNPJ":"","CONTATO":"","MARCA":"TECNOFIRE"},
            {"ID_FORN":4,"NOME":"CABOFRAX","CNPJ":"","CONTATO":"","MARCA":"CABOFRAX"},
            {"ID_FORN":5,"NOME":"IBAR","CNPJ":"","CONTATO":"","MARCA":"IBAR"},
            {"ID_FORN":6,"NOME":"BIOLÃ","CNPJ":"","CONTATO":"","MARCA":"BIOLÃ"},
            {"ID_FORN":7,"NOME":"SKAMOL ALUPORO","CNPJ":"","CONTATO":"","MARCA":"SKAMOL ALUPORO"},
            {"ID_FORN":8,"NOME":"MOSCONI AB70","CNPJ":"","CONTATO":"","MARCA":"MOSCONI AB70"},
            {"ID_FORN":9,"NOME":"MAGNESITA","CNPJ":"","CONTATO":"","MARCA":"MAGNESITA"},
            {"ID_FORN":10,"NOME":"ELKEN","CNPJ":"","CONTATO":"","MARCA":"ELKEN"},
            {"ID_FORN":11,"NOME":"CEMAÇO","CNPJ":"","CONTATO":"","MARCA":"CEMAÇO"},
            {"ID_FORN":12,"NOME":"BONY","CNPJ":"","CONTATO":"","MARCA":"BONY"},
        ]).to_csv(ARQ_FORN,index=False)
    if not os.path.exists(ARQ_DADOS):
        mats=[(1,"CIMENTO","SC","VOTORANTIM"),(2,"CARBETO","KG","-"),(3,"ARGAMASSA","KG","-")]
        lista=[]
        for id_,nome,uni,marca in mats:
            lista.append({"ID":id_,"NOME":nome,"UNIDADE":uni,"MARCA":marca,"LOCAL":"BARRACÃO","SALDO":0})
            lista.append({"ID":id_,"NOME":nome,"UNIDADE":uni,"MARCA":marca,"LOCAL":"OFICINA","SALDO":0})
        pd.DataFrame(lista).to_csv(ARQ_DADOS,index=False)
    else:
        # CORREÇÃO DO ERRO - ADICIONA COLUNAS QUE FALTAM
        df=pd.read_csv(ARQ_DADOS)
        if "UNIDADE" not in df.columns: df["UNIDADE"]="UN"
        if "MARCA" not in df.columns: df["MARCA"]="-"
        if "LOCAL" not in df.columns: df["LOCAL"]="BARRACÃO"
        if "SALDO" not in df.columns: df["SALDO"]=0
        df.to_csv(ARQ_DADOS,index=False)
    if not os.path.exists(ARQ_MOV):
        pd.DataFrame(columns=["IDX","DATA_HORA","LOTE","MARCA","FORNECEDOR","VALIDADE","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
    else:
        dfm=pd.read_csv(ARQ_MOV)
        if "MARCA" not in dfm.columns: dfm["MARCA"]="-"
        if "FORNECEDOR" not in dfm.columns: dfm["FORNECEDOR"]="-"
        if "UNIDADE" not in dfm.columns: dfm["UNIDADE"]="UN"
        dfm.to_csv(ARQ_MOV,index=False)
init()

if "logado" not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.title("🔐 Login")
    e=st.text_input("Email").lower().strip()
    s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS)
        u=df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"]==s)]
        if not u.empty:
            st.session_state.logado=True; st.session_state.usuario=e; st.session_state.perfil=u.iloc[0]["PERFIL"]
            # FORÇA RECARREGAR COM COLUNAS CORRIGIDAS
            df_d=pd.read_csv(ARQ_DADOS)
            if "UNIDADE" not in df_d.columns: df_d["UNIDADE"]="UN"
            if "MARCA" not in df_d.columns: df_d["MARCA"]="-"
            st.session_state.dados=df_d.to_dict('records')
            try: st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records')
            except: st.session_state.mov=[]
            st.rerun()
        else: st.error("Inválido")
    st.stop()

agora=datetime.now(FUSO)
df_forn = pd.read_csv(ARQ_FORN) if os.path.exists(ARQ_FORN) else pd.DataFrame()
lista_forn = df_forn["NOME"].tolist() if not df_forn.empty else ["-"]

if st.session_state.perfil=="ADMINISTRADOR":
    with st.sidebar.expander("🏭 FORNECEDORES", expanded=False):
        st.dataframe(df_forn, use_container_width=True, hide_index=True)
        id_f = st.number_input("ID Forn", min_value=1, value=int(df_forn["ID_FORN"].max()+1) if not df_forn.empty else 1, step=1)
        nome_f = st.text_input("Nome fornecedor")
        if st.button("💾 Salvar fornecedor"):
            if nome_f:
                novos=[f for f in pd.read_csv(ARQ_FORN).to_dict('records') if f["ID_FORN"]!=id_f] if os.path.exists(ARQ_FORN) else []
                novos.append({"ID_FORN":id_f,"NOME":nome_f.upper(),"CNPJ":"","CONTATO":"","MARCA":nome_f.upper()})
                pd.DataFrame(novos).to_csv(ARQ_FORN,index=False)
                st.success("Salvo"); st.rerun()

    with st.sidebar.expander("🛠️ MATERIAIS", expanded=True):
        df_temp=pd.DataFrame(st.session_state.dados)
        # GARANTE COLUNAS
        for col in ["UNIDADE","MARCA"]:
            if col not in df_temp.columns: df_temp[col]="-"
        df_mats=df_temp.drop_duplicates(subset=["ID"])[["ID","NOME","UNIDADE","MARCA"]].sort_values("ID")
        st.dataframe(df_mats, use_container_width=True, hide_index=True)
        id_ed=st.selectbox("ID atual", df_mats["ID"].tolist())
        linha=df_mats[df_mats["ID"]==id_ed].iloc[0]
        nid=st.number_input("Novo ID",value=int(id_ed),min_value=1,step=1)
        nno=st.text_input("Nome",value=linha["NOME"])
        nuni=st.selectbox("Unidade",UNIDADES,index=0)
        nmarca=st.selectbox("Marca", lista_forn + ["-","OUTRA"])
        nmarca_custom=st.text_input("Ou digite marca nova")
        marca_final = nmarca_custom.upper() if nmarca_custom else nmarca.upper()
        if st.button("💾 Salvar material"):
            for d in st.session_state.dados:
                if d["ID"]==id_ed:
                    d["ID"]=int(nid); d["NOME"]=nno.upper(); d["UNIDADE"]=nuni; d["MARCA"]=marca_final
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            st.success("Salvo"); st.rerun()

    if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

df_est=pd.DataFrame(st.session_state.dados)
for col in ["UNIDADE","MARCA"]:
    if col not in df_est.columns: df_est[col]="-"
pivot=df_est.pivot_table(index=["ID","NOME","UNIDADE","MARCA"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACÃO" not in pivot.columns: pivot["BARRACÃO"]=0
if "OFICINA" not in pivot.columns: pivot["OFICINA"]=0
pivot["TOTAL GERAL"]=pivot["BARRACÃO"]+pivot["OFICINA"]

st.title(f"📦 TOTAL: {pivot['TOTAL GERAL'].sum():.0f} | {agora.strftime('%d/%m/%Y %H:%M')}")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)

ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa={d["ID"]:(d["NOME"],d["UNIDADE"],d["MARCA"]) for d in st.session_state.dados}
cA,cB,cC,cD=st.columns(4)
id_sel=cA.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa[x][0]}")
local_sel=cB.selectbox("Local", ["BARRACÃO","OFICINA"])
marca_lote=cC.selectbox("Marca lote", lista_forn + ["-"])
forn_lote=cD.selectbox("Fornecedor", lista_forn)

c1,c2,c3,c4=st.columns(4)
lote=c1.text_input("LOTE")
validade=c2.date_input("VALIDADE",value=date.today())
qtd=c3.number_input(f"QTD",value=1.0)
ent=c4.number_input("Paletes",value=1.0)
total_calc=qtd*ent
c5,c6,c7=st.columns(3)
resp=c5.text_input("Responsável",value=st.session_state.usuario)
tipo_sel=c6.selectbox("Tipo", ["Entrada","Saída"])
c7.metric("TOTAL", f"{total_calc:.2f}")

if st.button(f"✅ SALVAR {tipo_sel}", type="primary", use_container_width=True):
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACÃO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    if local_sel=="BARRACÃO" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]+=total_calc; obs="ENTRADA"
    elif local_sel=="OFICINA" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc; obs="TRANSFER"
    elif local_sel=="OFICINA" and tipo_sel=="Saída":
        st.session_state.dados[idx_of]["SALDO"]-=total_calc; obs="SAIDA"
    else:
        st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc; obs="TRANSFER"
    novo_id = (max([m["IDX"] for m in st.session_state.mov]) + 1) if st.session_state.mov else 1
    novo={"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"LOTE":lote.upper(),"MARCA":marca_lote.upper(),"FORNECEDOR":forn_lote.upper(),"VALIDADE":validade.strftime("%d/%m/%Y"),"QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total_calc,"UNIDADE":mapa[id_sel][1],"LOCAL":local_sel,"TIPO":tipo_sel,"ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":resp.upper(),"OBS":obs}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
    st.success(obs); st.rerun()

if st.session_state.mov:
    df_mov=pd.DataFrame(st.session_state.mov).sort_values("IDX", ascending=False)
    st.dataframe(df_mov, use_container_width=True)
