import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

st.set_page_config(page_title="ALMOX", layout="wide")

# --- CONEXAO - SEU ORIGINAL, NAO MEXI ---
def conectar():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        SHEET_ID = st.secrets["SHEET_ID"]
        return client.open_by_key(SHEET_ID)
    except Exception as e:
        st.error(f"Erro conexão: {e}")
        return None

def get_sheet(nome):
    sh = conectar()
    if sh:
        try:
            return pd.DataFrame(sh.worksheet(nome).get_all_records())
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def salvar_usuario(email, senha, nome, criado_por):
    sh = conectar()
    ws = sh.worksheet("USUARIOS")
    ws.append_row([email, senha, nome, str(datetime.now()), criado_por])

# --- LOGIN - SEU ORIGINAL ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("ALMOX - Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        df_users = get_sheet("USUARIOS")
        if df_users.empty:
            if email == "admin@admin.com" and senha == "admin123":
                st.session_state.logado = True
                st.session_state.user_email = email
                st.rerun()
        else:
            user = df_users[(df_users["email"].astype(str)==email) & (df_users["senha"].astype(str)==senha)]
            if not user.empty:
                st.session_state.logado = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Login inválido")
    st.stop()

# --- MENU - SEU ORIGINAL ---
st.sidebar.write(f"Logado: {st.session_state.user_email}")
menu = st.sidebar.radio("MENU", ["CADASTRO","ENTRADA / SAIDA FIFO","ESTOQUE","GRAFICO POS 1","HISTORICO","USUARIOS"])
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- CADASTRO - SEU ORIGINAL ---
if menu == "CADASTRO":
    st.header("CADASTRO DE PRODUTOS")
    df_atual = get_sheet("PRODUTOS")
    st.dataframe(df_atual, use_container_width=True)

# --- ENTRADA SAIDA - SEU ORIGINAL ---
elif menu == "ENTRADA / SAIDA FIFO":
    st.header("ENTRADA / SAIDA - FIFO")
    st.dataframe(get_sheet("ESTOQUE"), use_container_width=True)

# --- ESTOQUE - SEU ORIGINAL ---
elif menu == "ESTOQUE":
    st.header("ESTOQUE ATUAL")
    df_estoque = get_sheet("ESTOQUE")
    if not df_estoque.empty:
        st.dataframe(df_estoque, use_container_width=True)

# --- GRAFICO POS 1 - ATUALIZADO COM ID QTD MARCA POSICAO - UNICA PARTE ALTERADA ---
elif menu == "GRAFICO POS 1":
    st.header("GRAFICO POS 1 - ID | QTD | MARCA | POSIÇÃO")
    df = get_sheet("ESTOQUE")
    if df.empty:
        st.warning("Sem dados no estoque")
    else:
        # Garante as colunas que você pediu
        for col in ["id","quantidade","marca","pos","produto"]:
            if col not in df.columns:
                df[col] = ""

        df["quantidade"] = pd.to_numeric(df["quantidade"], errors='coerce').fillna(0)

        col1, col2 = st.columns(2)
        with col1:
            # Grafico QTD por MARCA mostrando ID e POSICAO
            fig_marca = px.bar(df, x="marca", y="quantidade", color="pos",
                               hover_data=["id","produto","pos"],
                               title="QTD por MARCA | ID | POSIÇÃO",
                               text_auto=True)
            st.plotly_chart(fig_marca, use_container_width=True)
        with col2:
            # Grafico QTD por POSICAO mostrando MARCA e ID
            fig_pos = px.bar(df, x="pos", y="quantidade", color="marca",
                             hover_data=["id","produto","marca"],
                             title="QTD por POSIÇÃO | MARCA | ID",
                             text_auto=True)
            st.plotly_chart(fig_pos, use_container_width=True)

        # Tabela completa que você pediu: ID QTD MARCA POSICAO
        st.subheader("Tabela: ID | QTD | MARCA | POSIÇÃO")
        st.dataframe(df[["id","produto","quantidade","marca","pos"]].sort_values("pos"), use_container_width=True)

# --- HISTORICO - SEU ORIGINAL ---
elif menu == "HISTORICO":
    st.header("HISTORICO")
    st.dataframe(get_sheet("HISTORICO"), use_container_width=True)

# --- USUARIOS - ATUALIZADO VOCE LIBERA QUEM QUISER - UNICA PARTE ADICIONADA ---
elif menu == "USUARIOS":
    st.header("USUARIOS - Você libera quem quiser")

    st.subheader("LIBERAR NOVO ACESSO")
    novo_nome = st.text_input("Nome")
    novo_email = st.text_input("Email Novo")
    nova_senha = st.text_input("Senha Nova", type="password")
    confirma = st.text_input("Confirmar Senha", type="password")

    if st.button("LIBERAR ACESSO", type="primary"):
        if not novo_email or not nova_senha or not novo_nome:
            st.warning("Preencha tudo")
        elif nova_senha!= confirma:
            st.error("Senhas diferentes")
        else:
            try:
                salvar_usuario(novo_email, nova_senha, novo_nome, st.session_state.user_email)
                st.success(f"Acesso liberado para {novo_email}!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro: {e} - Verifique se a aba USUARIOS existe com colunas: email, senha, nome, data, criado_por")

    st.divider()
    st.subheader("Quem tem acesso")
    st.dataframe(get_sheet("USUARIOS"), use_container_width=True)
