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
        mats=[(1,"CIMENTO","SC","VOTORANTIM"),(2,"CARBETO","KG","-"),(3,"ARGAMASSA","KG","-"),(4,"PLACIBAR","PÇ","-"),(5,"LÃ ROCHA","M²","-"),(6,"TIJOLO SEMI SUPRA","PÇ","IBAR"),(7,"TIJOLO ISOLANTE","PÇ","IBAR"),(8,"TIJOLO REFRATARIO","PÇ","SAINT-GOBAIN"),(9,"GAXETAS","PÇ","-"),(10,"PLACAS BANHO","PÇ","-"),(11,"CHAMOTE","KG","-"),(12,"PASTA FRIA","KG","-")]
        lista=[]
        for id_,nome,uni,marca in mats:
            lista.append({"ID":id_,"NOME":nome,"UNIDADE":uni,"MARCA":marca,"LOCAL":"BARRACÃO","SALDO":0})
            lista.append({"ID":id_,"NOME":nome,"UNIDADE":uni,"MARCA":marca,"LOCAL":"OFICINA","SALDO":0})
        pd.DataFrame(lista).to_csv(ARQ_DADOS,index=False)
    else:
        df=pd.read_csv(ARQ_DADOS)
        if "UNIDADE" not in df.columns: df["UNIDADE"]="UN"
        if "MARCA" not in df.columns: df["MARCA"]="-"
        df.to_csv(ARQ_DADOS,index=False)
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
            df_d=pd.read_csv(ARQ_DADOS)
            if "UNIDADE" not in df_d.columns: df_d["UNIDADE"]="UN"
            if "MARCA" not in df_d.columns: df_d["MARCA"]="-"
            st.session_state.dados=df_d.to_dict('records')
            try:
                df_m=pd.read_csv(ARQ_MOV)
                st.session_state.mov=[] if df_m.empty else df_m.to_dict('records')
            except: st.session_state.mov=[]
            st.rerun()
        else: st.error("Inválido")
    st.stop()

agora=datetime.now(FUSO)
df_forn = pd.read_csv(ARQ_FORN) if os.path.exists(ARQ_FORN) else pd.DataFrame()
lista_forn = df_forn["NOME"].tolist() if not df_forn.empty else ["-"]

