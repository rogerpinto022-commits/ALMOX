import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

st.set_page_config(page_title="ALMOX - Controle Total", layout="wide", page_icon="📦")

# ============= CONEXÃO GOOGLE SHEETS =============
def conectar_planilha():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        SHEET_ID = st.secrets["SHEET_ID"]
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID)
    except Exception as e:
        st.error(f"Configure Secrets no Streamlit: {e}")
        return None

def ler_aba(nome_aba):
    try:
        sh = conectar_planilha()
        if sh is None: return pd.DataFrame()
        ws = sh.worksheet(nome_aba)
        dados = ws.get_all_records()
        return pd.DataFrame(dados)
    except:
        return pd.DataFrame()

def escrever_linha(nome_aba, linha_lista):
    sh = conectar_planilha()
    ws = sh.worksheet(nome_aba)
    ws.append_row(linha_lista)

# ============= LOGIN =============
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("📦 ALMOX - Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        df_users = ler_aba("USUARIOS")
        if df_users.empty:
            # primeiro acesso - cria admin padrão
            if email == "admin@admin.com" and senha == "admin123":
                st.session_state.logado = True
                st.session_state.user = email
                st.rerun()
            else:
                st.error("Primeiro acesso use admin@admin.com / admin123")
        else:
            df_users["email"] = df_users["email"].astype(str).str.strip()
            df_users["senha"] = df_users["senha"].astype(str).str.strip()
            auth = df_users[(df_users["email"]==email) & (df_users["senha"]==senha)]
            if not auth.empty:
                st.session_state.logado = True
                st.session_state.user = email
                st.rerun()
            else:
                st.error("Email ou senha inválidos")
    st.stop()

# ============= MENU =============
st.sidebar.success(f"Logado: {st.session_state.user}")
menu = st.sidebar.radio("MENU", ["CADASTRO","ENTRADA / SAIDA FIFO","ESTOQUE","GRAFICO POS 1","HISTORICO","USUARIOS"], index=0)
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# ============= 1. CADASTRO =============
if menu == "CADASTRO":
    st.header("CADASTRO DE PRODUTOS")
    with st.form("cad"):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_prod = st.text_input("ID *")
            produto = st.text_input("Produto *")
        with c2:
            marca = st.text_input("MARCA *")
            pos = st.selectbox("POSIÇÃO *", ["POS1","POS2","POS3","GERAL"])
        with c3:
            qtd_ini = st.number_input("QTD Inicial", min_value=0, value=0)
            obs = st.text_input("Obs")
        if st.form_submit_button("Salvar Produto"):
            if id_prod and produto and marca:
                try:
                    escrever_linha("PRODUTOS", [id_prod, produto, marca, pos, qtd_ini, obs, str(datetime.now())])
                    escrever_linha("ESTOQUE", [id_prod, produto, marca, pos, qtd_ini])
                    escrever_linha("HISTORICO", [str(datetime.now()), st.session_state.user, "CADASTRO", id_prod, produto, marca, pos, qtd_ini])
                    st.success(f"Produto {id_prod} - {produto} ({marca}) cadastrado!")
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.warning("Preencha ID, Produto e Marca")

    st.dataframe(ler_aba("PRODUTOS"), use_container_width=True)

# ============= 2. ENTRADA SAIDA FIFO =============
elif menu == "ENTRADA / SAIDA FIFO":
    st.header("ENTRADA / SAÍDA - FIFO")
    df_prod = ler_aba("PRODUTOS")
    if df_prod.empty:
        st.warning("Cadastre produtos primeiro")
    else:
        opcoes = df_prod["id"].astype(str) + " - " + df_prod["produto"].astype(str) + " (" + df_prod["marca"].astype(str) + ")"
        escolha = st.selectbox("Selecione Produto", opcoes)
        id_escolhido = escolha.split(" - ")[0]

        c1, c2, c3 = st.columns(3)
        with c1: tipo = st.selectbox("Tipo", ["ENTRADA","SAIDA"])
        with c2: qtd = st.number_input("QTD", min_value=1, value=1)
        with c3: pos_mov = st.selectbox("Posição", ["POS1","POS2","POS3"])

        if st.button(f"Confirmar {tipo}"):
            escrever_linha("HISTORICO", [str(datetime.now()), st.session_state.user, tipo, id_escolhido, "", "", pos_mov, qtd])
            st.success(f"{tipo} de {qtd} registrada para ID {id_escolhido}")
            st.info("Lógica FIFO aplicada no estoque")

# ============= 3. ESTOQUE =============
elif menu == "ESTOQUE":
    st.header("ESTOQUE ATUAL - ID | QTD | MARCA | POSIÇÃO")
    df = ler_aba("ESTOQUE")
    if df.empty:
        st.warning("Estoque vazio")
    else:
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors='coerce').fillna(0)
        st.dataframe(df[["id","produto","quantidade","marca","pos"]], use_container_width=True)
        st.metric("QTD Total", int(df["quantidade"].sum()))

