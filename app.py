import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox Barracão + Oficina", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")

ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"

MATERIAIS_INICIAIS = [(1,"CIMENTO"),(2,"CARBETO"),(3,"ARGAMASSA"),(4,"PLACIBAR"),(5,"LÃ ROCHA"),(6,"TIJOLO SEMI SUPRA"),(7,"TIJOLO ISOLANTE"),(8,"TIJOLO REFRATARIO"),(9,"GAXETAS"),(10,"PLACAS BANHO"),(11,"CHAMOTE"),(12,"PASTA FRIA"),(14,"BLOCO LATERAL"),(15,"BLOCO FUNDO"),(16,"BARRAS CATODICAS"),(17,"BLOCOS FUNDO")]

def init():
    if not os.path.exists(ARQ_EMAILS):
        pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","ENTRADA":True,"SAIDA":True,"GRAFICO":True,"STATUS":"LIBERADO","PERFIL":"ADMINISTRADOR"}]).to_csv(ARQ_EMAILS, index=False)
    if not os.path.exists(ARQ_DADOS):
        lista=[]
        for id_,nome in MATERIAIS_INICIAIS:
            lista.append({"ID":id_,"NOME":nome,"LOCAL":"BARRACÃO","SALDO":0})
            lista.append({"ID":id_,"NOME":nome,"LOCAL":"OFICINA","SALDO":0})
        pd.DataFrame(lista).to_csv(ARQ_DADOS, index=False)
    if not os.path.exists(ARQ_MOV):
        pd.DataFrame(columns=["DATA_HORA","LOTE","VALIDADE","QTD_PALETE","ENTRADA","TOTAL","IDADE_MEDIA","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV, index=False)
init()

if "logado" not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.title("🔐 Login - Almox")
    email=st.text_input("Email").lower().strip()
    senha=st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS)
        user=df_e[(df_e["EMAIL"]==email)&(df_e["SENHA"]==senha)&(df_e["STATUS"]=="LIBERADO")]
        if not user.empty:
            st.session_state.logado=True
            st.session_state.usuario=email
            st.session_state.perfil=user.iloc[0]["PERFIL"]
            st.session_state.local_acesso=user.iloc[0]["LOCAL"]
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            try:
                st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records')
            except:
                st.session_state.mov=[]
            st.rerun()
        else: st.error("Login inválido")
    st.stop()

agora=datetime.now(FUSO)

# --- SIDEBAR ADMIN ---
if st.session_state.perfil=="ADMINISTRADOR":
    with st.sidebar.expander("🛠️ EDITAR MATERIAIS - ID e NOME", expanded=True):
        df_estoque_temp=pd.DataFrame(st.session_state.dados)
        df_mats = df_estoque_temp.drop_duplicates(subset=["ID","NOME"])[["ID","NOME"]].sort_values("ID")
        st.dataframe(df_mats, use_container_width=True, hide_index=True)

        st.divider()
        st.write("**1. Editar ID e NOME**")
        id_editar = st.selectbox("ID atual", df_mats["ID"].tolist())
        nome_atual = df_mats[df_mats["ID"]==id_editar]["NOME"].values[0]
        col_id, col_nome = st.columns([1,2])
        novo_id_edit = col_id.number_input("Novo ID", min_value=1, step=1, value=int(id_editar))
        novo_nome_edit = col_nome.text_input("Novo nome", value=nome_atual)
        if st.button("💾 Salvar ID e Nome"):
            if novo_id_edit!=id_editar and novo_id_edit in df_mats["ID"].tolist():
                st.error(f"ID {novo_id_edit} já existe!")
            else:
                for d in st.session_state.dados:
                    if d["ID"]==id_editar:
                        d["ID"]=int(novo_id_edit)
                        d["NOME"]=novo_nome_edit.upper()
                pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS, index=False)
                st.success(f"Alterado {id_editar}->{novo_id_edit} | {novo_nome_edit}"); st.rerun()

        st.divider()
        st.write("**2. Adicionar novo material**")
        novo_id = st.number_input("Novo ID", min_value=1, step=1, value=int(df_mats["ID"].max()+1), key="novo_id_add")
        novo_mat_nome = st.text_input("Nome novo material", key="novo_nome_add")
        if st.button("➕ Adicionar material"):
            if novo_mat_nome:
                if novo_id in df_mats["ID"].tolist():
                    st.error("ID já existe")
                else:
                    st.session_state.dados.append({"ID":novo_id,"NOME":novo_mat_nome.upper(),"LOCAL":"BARRACÃO","SALDO":0})
                    st.session_state.dados.append({"ID":novo_id,"NOME":novo_mat_nome.upper(),"LOCAL":"OFICINA","SALDO":0})
                    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS, index=False)
                    st.success("Adicionado"); st.rerun()

        st.divider()
        st.write("**3. Apagar material**")
        id_apagar = st.selectbox("ID para APAGAR", df_mats["ID"].tolist(), key="apagar")
        if st.button("🗑️ Apagar definitivo"):
            st.session_state.dados = [d for d in st.session_state.dados if d["ID"]!=id_apagar]
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS, index=False)
            st.warning(f"ID {id_apagar} apagado"); st.rerun()

    with st.sidebar.expander("🔑 CONTROLE DE ACESSO"):
        ne=st.text_input("Email novo").lower().strip()
        ns=st.text_input("Senha nova", type="password")
        loc=st.selectbox("Local acesso", ["BARRACÃO","OFICINA","AMBOS"])
        if st.button("Cadastrar acesso"):
            if "@" in ne and ns:
                df_e=pd.read_csv(ARQ_EMAILS)
                df_e=df_e[~((df_e["EMAIL"]==ne)&(df_e["LOCAL"]==loc))]
                df_e=pd.concat([df_e,pd.DataFrame([{"EMAIL":ne,"SENHA":ns,"LOCAL":loc,"ENTRADA":True,"SAIDA":True,"GRAFICO":True,"STATUS":"LIBERADO","PERFIL":"OPERADOR"}])],ignore_index=True)
                df_e.to_csv(ARQ_EMAILS,index=False)
                st.success("Liberado")

    if st.sidebar.button("🚪 Sair"):
        st.session_state.clear(); st.rerun()

