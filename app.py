import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

st.set_page_config(page_title="ALMOX", layout="wide")

# --- SUA FUNCAO CONECTAR - ORIGINAL ---
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

# --- SUA FUNCAO LOGIN - ORIGINAL ---
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

# --- SEU MENU - ORIGINAL ---
st.sidebar.write(f"Logado: {st.session_state.user_email}")
menu = st.sidebar.radio("MENU", ["CADASTRO","ENTRADA / SAIDA FIFO","ESTOQUE","GRAFICO POS 1","HISTORICO","USUARIOS"])
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- SEU CADASTRO - ORIGINAL ---
if menu == "CADASTRO":
    st.header("CADASTRO DE PRODUTOS")

# --- SUA ENTRADA SAIDA - ORIGINAL ---
elif menu == "ENTRADA / SAIDA FIFO":
    st.header("ENTRADA / SAIDA - FIFO")

# --- SEU ESTOQUE - ORIGINAL ---
elif menu == "ESTOQUE":
    st.header("ESTOQUE ATUAL")
    df_estoque = get_sheet("ESTOQUE")
    if not df_estoque.empty:
        st.dataframe(df_estoque, use_container_width=True)

# --- SEU GRAFICO POS 1 - ORIGINAL ---
elif menu == "GRAFICO POS 1":
    st.header("GRAFICO POS 1")
    df = get_sheet("ESTOQUE")
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# --- SEU HISTORICO - ORIGINAL ---
elif menu == "HISTORICO":
    st.header("HISTORICO")
    st.dataframe(get_sheet("HISTORICO"), use_container_width=True)

# --- ABA USUARIOS - UNICA PARTE NOVA QUE VOCE PEDIU ---
elif menu == "USUARIOS":
    st.header("USUARIOS")
    
    # --- INICIO DA NOVA FUNCAO CRIAR USUARIO ---
    st.subheader("Criar Novo Usuario")
    novo_nome = st.text_input("Nome")
    novo_email = st.text_input("Email Novo")
    nova_senha = st.text_input("Senha Nova", type="password")
    
    if st.button("Criar Usuario"):
        if novo_email and nova_senha and novo_nome:
            try:
                sh = conectar()
                ws = sh.worksheet("USUARIOS")
                ws.append_row([novo_email, nova_senha, novo_nome, str(datetime.now()), st.session_state.user_email])
                st.success(f"Usuario {novo_email} criado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao criar: {e}")
        else:
            st.warning("Preencha Nome, Email e Senha")
    # --- FIM DA NOVA FUNCAO ---
    
    st.divider()
    st.subheader("Usuarios Cadastrados")
    st.dataframe(get_sheet("USUARIOS"), use_container_width=True)