# SIDEBAR ADMIN - TUDO DE VOLTA
if st.session_state.perfil=="ADMINISTRADOR":
    with st.sidebar.expander("🏭 FORNECEDORES - EDITAR/NOVO", expanded=False):
        st.dataframe(df_forn, use_container_width=True, hide_index=True)
        st.write("**Novo / Editar**")
        id_f = st.number_input("ID Forn", min_value=1, value=int(df_forn["ID_FORN"].max()+1) if not df_forn.empty else 1, step=1)
        nome_f = st.text_input("Nome fornecedor")
        c1,c2=st.columns(2)
        if c1.button("💾 Salvar fornecedor"):
            if nome_f:
                try: atuais=pd.read_csv(ARQ_FORN).to_dict('records')
                except: atuais=[]
                novos=[f for f in atuais if f["ID_FORN"]!=id_f]
                novos.append({"ID_FORN":id_f,"NOME":nome_f.upper(),"CNPJ":"","CONTATO":"","MARCA":nome_f.upper()})
                pd.DataFrame(novos).to_csv(ARQ_FORN,index=False)
                st.success("Salvo"); st.rerun()
        if c2.button("🗑️ Apagar fornecedor"):
            try: atuais=pd.read_csv(ARQ_FORN).to_dict('records')
            except: atuais=[]
            novos=[f for f in atuais if f["ID_FORN"]!=id_f]
            pd.DataFrame(novos).to_csv(ARQ_FORN,index=False)
            st.warning("Apagado"); st.rerun()

    with st.sidebar.expander("🛠️ EDITAR - ID / NOME / UNID / MARCA", expanded=True):
        df_temp=pd.DataFrame(st.session_state.dados)
        for c in ["UNIDADE","MARCA"]:
            if c not in df_temp.columns: df_temp[c]="-"
        df_mats=df_temp.drop_duplicates(subset=["ID"])[["ID","NOME","UNIDADE","MARCA"]].sort_values("ID")
        st.dataframe(df_mats, use_container_width=True, hide_index=True)
        st.write("**Editar material**")
        id_ed=st.selectbox("ID atual", df_mats["ID"].tolist())
        linha=df_mats[df_mats["ID"]==id_ed].iloc[0]
        c1,c2=st.columns(2)
        nid=c1.number_input("Novo ID",value=int(id_ed),min_value=1,step=1)
        nno=c2.text_input("Nome",value=linha["NOME"])
        c3,c4=st.columns(2)
        nuni=c3.selectbox("Unidade",UNIDADES,index=UNIDADES.index(linha["UNIDADE"]) if linha["UNIDADE"] in UNIDADES else 0)
        nmarca=c4.selectbox("Marca", lista_forn + ["-","OUTRA"], index=0)
        nmarca_custom=st.text_input("Ou digite marca nova", value="" if linha["MARCA"] in lista_forn else linha["MARCA"])
        marca_final = nmarca_custom.upper() if nmarca_custom else nmarca.upper()
        if st.button("💾 Salvar ID/Nome/Unid/Marca"):
            if nid!=id_ed and nid in df_mats["ID"].tolist():
                st.error("ID já existe")
            else:
                for d in st.session_state.dados:
                    if d["ID"]==id_ed:
                        d["ID"]=int(nid); d["NOME"]=nno.upper(); d["UNIDADE"]=nuni; d["MARCA"]=marca_final
                pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
                st.success(f"Salvo: {nid} {nno}"); st.rerun()
        st.divider()
        st.write("**Adicionar novo**")
        ca1,ca2=st.columns(2)
        aid=ca1.number_input("ID novo",value=int(df_mats["ID"].max()+1),min_value=1,step=1,key="aid")
        ano=ca2.text_input("Nome novo",key="ano")
        ca3,ca4=st.columns(2)
        auni=ca3.selectbox("Unid.",UNIDADES,key="auni")
        amarca=ca4.selectbox("Marca",lista_forn + ["-"],key="amarca")
        if st.button("➕ Adicionar material"):
            if ano and aid not in df_mats["ID"].tolist():
                st.session_state.dados.append({"ID":aid,"NOME":ano.upper(),"UNIDADE":auni,"MARCA":amarca if (marca:=amarca.upper()) else "-", "LOCAL":"BARRACÃO","SALDO":0})
                st.session_state.dados.append({"ID":aid,"NOME":ano.upper(),"UNIDADE":auni,"MARCA": marca,"LOCAL":"OFICINA","SALDO":0})
                pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
                st.rerun()
        st.write("**Apagar material**")
        id_ap=st.selectbox("ID apagar", df_mats["ID"].tolist(), key="ap")
        if st.button("🗑️ Apagar material"):
            st.session_state.dados=[d for d in st.session_state.dados if d["ID"]!=id_ap]
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            st.rerun()
    if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

# ESTOQUE + GRAFICOS DE VOLTA
df_est=pd.DataFrame(st.session_state.dados)
for c in ["UNIDADE","MARCA"]:
    if c not in df_est.columns: df_est[c]="-"
