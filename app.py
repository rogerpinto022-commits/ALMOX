import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox Final", layout="wide")
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
    else:
        try:
            df = pd.read_csv(ARQ_DADOS)
            if "VALIDADE_PADRAO" not in df.columns: df["VALIDADE_PADRAO"] = 180
            if "UNIDADE" not in df.columns: df["UNIDADE"] = "UN"
            if "MARCA" not in df.columns: df["MARCA"] = "-"
            df.to_csv(ARQ_DADOS,index=False)
        except:
            pass

    if not os.path.exists(ARQ_MOV):
        pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","MARCA","FORNECEDOR","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)

    if not os.path.exists(ARQ_EMAILS):
        pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","PERFIL":"ADMINISTRADOR"}]).to_csv(ARQ_EMAILS,index=False)

    if not os.path.exists(ARQ_FORN):
        pd.DataFrame([{"ID_FORN":i+1,"NOME":n,"MARCA":n} for i,n in enumerate(["FONDU","SHINAGAWA","TECNOFIRE","CABOFRAX","IBAR","BIOLA"])]).to_csv(ARQ_FORN,index=False)

init()

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("Login")
    e = st.text_input("Email").lower().strip()
    s = st.text_input("Senha",type="password")
    if st.button("Entrar"):
        try:
            df_e = pd.read_csv(ARQ_EMAILS)
            u = df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"]==s)]
            if not u.empty:
                st.session_state.logado = True
                st.session_state.usuario = e
                st.session_state.dados = pd.read_csv(ARQ_DADOS).to_dict('records')
                try:
                    df_m = pd.read_csv(ARQ_MOV)
                    if df_m.empty or "IDX" not in df_m.columns:
                        st.session_state.mov = []
                    else:
                        st.session_state.mov = df_m.to_dict('records')
                except:
                    st.session_state.mov = []
                st.rerun()
            else:
                st.error("Invalido")
        except Exception as ex:
            st.error(f"Erro login: {ex}")
    st.stop()

agora = datetime.now(FUSO)
hoje = date.today()

try:
    df_forn = pd.read_csv(ARQ_FORN)
    lista_forn = df_forn["NOME"].tolist() if not df_forn.empty else ["-"]
except:
    lista_forn = ["-"]

# SIDEBAR VALIDADE PADRAO
with st.sidebar.expander("EDITAR VALIDADE PADRAO", expanded=True):
    df_tmp = pd.DataFrame(st.session_state.dados)
    if "VALIDADE_PADRAO" not in df_tmp.columns:
        df_tmp["VALIDADE_PADRAO"] = 180
    df_tmp = df_tmp.drop_duplicates("ID")[["ID","NOME","VALIDADE_PADRAO"]].sort_values("ID")
    st.dataframe(df_tmp, use_container_width=True, hide_index=True)
    if not df_tmp.empty:
        id_val = st.selectbox("ID material", df_tmp["ID"].tolist(), key="idval")
        linha_val = df_tmp[df_tmp["ID"]==id_val].iloc[0]
        dias_atual = int(linha_val["VALIDADE_PADRAO"])
        novos_dias = st.number_input(f"Dias - {linha_val['NOME']}", min_value=1, max_value=3650, value=dias_atual, step=1)
        if st.button("Salvar validade padrao"):
            for d in st.session_state.dados:
                if d["ID"] == id_val:
                    d["VALIDADE_PADRAO"] = novos_dias
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            st.success("Salvo")
            st.rerun()

# SIDEBAR EDITAR LOTE - BLINDADO
with st.sidebar.expander("EDITAR VALIDADE DE LOTE", expanded=False):
    if st.session_state.mov and len(st.session_state.mov) > 0:
        df_m = pd.DataFrame(st.session_state.mov)
        if "IDX" in df_m.columns and not df_m.empty:
            try:
                idx_list = df_m["IDX"].tolist()
                idx_edit = st.selectbox("IDX do lote", idx_list)
                lote_sel = df_m[df_m["IDX"]==idx_edit].iloc[0]
                st.write(f"Lote: {lote_sel.get('LOTE','')} | Mat: {lote_sel.get('NOME_MAT','')}")
                try:
                    fab_atual = datetime.strptime(str(lote_sel.get('DATA_FAB','')),"%d/%m/%Y").date()
                except:
                    fab_atual = hoje
                try:
                    val_atual = datetime.strptime(str(lote_sel.get('VALIDADE','')),"%d/%m/%Y").date()
                except:
                    val_atual = hoje + timedelta(days=180)
                nova_fab = st.date_input("Nova DATA FAB", value=fab_atual, key="nfab")
                nova_val = st.date_input("Nova DATA VALIDADE", value=val_atual, key="nval")
                st.write(f"Novo prazo: {(nova_val-nova_fab).days} dias")
                if st.button("Atualizar lote"):
                    for m in st.session_state.mov:
                        if m.get("IDX") == idx_edit:
                            m["DATA_FAB"] = nova_fab.strftime("%d/%m/%Y")
                            m["VALIDADE"] = nova_val.strftime("%d/%m/%Y")
                            m["DIAS_VALIDADE"] = (nova_val - nova_fab).days
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                    st.success("Atualizado")
                    st.rerun()
            except Exception as ex:
                st.write(f"Sem lotes validos: {ex}")
        else:
            st.write("Nenhum lote ainda")
    else:
        st.write("Nenhum lote lancado")