# --- ESTOQUE ---
df_estoque=pd.DataFrame(st.session_state.dados)
pivot=df_estoque.pivot_table(index=["ID","NOME"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACÃO" not in pivot.columns: pivot["BARRACÃO"]=0
if "OFICINA" not in pivot.columns: pivot["OFICINA"]=0
pivot["TOTAL GERAL"]=pivot["BARRACÃO"]+pivot["OFICINA"]

st.title(f"📦 TOTAL GERAL: {pivot['TOTAL GERAL'].sum():.0f} | {agora.strftime('%d/%m/%Y %H:%M')} Brasília")
st.caption(f"Logado: {st.session_state.usuario} | BARRACÃO + OFICINA = TOTAL GERAL")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)

st.divider()
# --- LANÇAMENTO ---
ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
nomes={d["ID"]:d["NOME"] for d in st.session_state.dados}

c_sel1,c_sel2=st.columns(2)
id_sel=c_sel1.selectbox("Material (ID)", ids, format_func=lambda x: f"{x} - {nomes[x]}")
local_sel=c_sel2.selectbox("Local lançamento", ["BARRACÃO","OFICINA"])

c1,c2,c3,c4=st.columns(4)
lote=c1.text_input("LOTE")
validade=c2.date_input("VALIDADE", value=date.today())
qtd=c3.number_input("QTD/PALETE", min_value=0.0, value=1.0, step=1.0)
ent=c4.number_input("ENTRADA (nº paletes)", min_value=0.0, value=1.0, step=1.0)

total_calc=qtd*ent
idade_media = 0

c5,c6,c7=st.columns(3)
resp=c5.text_input("Responsável", value=st.session_state.usuario)
tipo_sel=c6.selectbox("Tipo", ["Entrada","Saída"])
c7.metric("TOTAL", f"{total_calc:.0f}")
c7.metric("IDADE MÉDIA (dias)", "0 no lançamento")

if st.button(f"✅ SALVAR {tipo_sel} em {local_sel}", type="primary", use_container_width=True):
    if not lote:
        st.error("Preencha o LOTE")
    else:
        idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACÃO"),None)
        idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
        obs=""
        if local_sel=="BARRACÃO" and tipo_sel=="Entrada":
            st.session_state.dados[idx_ba]["SALDO"]+=total_calc
            obs=f"ENTRADA REAL BARRACÃO: +{total_calc} no TOTAL GERAL"
        elif local_sel=="OFICINA" and tipo_sel=="Entrada":
            st.session_state.dados[idx_ba]["SALDO"]-=total_calc
            st.session_state.dados[idx_of]["SALDO"]+=total_calc
            obs=f"TRANSFER AUTO BARRACÃO->OFICINA | TOTAL GERAL não muda"
        elif local_sel=="OFICINA" and tipo_sel=="Saída":
            st.session_state.dados[idx_of]["SALDO"]-=total_calc
            obs=f"CONSUMO OFICINA: -{total_calc} do TOTAL GERAL"
        else: # Saída Barracão vira transferência
            st.session_state.dados[idx_ba]["SALDO"]-=total_calc
            st.session_state.dados[idx_of]["SALDO"]+=total_calc
            obs="TRANSFER AUTO"

        novo={"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"LOTE":lote.upper(),"VALIDADE":validade.strftime("%d/%m/%Y"),"QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total_calc,"IDADE_MEDIA":idade_media,"LOCAL":local_sel,"TIPO":tipo_sel,"ID_MAT":id_sel,"NOME_MAT":nomes[id_sel],"RESPONSAVEL":resp.upper(),"OBS":obs}
        st.session_state.mov.append(novo)
        pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS, index=False)
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False)
        st.success(obs)
        st.rerun()

