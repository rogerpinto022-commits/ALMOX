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
            {"ID_FORN":1,"NOME":"VOTORANTIM","CNPJ":"","CONTATO":"","MARCA":"VOTORANTIM"},
            {"ID_FORN":2,"NOME":"IBAR","CNPJ":"","CONTATO":"","MARCA":"IBAR"},
            {"ID_FORN":3,"NOME":"SAINT-GOBAIN","CNPJ":"","CONTATO":"","MARCA":"SAINT-GOBAIN"},
        ]).to_csv(ARQ_FORN,index=False)
    if not os.path.exists(ARQ_DADOS):
        mats=[(1,"CIMENTO","SC","VOTORANTIM"),(2,"CARBETO","KG","-"),(3,"ARGAMASSA","KG","-"),(4,"PLACIBAR","PÇ","-"),(5,"LÃ ROCHA","M²","-"),(6,"TIJOLO SEMI SUPRA","PÇ","IBAR"),(7,"TIJOLO ISOLANTE","PÇ","IBAR"),(8,"TIJOLO REFRATARIO","PÇ","SAINT-GOBAIN"),(9,"GAXETAS","PÇ","-"),(10,"PLACAS BANHO","PÇ","-"),(11,"CHAMOTE","KG","-"),(12,"PASTA FRIA","KG","-"),(14,"BLOCO LATERAL","PÇ","-"),(15,"BLOCO FUNDO","PÇ","-"),(16,"BARRAS CATODICAS","PÇ","-"),(17,"BLOCOS FUNDO","PÇ","-")]
        lista=[]
        for id_,nome,uni,marca in mats:
            lista.append({"ID":id_,"NOME":nome,"UNIDADE":uni,"MARCA":marca,"LOCAL":"BARRACÃO","SALDO":0})
            lista.append({"ID":id_,"NOME":nome,"UNIDADE":uni,"MARCA":marca,"LOCAL":"OFICINA","SALDO":0})
        pd.DataFrame(lista).to_csv(ARQ_DADOS,index=False)
    if not os.path.exists(ARQ_MOV):
        pd.DataFrame(columns=["IDX","DATA_HORA","LOTE","MARCA","FORNECEDOR","VALIDADE","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
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
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            st.session_state.forns=pd.read_csv(ARQ_FORN).to_dict('records') if os.path.exists(ARQ_FORN) else []
            try: st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records')
            except: st.session_state.mov=[]
            st.rerun()
        else: st.error("Inválido")
    st.stop()

agora=datetime.now(FUSO)
# CARREGA FORNECEDORES
df_forn = pd.DataFrame(pd.read_csv(ARQ_FORN)) if os.path.exists(ARQ_FORN) else pd.DataFrame()
lista_forn = df_forn["NOME"].tolist() if not df_forn.empty else ["-"]

if st.session_state.perfil=="ADMINISTRADOR":
    # --- EDITAR FORNECEDORES ---
    with st.sidebar.expander("🏭 FORNECEDORES - EDITAR/NOVO", expanded=False):
        st.dataframe(df_forn, use_container_width=True, hide_index=True)
        st.write("**Novo / Editar Fornecedor**")
        id_f = st.number_input("ID Forn", min_value=1, value=int(df_forn["ID_FORN"].max()+1) if not df_forn.empty else 1, step=1)
        nome_f = st.text_input("Nome fornecedor")
        cnpj_f = st.text_input("CNPJ")
        cont_f = st.text_input("Contato / Tel")
        marca_f = st.text_input("Marca que fornece")
        c1,c2=st.columns(2)
        if c1.button("💾 Salvar fornecedor"):
            if nome_f:
                # remove se já existe mesmo ID
                novos=[f for f in pd.read_csv(ARQ_FORN).to_dict('records') if f["ID_FORN"]!=id_f] if os.path.exists(ARQ_FORN) else []
                novos.append({"ID_FORN":id_f,"NOME":nome_f.upper(),"CNPJ":cnpj_f,"CONTATO":cont_f,"MARCA":marca_f.upper()})
                pd.DataFrame(novos).to_csv(ARQ_FORN,index=False)
                st.success(f"Fornecedor {nome_f} salvo"); st.rerun()
        if c2.button("🗑️ Apagar fornecedor"):
            novos=[f for f in pd.read_csv(ARQ_FORN).to_dict('records') if f["ID_FORN"]!=id_f]
            pd.DataFrame(novos).to_csv(ARQ_FORN,index=False)
            st.warning("Apagado"); st.rerun()

    with st.sidebar.expander("🛠️ MATERIAIS - ID/NOME/UNID/MARCA", expanded=True):
        df_temp=pd.DataFrame(st.session_state.dados)
        df_mats=df_temp.drop_duplicates(subset=["ID"])[["ID","NOME","UNIDADE","MARCA"]].sort_values("ID")
        st.dataframe(df_mats, use_container_width=True, hide_index=True)
        id_ed=st.selectbox("ID atual", df_mats["ID"].tolist())
        linha=df_mats[df_mats["ID"]==id_ed].iloc[0]
        nid=st.number_input("Novo ID",value=int(id_ed),min_value=1,step=1)
        nno=st.text_input("Nome",value=linha["NOME"])
        c3,c4=st.columns(2)
        nuni=c3.selectbox("Unidade",UNIDADES,index=UNIDADES.index(linha["UNIDADE"]) if linha["UNIDADE"] in UNIDADES else 0)
        # marca vem dos fornecedores
        opcoes_marca = lista_forn + ["-","OUTRA"]
        nmarca=c4.selectbox("Marca/Fornecedor", opcoes_marca, index=0)
        nmarca_custom=st.text_input("Ou digite marca nova")
        marca_final = nmarca_custom.upper() if nmarca_custom else nmarca.upper()
        if st.button("💾 Salvar material"):
            for d in st.session_state.dados:
                if d["ID"]==id_ed:
                    d["ID"]=int(nid); d["NOME"]=nno.upper(); d["UNIDADE"]=nuni; d["MARCA"]=marca_final
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            st.success("Salvo"); st.rerun()

        st.divider()
        aid=st.number_input("ID novo material",value=int(df_mats["ID"].max()+1),min_value=1,step=1,key="aid")
        ano=st.text_input("Nome novo",key="ano")
        ca3,ca4=st.columns(2)
        auni=ca3.selectbox("Unid.",UNIDADES,key="auni")
        amarca=ca4.selectbox("Marca",opcoes_marca,key="amarca")
        if st.button("➕ Adicionar material"):
            if ano:
                st.session_state.dados.append({"ID":aid,"NOME":ano.upper(),"UNIDADE":auni,"MARCA":amarca if (marca:=amarca.upper()) else "-", "LOCAL":"BARRACÃO","SALDO":0})
                st.session_state.dados.append({"ID":aid,"NOME":ano.upper(),"UNIDADE":auni,"MARCA": marca,"LOCAL":"OFICINA","SALDO":0})
                pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
                st.rerun()

    if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

# ESTOQUE
df_est=pd.DataFrame(st.session_state.dados)
pivot=df_est.pivot_table(index=["ID","NOME","UNIDADE","MARCA"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACÃO" not in pivot.columns: pivot["BARRACÃO"]=0
if "OFICINA" not in pivot.columns: pivot["OFICINA"]=0
pivot["TOTAL GERAL"]=pivot["BARRACÃO"]+pivot["OFICINA"]
st.title(f"📦 TOTAL: {pivot['TOTAL GERAL'].sum():.0f} | {agora.strftime('%d/%m/%Y %H:%M')}")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)
c1,c2=st.columns(2)
c1.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACÃO","OFICINA"], barmode="group", title="ESTOQUE REAL"), use_container_width=True)
c2.plotly_chart(px.pie(pivot, values="TOTAL GERAL", names="MARCA", title="POR MARCA/FORNECEDOR"), use_container_width=True)

st.divider()
ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa={d["ID"]:(d["NOME"],d["UNIDADE"],d["MARCA"]) for d in st.session_state.dados}

cA,cB,cC,cD=st.columns(4)
id_sel=cA.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa[x][0]}")
local_sel=cB.selectbox("Local", ["BARRACÃO","OFICINA"])
marca_lote=cC.selectbox("Marca lote", lista_forn + ["-"], index=0)
forn_lote=cD.selectbox("Fornecedor", lista_forn, index=0)

c1,c2,c3,c4=st.columns(4)
lote=c1.text_input("LOTE")
validade=c2.date_input("VALIDADE",value=date.today())
qtd=c3.number_input(f"QTD ({mapa[id_sel][1]})",value=1.0)
ent=c4.number_input("Paletes",value=1.0)
total_calc=qtd*ent
c5,c6,c7=st.columns(3)
resp=c5.text_input("Responsável",value=st.session_state.usuario)
tipo_sel=c6.selectbox("Tipo", ["Entrada","Saída"])
c7.metric("TOTAL", f"{total_calc:.2f} {mapa[id_sel][1]}")

if st.button(f"✅ SALVAR {tipo_sel}", type="primary", use_container_width=True):
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACÃO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    if local_sel=="BARRACÃO" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]+=total_calc; obs="ENTRADA BARRACÃO"
    elif local_sel=="OFICINA" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc; obs="TRANSFER B->O"
    elif local_sel=="OFICINA" and tipo_sel=="Saída":
        st.session_state.dados[idx_of]["SALDO"]-=total_calc; obs="SAÍDA OFICINA"
    else:
        st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc; obs="TRANSFER"

    novo_id = (max([m["IDX"] for m in st.session_state.mov]) + 1) if st.session_state.mov else 1
    novo={"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"LOTE":lote.upper(),"MARCA":marca_lote.upper(),"FORNECEDOR":forn_lote.upper(),"VALIDADE":validade.strftime("%d/%m/%Y"),"QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total_calc,"UNIDADE":mapa[id_sel][1],"LOCAL":local_sel,"TIPO":tipo_sel,"ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":resp.upper(),"OBS":obs}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
    st.success(obs); st.rerun()

if st.session_state.mov:
    st.divider()
    st.subheader("📋 Registros")
    df_mov=pd.DataFrame(st.session_state.mov).sort_values("IDX", ascending=False)
    st.dataframe(df_mov, use_container_width=True)
    st.plotly_chart(px.bar(df_mov, x="NOME_MAT", y="TOTAL", color="FORNECEDOR", barmode="group", title="Consumo por FORNECEDOR"), use_container_width=True)
    id_del=st.selectbox("IDX apagar e estornar", df_mov["IDX"].tolist())
    if st.button("🗑️ APAGAR E ESTORNAR", type="primary"):
        mov_del=next((m for m in st.session_state.mov if m["IDX"]==id_del), None)
        if mov_del:
            idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==mov_del["ID_MAT"] and d["LOCAL"]=="BARRACÃO"),None)
            idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==mov_del["ID_MAT"] and d["LOCAL"]=="OFICINA"),None)
            tot=mov_del["TOTAL"]
            if mov_del["LOCAL"]=="BARRACÃO" and mov_del["TIPO"]=="Entrada": st.session_state.dados[idx_ba]["SALDO"]-=tot
            elif mov_del["LOCAL"]=="OFICINA" and mov_del["TIPO"]=="Entrada":
                st.session_state.dados[idx_ba]["SALDO"]+=tot; st.session_state.dados[idx_of]["SALDO"]-=tot
            elif mov_del["LOCAL"]=="OFICINA" and mov_del["TIPO"]=="Saída": st.session_state.dados[idx_of]["SALDO"]+=tot
            else: st.session_state.dados[idx_ba]["SALDO"]+=tot; st.session_state.dados[idx_of]["SALDO"]-=tot
            st.session_state.mov=[m for m in st.session_state.mov if m["IDX"]!=id_del]
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
            st.warning("Apagado"); st.rerun()
