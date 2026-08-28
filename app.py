import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit.components.v1 as components
import urllib.parse

st.set_page_config(page_title="REFORMA DE FORNOS V10 - FIX", layout="wide", page_icon="🔥")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_EMAILS = "emails.csv"
ARQ_GRD = "grd.csv"

LOCAL_GALPAO = "GALPÃO DE MATERIAIS REFRATARIOS"
LOCAL_SALA = "SALA ANEXA"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"
LOCAIS = [LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]

def safe_float(v, padrao=0.0):
    try:
        if v is None or v=="" or str(v).strip()=="": return float(padrao)
        return float(str(v).replace(",",".").strip())
    except: return float(padrao)

def carregar_seguro(caminho):
    if not os.path.exists(caminho): return []
    try:
        df=pd.read_csv(caminho).fillna("")
        df.columns=[str(c).upper().strip() for c in df.columns]
        return df.to_dict('records')
    except:
        try: os.remove(caminho)
        except: pass
        return []

if 'lista_cadastro' not in st.session_state: st.session_state.lista_cadastro=carregar_seguro(ARQ_CAD)
if 'lista_mov' not in st.session_state: st.session_state.lista_mov=carregar_seguro(ARQ_MOV)
if 'lista_grd' not in st.session_state: st.session_state.lista_grd=carregar_seguro(ARQ_GRD)
if 'logado' not in st.session_state: st.session_state.logado=False
if 'edit_idx' not in st.session_state: st.session_state.edit_idx=None

if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO"}]).to_csv(ARQ_EMAILS, index=False)

if not st.session_state.logado:
    st.title("🔐 REFORMA DE FORNOS - Login")
    e = st.text_input("Email").lower().strip()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        df_e = pd.read_csv(ARQ_EMAILS)
        user = df_e[(df_e["EMAIL"]==e) & (df_e["SENHA"]==s) & (df_e["STATUS"]=="LIBERADO")]
        if not user.empty:
            st.session_state.logado=True
            st.session_state.local_acesso=user.iloc[0]["LOCAL"]
            st.rerun()
        else: st.error("Login inválido")
    st.stop()

agora_br = datetime.now(fuso)
st.sidebar.markdown("## 🖥️ MODO 24H")
auto = st.sidebar.toggle("🔄 ATUALIZAÇÃO AUTOMÁTICA 10s (TV)", value=True)
if auto:
    components.html("""<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>""", height=0)

manter = st.sidebar.toggle("🔒 MANTER TELA LIGADA", value=True)
if manter:
    components.html("""<script>let wakeLock=null; async function requestLock(){ try{ if('wakeLock' in navigator){ wakeLock=await navigator.wakeLock.request('screen'); } }catch(e){} } requestLock();</script>""", height=0)

if st.sidebar.button("🔴 FECHAR / BACKUP", type="primary", use_container_width=True):
    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
    pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
    pd.DataFrame(st.session_state.lista_grd).to_csv(ARQ_GRD,index=False)
    st.session_state.clear(); st.stop()

def calcular_valido_ate(fab_str, tempo_meses):
    try:
        fab=datetime.strptime(fab_str, "%d/%m/%Y")
        valido=fab + relativedelta(months=int(safe_float(tempo_meses,12)))
        return valido.strftime("%d/%m/%Y")
    except: return "00/00/0000"

def get_catalogo_por_id(id_digitado):
    id_digitado=str(id_digitado).strip().upper()
    return [(i,r) for i,r in enumerate(st.session_state.lista_cadastro) if str(r.get('ID','')).upper()==id_digitado]

def get_ultimo_catalogo_por_id(id_digitado):
    itens = get_catalogo_por_id(id_digitado)
    return itens[-1][1] if itens else None

def get_saldos_completos():
    saldos={}
    for r in st.session_state.get('lista_cadastro',[]):
        id_prod = str(r.get('ID','')).strip().upper()
        lote = str(r.get('LOTE','')).strip().upper()
        if not id_prod or not lote: continue
        local = str(r.get('LOCAL', LOCAL_GALPAO))
        if "SALA" in local.upper(): local = LOCAL_SALA
        elif "OFIC" in local.upper(): local = LOCAL_OFICINA
        else: local = LOCAL_GALPAO
        marca = str(r.get('MARCA','SEM MARCA')).upper().strip() or "SEM MARCA"
        qtd_palete=safe_float(r.get('QTD_PALETE',0),0)
        entrada_pal=safe_float(r.get('ENTRADA',0),0)
        total=safe_float(r.get('TOTAL',0),0)
        if total==0: total=qtd_palete*entrada_pal
        chave = f"{id_prod}__{local}__{marca}__{lote}"
        if chave not in saldos:
            saldos[chave]={'ID':id_prod,'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE_ORIG':lote,'FABRICACAO':r.get('FABRICACAO',''),'VALIDO_ATE':r.get('VALIDO_ATE',''),'UNIDADE':str(r.get('UNIDADE','KG')).upper(),'QTD_PALETE_BASE':qtd_palete,'SALDO_PALETES':entrada_pal,'SALDO_QTD':total}
        else:
            saldos[chave]['SALDO_PALETES']+=entrada_pal; saldos[chave]['SALDO_QTD']+=total
    for m in st.session_state.get('lista_mov',[]):
        id_prod = str(m.get('ID','')).strip().upper()
        lote = str(m.get('LOTE','')).strip().upper()
        if not id_prod or not lote: continue
        local_mov=str(m.get('LOCAL_MOV','')).strip()
        if "SALA" in local_mov.upper(): local_mov=LOCAL_SALA
        elif "OFIC" in local_mov.upper(): local_mov=LOCAL_OFICINA
        else: local_mov=LOCAL_GALPAO
        marca = str(m.get('MARCA','SEM MARCA')).upper().strip() or "SEM MARCA"
        tipo=str(m.get('TIPO','')).upper()
        paletes=safe_float(m.get('PALETES',0),0)
        qtd=safe_float(m.get('TOTAL_QTD',0),0)
        cat = get_ultimo_catalogo_por_id(id_prod)
        desc_cat = cat.get('DESCRICAO','') if cat else ""
        desc_mov = str(m.get('DESCRICAO','')).upper() or desc_cat
        chave = f"{id_prod}__{local_mov}__{marca}__{lote}"
        if chave not in saldos and tipo=="ENTRADA":
            saldos[chave]={'ID':id_prod,'DESCRICAO':desc_mov,'LOCAL':local_mov,'MARCA':marca,'LOTE_ORIG':lote,'FABRICACAO':m.get('FABRICACAO',''),'VALIDO_ATE':m.get('VALIDO_ATE',''),'UNIDADE':str(m.get('UNIDADE','KG')).upper(),'QTD_PALETE_BASE':safe_float(m.get('QTD_POR_PALETE',0)),'SALDO_PALETES':0,'SALDO_QTD':0}
        if chave not in saldos: continue
        if not saldos[chave].get('DESCRICAO'): saldos[chave]['DESCRICAO']=desc_mov
        if tipo=="ENTRADA":
            saldos[chave]['SALDO_PALETES']+=paletes; saldos[chave]['SALDO_QTD']+=qtd
        else:
            saldos[chave]['SALDO_PALETES']-=paletes; saldos[chave]['SALDO_QTD']-=qtd
    return saldos