if st.sidebar.button("Sair"):
    st.session_state.clear()
    st.rerun()

# ESTOQUE
df_est = pd.DataFrame(st.session_state.dados)
if "VALIDADE_PADRAO" not in df_est.columns:
    df_est["VALIDADE_PADRAO"] = 180

pivot = df_est.pivot_table(index=["ID","NOME","VALIDADE_PADRAO","UNIDADE"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index()
if "BARRACAO" not in pivot.columns:
    pivot["BARRACAO"] = 0
if "OFICINA" not in pivot.columns:
    pivot["OFICINA"] = 0
pivot["TOTAL"] = pivot["BARRACAO"] + pivot["OFICINA"]

st.title(f"TOTAL: {pivot['TOTAL'].sum():.0f}")
st.dataframe(pivot.sort_values("ID"), use_container_width=True)
st.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACAO","OFICINA"], barmode="group", title="Estoque por Local"), use_container_width=True)

# LANCAMENTO
st.divider()
st.subheader("Lancamento")
ids = sorted(list(set([d["ID"] for d in st.session_state.dados])))
mapa = {d["ID"]:(d["NOME"],d["UNIDADE"],d.get("VALIDADE_PADRAO",180)) for d in st.session_state.dados}

if ids:
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

    if dias_restantes < 0:
        status = "VENCIDO"
    elif dias_restantes <= 30:
        status = "A VENCER 30d"
    elif dias_restantes <= 90:
        status = "A VENCER 90d"
    else:
        status = "OK"

    st.info(f"Padrao: {mapa[id_sel][2]} dias | Validade: {dias_validade} dias | Restam: {dias_restantes} dias | {status}")

    if st.button(f"SALVAR - {status}", type="primary", use_container_width=True):
        idx_ba = next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="BARRACAO"),None)
        idx_of = next((i for i,d in enumerate(st.session_state.dados) if d["ID"]==id_sel and d["LOCAL"]=="OFICINA"),None)
        total_calc = qtd*ent
        if idx_ba is not None and idx_of is not None:
            if local_sel == "BARRACAO":
                st.session_state.dados[idx_ba]["SALDO"] += total_calc
            else:
                st.session_state.dados[idx_ba]["SALDO"] -= total_calc
                st.session_state.dados[idx_of]["SALDO"] += total_calc

            if st.session_state.mov:
                try:
                    novo_id = max([int(m.get("IDX",0)) for m in st.session_state.mov]) + 1
                except:
                    novo_id = 1
            else:
                novo_id = 1

            novo = {
                "IDX":novo_id,
                "DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),
                "DATA_FAB":data_fab.strftime("%d/%m/%Y"),
                "VALIDADE":validade.strftime("%d/%m/%Y"),
                "DIAS_VALIDADE":dias_validade,
                "STATUS_VAL":status,
                "LOTE":lote.upper(),
                "MARCA":"-",
                "FORNECEDOR":"-",
                "QTD_PALETE":qtd,
                "ENTRADA":ent,
                "TOTAL":total_calc,
                "UNIDADE":mapa[id_sel][1],
                "LOCAL":local_sel,
                "TIPO":"Entrada",
                "ID_MAT":id_sel,
                "NOME_MAT":mapa[id_sel][0],
                "RESPONSAVEL":st.session_state.usuario,
                "OBS":status
            }
            st.session_state.mov.append(novo)
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
            pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
            st.success("Salvo")
            st.rerun()

# GRAFICOS VALIDADE
if st.session_state.mov and len(st.session_state.mov) > 0:
    df_mov = pd.DataFrame(st.session_state.mov)
    if not df_mov.empty and "IDX" in df_mov.columns:
        df_mov["VAL_DT"] = pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
        df_mov["FAB_DT"] = pd.to_datetime(df_mov["DATA_FAB"], format="%d/%m/%Y", errors='coerce')
        df_mov["DIAS_REST"] = (df_mov["VAL_DT"] - pd.Timestamp(hoje)).dt.days

        def stt(d):
            if pd.isna(d): return "SEM"
            if d < 0: return "VENCIDO"
            if d <= 30: return "A VENCER 30d"
            if d <= 90: return "A VENCER 90d"
            return "OK"

        df_mov["STATUS_ATUAL"] = df_mov["DIAS_REST"].apply(stt)

        st.divider()
        st.subheader("Controle Validade")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("VENCIDOS", len(df_mov[df_mov["STATUS_ATUAL"]=="VENCIDO"]))
        m2.metric("30d", len(df_mov[df_mov["STATUS_ATUAL"]=="A VENCER 30d"]))
        m3.metric("90d", len(df_mov[df_mov["STATUS_ATUAL"]=="A VENCER 90d"]))
        m4.metric("OK", len(df_mov[df_mov["STATUS_ATUAL"]=="OK"]))

        st.plotly_chart(px.bar(df_mov, x="NOME_MAT", color="STATUS_ATUAL", title="VENCIDOS E A VENCER POR MATERIAL", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)
        st.plotly_chart(px.scatter(df_mov, x="FAB_DT", y="VAL_DT", color="STATUS_ATUAL", size="TOTAL", hover_data=["LOTE","DIAS_REST"], title="FABRICACAO vs VENCIMENTO"), use_container_width=True)
        st.dataframe(df_mov.sort_values("VAL_DT")[["IDX","NOME_MAT","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","LOTE","TOTAL","LOCAL"]], use_container_width=True)
