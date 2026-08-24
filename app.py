import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz
import os

st.set_page_config(page_title="Controle Lotes", layout="wide")
fuso = pytz.timezone('America/Sao_Paulo')

ARQ = "lotes.csv"
COLUNAS = ["LOTE", "VALIDADE", "QTD/PALETE", "ENTRADA", "TOTAL", "IDADE DE MEDIA", "DATA"]

def carregar():
    if os.path.exists(ARQ):
        try:
            df = pd.read_csv(ARQ)
            # garante colunas
            for c in COLUNAS:
                if c not in df.columns:
                    return pd.DataFrame(columns=COLUNAS)
            return df
        except:
            return pd.DataFrame(columns=COLUNAS)
    else:
        return pd.DataFrame(columns=COLUNAS)

df = carregar()

# --- FUNÇÕES A SEREM PREENCHIDAS ---
st.sidebar.header("📦 Lançamento")
agora = datetime.now(fuso)

lote = st.sidebar.text_input("LOTE")
validade = st.sidebar.date_input("VALIDADE", value=date.today())
qtd_palete = st.sidebar.number_input("QTD/PALETE", min_value=0.0, value=0.0, step=1.0)
entrada = st.sidebar.number_input("ENTRADA (nº paletes)", min_value=0.0, value=1.0, step=1.0)
data_lanc = st.sidebar.date_input("DATA", value=date.today())

# CÁLCULOS AUTOMÁTICOS
total = qtd_palete * entrada

# IDADE DE MEDIA = dias entre hoje e a DATA de entrada
if data_lanc:
    idade_media = (date.today() - data_lanc).days
    if idade_media < 0:
        idade_media = 0
else:
    idade_media = 0

st.sidebar.metric("TOTAL calculado", f"{total:.0f}")
st.sidebar.metric("IDADE DE MEDIA (dias)", f"{idade_media} dias")

if st.sidebar.button("✅ Salvar Lote", type="primary", use_container_width=True):
    if not lote:
        st.sidebar.error("Preencha o LOTE")
    else:
        novo = {
            "LOTE": lote.upper().strip(),
            "VALIDADE": validade.strftime("%d/%m/%Y"),
            "QTD/PALETE": qtd_palete,
            "ENTRADA": entrada,
            "TOTAL": total,
            "IDADE DE MEDIA": idade_media,
            "DATA": data_lanc.strftime("%d/%m/%Y") + f" {agora.strftime('%H:%M')} - Brasília"
        }
        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
        df.to_csv(ARQ, index=False)
        st.sidebar.success(f"Lote {lote} salvo!")
        st.rerun()

# --- TELA PRINCIPAL ---
st.title("📋 Controle por Lote")
st.caption(f"Horário Brasília: {agora.strftime('%d/%m/%Y %H:%M:%S')}")

if df.empty:
    st.info("Nenhum lote lançado ainda. Preencha ao lado.")
    st.stop()

# Converte para cálculo
df["VALIDADE_DT"] = pd.to_datetime(df["VALIDADE"], dayfirst=True, errors='coerce')
df["DATA_DT"] = pd.to_datetime(df["DATA"].str[:10], dayfirst=True, errors='coerce')
hoje = pd.Timestamp.now()

# Alerta de validade
df["DIAS_PARA_VENCER"] = (df["VALIDADE_DT"] - hoje).dt.days

# Métricas
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Geral", f"{df['TOTAL'].sum():.0f}")
c2.metric("Total Paletes", f"{df['ENTRADA'].sum():.0f}")
c3.metric("Lotes vencidos", f"{len(df[df['DIAS_PARA_VENCER']<0])}")
c4.metric("Lotes a vencer 30 dias", f"{len(df[(df['DIAS_PARA_VENCER']>=0)&(df['DIAS_PARA_VENCER']<=30)])}")

st.divider()

# Filtros
f_lote = st.text_input("🔍 Filtrar por LOTE")
if f_lote:
    df_filt = df[df["LOTE"].str.contains(f_lote.upper(), na=False)]
else:
    df_filt = df

# Tabela colorida
def cor_validade(val):
    if val < 0:
        return 'background-color: #ff4b4b; color: white'
    elif val <= 30:
        return 'background-color: #ffcc00'
    else:
        return ''

st.dataframe(
    df_filt[COLUNAS + ["DIAS_PARA_VENCER"]].sort_values("VALIDADE_DT"),
    use_container_width=True
)

st.divider()

# --- EDITAR / EXCLUIR ---
st.subheader("🗑️ Editar / Excluir")

col1, col2 = st.columns([2,1])
with col1:
    lote_sel = st.selectbox("Selecione o LOTE para editar/excluir", df["LOTE"].unique())

with col2:
    st.write("")
    st.write("")
    if st.button("🗑️ Excluir Lote"):
        df = df[df["LOTE"]!= lote_sel]
        df.to_csv(ARQ, index=False)
        st.success(f"Lote {lote_sel} excluído!")
        st.rerun()

# Mostrar dados do lote selecionado
if lote_sel:
    linha = df[df["LOTE"]==lote_sel].iloc[0]
    st.write(f"Editando: **{lote_sel}**")
    c1,c2,c3 = st.columns(3)
    nova_qtd = c1.number_input("Nova QTD/PALETE", value=float(linha["QTD/PALETE"]))
    nova_ent = c2.number_input("Nova ENTRADA", value=float(linha["ENTRADA"]))
    nova_val = c3.date_input("Nova Validade", value=pd.to_datetime(linha["VALIDADE"], dayfirst=True).date() if pd.notna(linha["VALIDADE_DT"]) else date.today())

    if st.button("💾 Atualizar"):
        idx = df[df["LOTE"]==lote_sel].index[0]
        df.loc[idx, "QTD/PALETE"] = nova_qtd
        df.loc[idx, "ENTRADA"] = nova_ent
        df.loc[idx, "TOTAL"] = nova_qtd * nova_ent
        df.loc[idx, "VALIDADE"] = nova_val.strftime("%d/%m/%Y")
        # Recalcula idade
        df.loc[idx, "IDADE DE MEDIA"] = (date.today() - pd.to_datetime(df.loc[idx, "DATA"][:10], dayfirst=True).date()).days if len(str(df.loc[idx, "DATA"]))>5 else 0
        df.to_csv(ARQ, index=False)
        st.success("Atualizado!")
        st.rerun()
         