def buscar_por_id(id_digitado):
    id_digitado = str(id_digitado).strip().upper()
    saldos = get_saldos_completos()
    resultados = [d for d in saldos.values() if d.get('ID','').upper()==id_digitado and safe_float(d.get('SALDO_QTD',0))>0]
    try: resultados.sort(key=lambda x: datetime.strptime(x.get('FABRICACAO','01/01/2000'), "%d/%m/%Y"))
    except: pass
    return resultados

st.markdown(f"<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00;'>🔥 REFORMA DE FORNOS - {st.session_state.local_acesso} | {agora_br.strftime('%d/%m/%Y %H:%M:%S')} Brasília 🔥</h1>", unsafe_allow_html=True)

tab_dash, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🖥️ DASHBOARD 24H GESTOR","📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 ESTOQUE","📊 BUSCA POR ID","📦 GRD + ZAP","📈 GRAFICOS"])

with tab_dash:
    saldos = get_saldos_completos()
    lista=[{"ID":d.get('ID'),"DESCRIÇÃO":d.get('DESCRICAO'),"LOCAL":d.get('LOCAL'),"MARCA":d.get('MARCA'),"LOTE":d.get('LOTE_ORIG'),"FAB":d.get('FABRICACAO'),"VALIDO":d.get('VALIDO_ATE'),"UNIDADE":d.get('UNIDADE'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0)),"SALDO_PAL":safe_float(d.get('SALDO_PALETES',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)
    if df.empty:
        st.warning("Sem estoque")
    else:
        total_geral_qtd = df['SALDO_QTD'].sum()
        total_geral_pal = df['SALDO_PAL'].sum()
        total_galpao = df[df['LOCAL']==LOCAL_GALPAO]['SALDO_QTD'].sum()
        total_sala = df[df['LOCAL']==LOCAL_SALA]['SALDO_QTD'].sum()
        total_oficina = df[df['LOCAL']==LOCAL_OFICINA]['SALDO_QTD'].sum()
        total_ids = df['ID'].nunique()
        total_lotes = len(df)
        k1,k2,k3,k4,k5,k6 = st.columns(6)
        with k1: st.metric("TOTAL GERAL QTD", f"{total_geral_qtd:,.0f}")
        with k2: st.metric("TOTAL PAL", f"{total_geral_pal:.1f}")
        with k3: st.metric("GALPÃO", f"{total_galpao:,.0f}")
        with k4: st.metric("SALA ANEXA", f"{total_sala:,.0f}")
        with k5: st.metric("OFICINA", f"{total_oficina:,.0f}")
        with k6: st.metric("IDs / LOTES", f"{total_ids} / {total_lotes}")

        c1,c2 = st.columns(2)
        with c1:
            df_id = df.groupby(['ID','DESCRIÇÃO'])[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(15)
            df_id['ID_DESC'] = df_id['ID'] + " - " + df_id['DESCRIÇÃO'].str[:20]
            df_id['TEXTO'] = df_id['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig1 = px.bar(df_id, x='ID_DESC', y='SALDO_QTD', text='TEXTO', title="TOP 15 IDs POR QTD - NUMEROS VISIVEIS")
            fig1.update_traces(textposition='outside', textfont_size=16)
            fig1.update_layout(height=600, xaxis_tickangle=-30)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            df_local = df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index()
            fig_pizza = px.pie(df_local, values='SALDO_QTD', names='LOCAL', title="DISTRIBUIÇÃO POR LOCAL", hole=0.4)
            fig_pizza.update_traces(textinfo='value+percent+label', textfont_size=18)
            st.plotly_chart(fig_pizza, use_container_width=True)

        df_show = df.sort_values(by='SALDO_QTD', ascending=False)[['ID','DESCRIÇÃO','LOTE','MARCA','LOCAL','FAB','VALIDO','SALDO_PAL','SALDO_QTD','UNIDADE']]
        st.dataframe(df_show, use_container_width=True, height=600)

#... resto das abas igual ao V10 (cadastro, movimentação, etc) já estão no arquivo completo que te mandei, só troque a linha 231 por essa