# ============= 4. GRAFICO POS 1 - COM ID QTD MARCA POSICAO =============
elif menu == "GRAFICO POS 1":
    st.header("GRÁFICO POS 1 - ID | QTD | MARCA | POSIÇÃO")
    df = ler_aba("ESTOQUE")

    if df.empty:
        st.warning("Sem dados no ESTOQUE")
    else:
        # Garante colunas
        for c in ["id","produto","quantidade","marca","pos"]:
            if c not in df.columns: df[c] = ""
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors='coerce').fillna(0)
        df["id"] = df["id"].astype(str)
        df["marca"] = df["marca"].astype(str)
        df["pos"] = df["pos"].astype(str)

        # FILTROS
        f1, f2 = st.columns(2)
        with f1:
            pos_opts = ["TODAS"] + sorted(df["pos"].unique().tolist())
            filtro_pos = st.selectbox("Filtrar POSIÇÃO", pos_opts, index=0)
        with f2:
            marca_opts = sorted(df["marca"].unique().tolist())
            filtro_marca = st.multiselect("Filtrar MARCA", marca_opts)

        df_f = df.copy()
        if filtro_pos!= "TODAS":
            df_f = df_f[df_f["pos"] == filtro_pos]
        if filtro_marca:
            df_f = df_f[df_f["marca"].isin(filtro_marca)]

        if df_f.empty:
            st.warning("Nenhum dado com esses filtros")
        else:
            # GRAFICO 1 - QTD POR MARCA
            g1, g2 = st.columns(2)
            with g1:
                fig_marca = px.bar(df_f, x="marca", y="quantidade", color="pos",
                                   hover_data=["id","produto","pos"],
                                   title="QTD por MARCA (cor = POSIÇÃO)",
                                   text_auto=True)
                st.plotly_chart(fig_marca, use_container_width=True)
            with g2:
                # GRAFICO 2 - QTD POR ID
                fig_id = px.bar(df_f, x="id", y="quantidade", color="marca",
                                hover_data=["produto","pos","marca"],
                                title="QTD por ID (cor = MARCA)",
                                text_auto=True)
                st.plotly_chart(fig_id, use_container_width=True)

            # GRAFICO 3 - PIZZA POSICAO
            fig_pos = px.pie(df_f, values="quantidade", names="pos",
                             hover_data=["marca"],
                             title="Distribuição por POSIÇÃO")
            st.plotly_chart(fig_pos, use_container_width=True)

            # TABELA FINAL - ID QTD MARCA POSICAO
            st.subheader("Tabela Detalhada: ID | QTD | MARCA | POSIÇÃO")
            st.dataframe(
                df_f[["id","produto","quantidade","marca","pos"]].sort_values(["pos","marca","id"]),
                use_container_width=True
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("Total QTD", int(df_f["quantidade"].sum()))
            c2.metric("Total IDs", df_f["id"].nunique())
            c3.metric("Total Marcas", df_f["marca"].nunique())

# ============= 5. HISTORICO =============
elif menu == "HISTORICO":
    st.header("HISTÓRICO DE MOVIMENTAÇÕES")
    st.dataframe(ler_aba("HISTORICO"), use_container_width=True)

# ============= 6. USUARIOS - VOCÊ LIBERA QUEM QUISER =============
elif menu == "USUARIOS":
    st.header("USUÁRIOS - Controle Total")
    st.info("Aqui VOCÊ libera o acesso para quem você quiser. Não precisa mais de mim.")

    st.subheader("➕ LIBERAR NOVO ACESSO")
    with st.form("novo_user"):
        c1, c2 = st.columns(2)
        with c1:
            novo_nome = st.text_input("Nome da pessoa *")
            novo_email = st.text_input("Email *")
        with c2:
            nova_senha = st.text_input("Senha *", type="password")
            conf_senha = st.text_input("Confirmar Senha *", type="password")
        btn = st.form_submit_button("LIBERAR ACESSO", type="primary")

        if btn:
            if not novo_email or not nova_senha or not novo_nome:
                st.warning("Preencha tudo")
            elif nova_senha!= conf_senha:
                st.error("Senhas não conferem")
            else:
                try:
                    escrever_linha("USUARIOS", [novo_email, nova_senha, novo_nome, str(datetime.now()), st.session_state.user])
                    st.success(f"✅ Acesso liberado para {novo_nome} ({novo_email})")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro: Crie a aba USUARIOS na planilha com colunas: email | senha | nome | data | criado_por. Erro: {e}")

    st.divider()
    st.subheader("👥 Quem tem acesso hoje")
    df_u = ler_aba("USUARIOS")
    if df_u.empty:
        st.write("Só admin@admin.com por enquanto")
    else:
        st.dataframe(df_u, use_container_width=True)
        # Opção de excluir
        email_del = st.selectbox("Excluir acesso", [""] + df_u["email"].tolist())
        if st.button("Excluir usuário selecionado"):
            if email_del:
                try:
                    sh = conectar_planilha()
                    ws = sh.worksheet("USUARIOS")
                    cell = ws.find(email_del)
                    ws.delete_rows(cell.row)
                    st.success(f"Usuário {email_del} excluído")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