pivot=df_est.pivot_table(index=["ID","NOME","UNIDADE","MARCA"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACÃO" not in pivot.columns: pivot["BARRACÃO"]=0
if "OFICINA" not in pivot.columns: pivot["OFICINA"]=0
pivot["TOTAL GERAL"]=pivot["BARRACÃO"]+pivot["OFICINA"]

st.title(f"📦 TOTAL: {pivot['TOTAL GERAL'].sum():.0f} | {agora.strftime('%d/%m/%Y %H:%M')}")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)
c1,c2=st.columns(2)
c1.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACÃO","OFICINA"], barmode="group", color_discrete_map={"BARRACÃO":"#1f77b4","OFICINA":"#ff7f0e"}, title="ESTOQUE REAL POR LOCAL"), use_container_width=True)
c2.plotly_chart(px.pie(pivot, values="TOTAL GERAL", names="NOME", title="TOTAL GERAL POR MATERIAL"), use_container_width=True)
st.plotly_chart(px.pie(pivot, values="TOTAL GERAL", names="MARCA", title="POR MARCA / FORNECEDOR"), use_container_width=True)

st.divider()
# LANÇAMENTO COM MARCA E FORNECEDOR
ids=sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa={d["ID"]:(d["NOME"],d["UNIDADE"],d["MARCA"]) for d in st.session_state.dados}
cA,cB,cC,cD=st.columns(4)
id_sel=cA.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa[x][0]} ({mapa[x][1]} | {mapa[x][2]})")
local_sel=cB.selectbox("Local", ["BARRACÃO","OFICINA"])
marca_lote=cC.selectbox("Marca lote", lista_forn + ["-"], index=lista_forn.index(mapa[id_sel][2]) if mapa[id_sel][2] in lista_forn else 0)
forn_lote=cD.selectbox("Fornecedor", lista_forn, index=lista_forn.index(mapa[id_sel][2]) if mapa[id_sel][2] in lista_forn else 0)
c1,c2,c3,c4=st.columns(4)
lote=c1.text_input("LOTE")
validade=c2.date_input("VALIDADE",value=date.today())
qtd=c3.number_input(f"QTD ({mapa[id_sel][1]})",value=1.0)
ent=c4.number_input("Paletes",value=1.0)
total_calc=qtd*ent
c5,c6,c7=st.columns(3)
resp=c5.text_input("Responsável",value=st.session_state.usuario)
tipo_sel=c6.selectbox("Tipo", ["Entrada","Saída"])
c7.metric(f"TOTAL {mapa[id_sel][1]}", f"{total_calc:.2f}")

if st.button(f"✅ SALVAR {tipo_sel} {local_sel} - {marca_lote}", type="primary", use_container_width=True):
    idx_ba=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACÃO"),None)
    idx_of=next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
    if local_sel=="BARRACÃO" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]+=total_calc; obs=f"ENTRADA BARRACÃO +{total_calc}"
    elif local_sel=="OFICINA" and tipo_sel=="Entrada":
        st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc; obs="TRANSFER B->O"
    elif local_sel=="OFICINA" and tipo_sel=="Saída":
        st.session_state.dados[idx_of]["SALDO"]-=total_calc; obs=f"SAÍDA OFICINA -{total_calc}"
    else:
        st.session_state.dados[idx_ba]["SALDO"]-=total_calc; st.session_state.dados[idx_of]["SALDO"]+=total_calc; obs="TRANSFER"
    novo_id = (max([m["IDX"] for m in st.session_state.mov]) + 1) if st.session_state.mov else 1
    novo={"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"LOTE":lote.upper(),"MARCA":marca_lote.upper(),"FORNECEDOR":forn_lote.upper(),"VALIDADE":validade.strftime("%d/%m/%Y"),"QTD_PALETE":qtd,"ENTRADA":ent,"TOTAL":total_calc,"UNIDADE":mapa[id_sel][1],"LOCAL":local_sel,"TIPO":tipo_sel,"ID_MAT":id_sel,"NOME_MAT":mapa[id_sel][0],"RESPONSAVEL":resp.upper(),"OBS":obs}
    st.session_state.mov.append(novo)
    pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
    st.success(obs); st.rerun()

# REGISTROS COM GRAFICOS - BLINDADO
if st.session_state.mov and len(st.session_state.mov)>0:
    df_mov=pd.DataFrame(st.session_state.mov)
    if not df_mov.empty and "IDX" in df_mov.columns:
        df_mov=df_mov.sort_values("IDX", ascending=False)
        st.divider()
        st.subheader("📋 Registros + Apagar")
        st.dataframe(df_mov, use_container_width=True)
        if "FORNECEDOR" in df_mov.columns:
            st.plotly_chart(px.bar(df_mov, x="NOME_MAT", y="TOTAL", color="FORNECEDOR", barmode="group", title="Consumo por FORNECEDOR"), use_container_width=True)
        if "MARCA" in df_mov.columns:
            st.plotly_chart(px.bar(df_mov, x="NOME_MAT", y="TOTAL", color="MARCA", barmode="group", title="Consumo por MARCA"), use_container_width=True)
        id_del=st.selectbox("IDX para apagar e estornar", df_mov["IDX"].tolist())
        if st.button("🗑️ APAGAR E ESTORNAR ESTOQUE", type="primary"):
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
                if st.session_state.mov:
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                else:
                    pd.DataFrame(columns=["IDX","DATA_HORA","LOTE","MARCA","FORNECEDOR","VALIDADE","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
                st.warning("Apagado e estornado"); st.rerun()