# --- GRAFICOS ---
if st.session_state.mov:
    st.divider()
    st.subheader("📊 Gráficos + Registros")
    df_mov=pd.DataFrame(st.session_state.mov)
    df_mov["DATA_DT"]=pd.to_datetime(df_mov["DATA_HORA"], dayfirst=True, errors='coerce')
    df_mov["VALIDADE_DT"]=pd.to_datetime(df_mov["VALIDADE"], dayfirst=True, errors='coerce')
    hoje=pd.Timestamp.now()

    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACÃO","OFICINA"], barmode="group", title="Saldo Barracão vs Oficina"), use_container_width=True)

    df_mov["DIAS_VENC"]=(df_mov["VALIDADE_DT"]-hoje).dt.days
    venc_status=[]
    for _,r in df_mov.iterrows():
        if r["DIAS_VENC"]<0: venc_status.append("Vencido")
        elif r["DIAS_VENC"]<=30: venc_status.append("A vencer 30d")
        else: venc_status.append("OK")
    df_mov["STATUS_VAL"]=venc_status
    c2.plotly_chart(px.histogram(df_mov, x="STATUS_VAL", title="Vencidos x A Vencer"), use_container_width=True)

    abc=df_mov.groupby("NOME_MAT")["TOTAL"].sum().reset_index().sort_values("TOTAL", ascending=False)
    abc["%"]=abc["TOTAL"]/abc["TOTAL"].sum()*100
    abc["% ACUM"]=abc["%"].cumsum()
    abc["CLASSE"]=abc["% ACUM"].apply(lambda x: "A" if x<=80 else "B" if x<=95 else "C")
    st.plotly_chart(px.bar(abc, x="NOME_MAT", y="TOTAL", color="CLASSE", title="Curva ABC - Consumo"), use_container_width=True)

    st.dataframe(df_mov.sort_values("DATA_DT", ascending=False), use_container_width=True)
