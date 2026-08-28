import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import urllib.parse

st.set_page_config(page_title="REFORMA DE FORNOS V10 - DASHBOARD 24H", layout="wide", page_icon="🔥")
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
auto_default = True
auto = st.sidebar.toggle("🔄 ATUALIZAÇÃO AUTOMÁTICA 10s (TV)", value=auto_default)
if auto:
    st.sidebar.success("✅ MODO TV ATIVO - Atualizando")
    components.html("""<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>""", height=0)

manter = st.sidebar.toggle("🔒 MANTER TELA LIGADA", value=True)
if manter:
    components.html("""<script>let wakeLock=null; async function requestLock(){ try{ if('wakeLock' in navigator){ wakeLock=await navigator.wakeLock.request('screen'); } }catch(e){} } requestLock(); document.addEventListener('visibilitychange',()=>{ if(wakeLock!==null && document.visibilityState==='visible'){requestLock();} });</script>""", height=0)

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

st.markdown("""
<style>
.big-metric {font-size: 48px!important; font-weight: 900!important; color: #00ff66!important; font-family: Orbitron, Arial Black!important; text-shadow: 0 0 10px #00ff66; }
.medium-metric {font-size: 28px!important; font-weight: 800!important; }
.card-24h {background: #111; border: 3px solid #ff4e00; border-radius: 15px; padding: 15px; margin: 10px 0; }
.led-green {background: #000; color: #00ff66; padding: 15px; border-radius: 12px; border: 4px solid #ff4e00; font-family: Orbitron; text-align: center; font-size: 28px; font-weight: 900; text-shadow: 0 0 10px #00ff66;}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<div class='led-green'>🔥 REFORMA DE FORNOS - {st.session_state.local_acesso} | {agora_br.strftime('%d/%m/%Y %H:%M:%S')} Brasília | DASHBOARD 24H 🔥</div>", unsafe_allow_html=True)

tab_dash, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🖥️ DASHBOARD 24H GESTOR","📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 ESTOQUE","📊 BUSCA POR ID","📦 GRD + ZAP","📈 GRAFICOS"])

with tab_dash:
    st.markdown("### 🖥️ DASHBOARD GESTOR - VISÃO 24 HORAS - NUMEROS GIGANTES")
    saldos = get_saldos_completos()
    lista=[{"ID":d.get('ID'),"DESCRIÇÃO":d.get('DESCRICAO'),"LOCAL":d.get('LOCAL'),"MARCA":d.get('MARCA'),"LOTE":d.get('LOTE_ORIG'),"FAB":d.get('FABRICACAO'),"VALIDO":d.get('VALIDO_ATE'),"UNIDADE":d.get('UNIDADE'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0)),"SALDO_PAL":safe_float(d.get('SALDO_PALETES',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)

    if df.empty:
        st.warning("Sem estoque - cadastre")
    else:
        total_geral_qtd = df['SALDO_QTD'].sum()
        total_geral_pal = df['SALDO_PAL'].sum()
        total_galpao = df[df['LOCAL']==LOCAL_GALPAO]['SALDO_QTD'].sum()
        total_sala = df[df['LOCAL']==LOCAL_SALA]['SALDO_QTD'].sum()
        total_oficina = df[df['LOCAL']==LOCAL_OFICINA]['SALDO_QTD'].sum()
        total_ids = df['ID'].nunique()
        total_lotes = len(df)

        k1,k2,k3,k4,k5,k6 = st.columns(6)
        with k1:
            st.markdown(f"<div class='card-24h'><div class='medium-metric'>TOTAL GERAL</div><div class='big-metric'>{total_geral_qtd:,.0f}</div><div>QTD</div></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='card-24h'><div class='medium-metric'>TOTAL PALETES</div><div class='big-metric'>{total_geral_pal:,.1f}</div><div>PAL</div></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='card-24h'><div class='medium-metric'>GALPÃO</div><div class='big-metric' style='color:#00ccff!important;'>{total_galpao:,.0f}</div></div>", unsafe_allow_html=True)
        with k4:
            st.markdown(f"<div class='card-24h'><div class='medium-metric'>SALA ANEXA</div><div class='big-metric' style='color:#ffcc00!important;'>{total_sala:,.0f}</div></div>", unsafe_allow_html=True)
        with k5:
            st.markdown(f"<div class='card-24h'><div class='medium-metric'>OFICINA</div><div class='big-metric' style='color:#ff6600!important;'>{total_oficina:,.0f}</div></div>", unsafe_allow_html=True)
        with k6:
            st.markdown(f"<div class='card-24h'><div class='medium-metric'>IDs / LOTES</div><div class='big-metric' style='color:#fff!important;'>{total_ids} / {total_lotes}</div></div>", unsafe_allow_html=True)

        st.divider()
        c1,c2 = st.columns(2)
        with c1:
            df_id = df.groupby(['ID','DESCRIÇÃO'])[['SALDO_QTD','SALDO_PAL']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(15)
            df_id['ID_DESC'] = df_id['ID'] + " - " + df_id['DESCRIÇÃO'].str[:20]
            df_id['TEXTO'] = df_id['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig1 = px.bar(df_id, x='ID_DESC', y='SALDO_QTD', text='TEXTO', title="🔝 TOP 15 IDs POR QTD", color='SALDO_QTD', color_continuous_scale='Viridis')
            fig1.update_traces(textposition='outside', textfont_size=16, textfont_family="Arial Black", marker_line_width=2)
            fig1.update_layout(height=600, title_font_size=24, xaxis_tickangle=-30)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            df_local = df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index()
            df_local['TEXTO'] = df_local['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig_pizza = px.pie(df_local, values='SALDO_QTD', names='LOCAL', title="📦 DISTRIBUIÇÃO POR LOCAL", hole=0.4)
            fig_pizza.update_traces(textinfo='value+percent+label', textfont_size=18, textfont_family="Arial Black")
            fig_pizza.update_layout(height=600, title_font_size=22)
            st.plotly_chart(fig_pizza, use_container_width=True)

        st.divider()
        df_marca = df.groupby(['MARCA'])[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(10)
        df_marca['TEXTO'] = df_marca['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
        fig3 = px.bar(df_marca, x='MARCA', y='SALDO_QTD', text='TEXTO', title="🏷️ TOP 10 MARCAS POR QTD", color='MARCA')
        fig3.update_traces(textposition='outside', textfont_size=18, textfont_family="Arial Black")
        fig3.update_layout(height=500, title_font_size=22)
        st.plotly_chart(fig3, use_container_width=True)

        st.divider()
        df_lote = df.sort_values(by='FAB', ascending=True).head(20)
        df_lote['TEXTO'] = df_lote['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
        fig4 = px.bar(df_lote, x='LOTE', y='SALDO_QTD', color='LOCAL', text='TEXTO', title="⏰ LOTES FIFO - MAIS ANTIGOS PRIMEIRO", barmode='group', hover_data=['ID','DESCRIÇÃO','FAB','VALIDO'])
        fig4.update_traces(textposition='outside', textfont_size=14)
        fig4.update_layout(height=600, xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)

        st.divider()
        df_show = df.sort_values(by='SALDO_QTD', ascending=False)[['ID','DESCRIÇÃO','LOTE','MARCA','LOCAL','FAB','VALIDO','SALDO_PAL','SALDO_QTD','UNIDADE']]
        st.dataframe(df_show.style.format({"SALDO_QTD":"{:,.0f}","SALDO_PAL":"{:.1f}"}).background_gradient(subset=['SALDO_QTD'], cmap='Greens'), use_container_width=True, height=600)

        df_baixo = df[df['SALDO_PAL'] < 2].sort_values(by='SALDO_PAL')
        if not df_baixo.empty:
            st.error(f"🚨 {len(df_baixo)} lotes com estoque baixo!")
            st.dataframe(df_baixo[['ID','DESCRIÇÃO','MARCA','LOTE','LOCAL','SALDO_PAL','SALDO_QTD']], use_container_width=True)
        else:
            st.success("✅ Nenhum lote crítico")

        msg_gestor = f"🖥️ DASHBOARD GESTOR {agora_br.strftime('%d/%m/%Y %H:%M')}\nTOTAL: {total_geral_qtd:,.0f} QTD = {total_geral_pal:.1f} PAL\nGALPÃO: {total_galpao:,.0f} | SALA: {total_sala:,.0f} | OFICINA: {total_oficina:,.0f}\nIDs: {total_ids} | Lotes: {total_lotes}"
        url_gestor = f"https://wa.me/?text={urllib.parse.quote(msg_gestor)}"
        st.link_button("📱 ENVIAR RESUMO GESTOR NO WHATSAPP", url_gestor, type="primary", use_container_width=True)

with tab1:
    st.subheader("📝 CADASTRO - Digita ID reconhece tudo + EDITAR/EXCLUIR")
    id_digitado_cad = st.text_input("🔍 DIGITE O ID", placeholder="Ex: 1", key="id_busca_cad_v10")
    if id_digitado_cad:
        itens = get_catalogo_por_id(id_digitado_cad)
        if itens:
            st.success(f"ID {id_digitado_cad} tem {len(itens)} cadastro(s)")

    desc_default=""; marca_default=""; qtd_default=1250.0; fab_default=date.today(); lote_default=""; id_default=id_digitado_cad.upper() if id_digitado_cad else "1"
    if st.session_state.edit_idx is not None:
        try:
            reg_edit = st.session_state.lista_cadastro[st.session_state.edit_idx]
            id_default=reg_edit.get('ID',''); desc_default=reg_edit.get('DESCRICAO',''); marca_default=reg_edit.get('MARCA',''); qtd_default=safe_float(reg_edit.get('QTD_PALETE',1250),1250); lote_default=reg_edit.get('LOTE','')
            st.warning(f"✏️ EDITANDO IDX {st.session_state.edit_idx}")
        except: st.session_state.edit_idx=None
    elif id_digitado_cad:
        ultimo = get_ultimo_catalogo_por_id(id_digitado_cad)
        if ultimo:
            desc_default=ultimo.get('DESCRICAO',''); marca_default=ultimo.get('MARCA',''); qtd_default=safe_float(ultimo.get('QTD_PALETE',1250),1250)

    with st.form("form_cad_v10", clear_on_submit=False):
        c1,c2=st.columns([2,1])
        with c1:
            id_in=st.text_input("ID*", value=id_default)
            desc_in=st.text_input("DESCRIÇÃO*", value=desc_default)
            marca_in=st.text_input("MARCA*", value=marca_default)
            lote_in=st.text_input("LOTE (OPCIONAL)", value=lote_default)
        with c2:
            st.markdown("### 📍 ONDE CADASTRAR?")
            check_galpao = st.checkbox(LOCAL_GALPAO, value=True, key="chk_g_cad10")
            check_sala = st.checkbox(LOCAL_SALA, value=False, key="chk_s_cad10")
            check_oficina = st.checkbox(LOCAL_OFICINA, value=False, key="chk_o_cad10")
        c3,c4,c5=st.columns(3)
        with c3:
            fab_in=st.date_input("FABRICAÇÃO*", value=fab_default)
            tempo_in=st.number_input("VALIDADE MESES*", value=12, min_value=1)
        with c4:
            unidade_in=st.selectbox("UNIDADE*", ["KG","UNIDADE","SACO","BLOCO","TIJOLO","LATA","CAIXA","METRO","LITRO"], index=0)
            qtd_in=st.number_input(f"QTD/PALETE*", value=float(qtd_default))
        with c5:
            ent_in=st.number_input("QTD PALETES", value=0.0)

        locais_selecionados = []
        if check_galpao: locais_selecionados.append(LOCAL_GALPAO)
        if check_sala: locais_selecionados.append(LOCAL_SALA)
        if check_oficina: locais_selecionados.append(LOCAL_OFICINA)

        col_btn1,col_btn2 = st.columns(2)
        with col_btn1:
            btn_salvar = st.form_submit_button(f"💾 {'ATUALIZAR' if st.session_state.edit_idx is not None else 'CADASTRAR'} EM {len(locais_selecionados)} LOCAL(IS)", type="primary", use_container_width=True)
        with col_btn2:
            btn_cancel = st.form_submit_button("❌ CANCELAR", use_container_width=True)

        if btn_cancel:
            st.session_state.edit_idx=None; st.rerun()

        if btn_salvar:
            if not id_in.strip() or not desc_in.strip() or not marca_in.strip():
                st.error("ID, Descrição e Marca obrigatórios")
            elif not locais_selecionados and st.session_state.edit_idx is None:
                st.error("Selecione pelo menos 1 local")
            else:
                fab_str=fab_in.strftime("%d/%m/%Y"); valido=calcular_valido_ate(fab_str, tempo_in); total=safe_float(qtd_in)*safe_float(ent_in) if lote_in.strip() else 0
                if st.session_state.edit_idx is not None:
                    st.session_state.lista_cadastro[st.session_state.edit_idx] = {"ID":id_in.strip().upper(),"DESCRICAO":desc_in.upper().strip(),"MARCA":marca_in.upper().strip(),"LOTE":lote_in.strip().upper(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido,"QTD_PALETE":safe_float(qtd_in),"ENTRADA":safe_float(ent_in),"TOTAL":total,"UNIDADE":unidade_in.upper(),"LOCAL":locais_selecionados[0] if locais_selecionados else LOCAL_GALPAO,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")}
                    st.session_state.edit_idx=None
                else:
                    for local_sel in locais_selecionados:
                        st.session_state.lista_cadastro.append({"ID":id_in.strip().upper(),"DESCRICAO":desc_in.upper().strip(),"MARCA":marca_in.upper().strip(),"LOTE":lote_in.strip().upper(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido,"QTD_PALETE":safe_float(qtd_in),"ENTRADA":safe_float(ent_in),"TOTAL":total,"UNIDADE":unidade_in.upper(),"LOCAL":local_sel,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                st.rerun()

    if st.session_state.lista_cadastro:
        lista_filtrada = st.session_state.lista_cadastro
        if id_digitado_cad:
            lista_filtrada = [r for r in st.session_state.lista_cadastro if id_digitado_cad.upper() in str(r.get('ID','')).upper()]
        for idx_real, reg in enumerate(st.session_state.lista_cadastro):
            if id_digitado_cad and reg not in lista_filtrada: continue
            c1,c2,c3,c4 = st.columns([3,3,1,1])
            with c1: st.write(f"**ID {reg.get('ID')}** | {reg.get('DESCRICAO')} | {reg.get('MARCA')} | {reg.get('LOTE')}")
            with c2: st.write(f"{reg.get('LOCAL')} | {reg.get('QTD_PALETE')} {reg.get('UNIDADE')}")
            with c3:
                if st.button("✏️ EDITAR", key=f"edit10_{idx_real}", use_container_width=True):
                    st.session_state.edit_idx=idx_real; st.rerun()
            with c4:
                if st.button("🗑️ EXCLUIR", key=f"del10_{idx_real}", type="primary", use_container_width=True):
                    st.session_state.lista_cadastro.pop(idx_real)
                    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                    st.rerun()

with tab2:
    st.subheader("🔄 MOVIMENTAÇÃO")
    ids_disponiveis = sorted(list(set([str(r.get('ID','')).strip().upper() for r in st.session_state.lista_cadastro if r.get('ID')])))
    id_busca_mov = st.text_input("🔍 DIGITE O ID", key="busca_id_mov10")
    if not ids_disponiveis: st.warning("Cadastre ID primeiro")
    else:
        c1,c2=st.columns(2)
        with c1:
            id_mov_sel = st.selectbox("ID*", options=ids_disponiveis, index=ids_disponiveis.index(id_busca_mov.upper()) if id_busca_mov and id_busca_mov.upper() in ids_disponiveis else 0)
            catalogo = get_ultimo_catalogo_por_id(id_mov_sel)
            desc_mov_auto = catalogo.get('DESCRICAO','') if catalogo else ""
            st.text_input("DESCRIÇÃO (auto)", value=desc_mov_auto, disabled=True)
            lote_mov = st.text_input(f"LOTE*")
            marca_mov=st.selectbox("MARCA*", options=sorted(list(set([str(r.get('MARCA','')).upper() for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==id_mov_sel.upper()]))))
            local_mov=st.selectbox("LOCAL ORIGEM*", LOCAIS)
        with c2:
            tipo_mov=st.selectbox("TIPO*", ["ENTRADA","SAIDA","TRANSFERENCIA"])
            paletes_mov=st.number_input(f"QTD PALETES", value=1.0, min_value=0.1, step=0.5)
            qtd_base=safe_float(catalogo.get('QTD_PALETE',1250),1250) if catalogo else 1250
            unidade_base=catalogo.get('UNIDADE','KG') if catalogo else "KG"
            st.metric(f"TOTAL {unidade_base}", f"{safe_float(paletes_mov)*qtd_base:,.0f}")
            local_dest = st.selectbox("Destino TRANSFER", LOCAIS, index=1)
            fab_mov = st.date_input("FABRICAÇÃO LOTE", value=date.today())
            tempo_mov = st.number_input("Validade meses", value=12, min_value=1)
            valido_mov = calcular_valido_ate(fab_mov.strftime("%d/%m/%Y"), tempo_mov)
            motivo=st.text_input("MOTIVO*","REFORMA FORNO")
        if st.button("✅ CONFIRMAR", type="primary", use_container_width=True):
            if not lote_mov.strip():
                st.error("LOTE obrigatório")
            else:
                desc_final = catalogo.get('DESCRICAO','') if catalogo else ""
                total_qtd_mov=safe_float(paletes_mov)*qtd_base
                if tipo_mov=="ENTRADA":
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"DESCRICAO":desc_final,"TIPO":"ENTRADA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"FABRICACAO":fab_mov.strftime("%d/%m/%Y"),"VALIDO_ATE":valido_mov,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"ENTRADA"})
                elif tipo_mov=="SAIDA":
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"DESCRICAO":desc_final,"TIPO":"SAIDA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"SAIDA"})
                else:
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"DESCRICAO":desc_final,"TIPO":"SAIDA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"MOTIVO":f"TRANSFER -> {local_dest}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"TRANSFER"})
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"DESCRICAO":desc_final,"TIPO":"ENTRADA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"FABRICACAO":fab_mov.strftime("%d/%m/%Y"),"VALIDO_ATE":valido_mov,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_dest,"OBS":f"TRANSFER"})
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success("OK"); st.rerun()

with tab3:
    saldos=get_saldos_completos()
    df_estoque=[{"ID":r.get('ID'),"DESCRIÇÃO":r.get('DESCRICAO'),"LOTE":r.get('LOTE_ORIG'),"MARCA":r.get('MARCA'),"LOCAL":r.get('LOCAL'),"FAB":r.get('FABRICACAO'),"SALDO PAL":safe_float(r.get('SALDO_PALETES',0)),"SALDO QTD":safe_float(r.get('SALDO_QTD',0))} for r in saldos.values() if safe_float(r.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(df_estoque)
    if not df.empty: st.dataframe(df.sort_values(by=['ID','LOCAL']), use_container_width=True, height=600)
    else: st.info("Sem estoque")

with tab4:
    id_busca = st.text_input("🔍 Digite o ID", key="busca_tab4_10")
    if id_busca:
        dados = buscar_por_id(id_busca)
        cat = get_ultimo_catalogo_por_id(id_busca)
        desc_busca = cat.get('DESCRICAO','') if cat else (dados[0].get('DESCRICAO','') if dados else "")
        if dados:
            df_busca = pd.DataFrame([{"ID": d.get('ID'),"DESCRIÇÃO": d.get('DESCRICAO'),"LOTE": d.get('LOTE_ORIG'),"MARCA": d.get('MARCA'),"LOCAL": d.get('LOCAL'),"FAB": d.get('FABRICACAO'),"SALDO QTD": safe_float(d.get('SALDO_QTD',0)),"SALDO PAL": safe_float(d.get('SALDO_PALETES',0))} for d in dados])
            total_qtd = df_busca['SALDO QTD'].sum()
            msg_zap = f"ID {id_busca} - {desc_busca}\nTOTAL: {total_qtd:,.0f}\n" + "\n".join([f"- {r['MARCA']} {r['LOTE']} {r['LOCAL']} {r['SALDO QTD']:,.0f}" for _,r in df_busca.iterrows()])
            url_zap = f"https://wa.me/?text={urllib.parse.quote(msg_zap)}"
            c1,c2=st.columns([3,1])
            with c1: st.success(f"ID {id_busca} - {desc_busca} | TOTAL: {total_qtd:,.0f} | {len(df_busca)} lotes")
            with c2: st.link_button("📱 ZAP", url_zap, type="primary", use_container_width=True)
            st.dataframe(df_busca, use_container_width=True)
            fig = px.bar(df_busca, x='LOCAL', y='SALDO QTD', color='MARCA', barmode='group', text='SALDO QTD', title=f'ID {id_busca} - {desc_busca}')
            fig.update_traces(textposition='outside', textfont_size=16, textfont_family="Arial Black")
            st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("📦 GRD - Guia + WhatsApp")
    ids_disponiveis = sorted(list(set([str(r.get('ID','')).strip().upper() for r in st.session_state.lista_cadastro if r.get('ID')])))
    if ids_disponiveis:
        col_grd1,col_grd2=st.columns(2)
        with col_grd1:
            id_grd = st.selectbox("ID* (GRD)", options=ids_disponiveis, key="id_grd10")
            cat_grd = get_ultimo_catalogo_por_id(id_grd)
            desc_grd = cat_grd.get('DESCRICAO','') if cat_grd else ""
            st.text_input("Descrição", value=desc_grd, disabled=True)
            lote_grd = st.text_input("Lote GRD*", key="lote_grd10")
            marca_grd = st.selectbox("Marca GRD*", options=sorted(list(set([str(r.get('MARCA','')).upper() for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==id_grd.upper()]))))
            qtd_grd = st.number_input("Qtd Paletes GRD*", value=1.0, min_value=0.1)
        with col_grd2:
            origem_grd = st.selectbox("Origem*", LOCAIS, key="origem_grd10")
            destino_grd = st.selectbox("Destino*", [l for l in LOCAIS if l!=origem_grd], key="destino_grd10")
            os_grd = st.text_input("OS / Forno*", key="os_grd10")
            resp_grd = st.text_input("Responsável*", value="OPERADOR")
            num_grd = f"GRD-{datetime.now(fuso).strftime('%Y%m%d%H%M%S')}"

        if st.button("✅ GERAR GRD", type="primary", use_container_width=True):
            if not lote_grd: st.error("Lote obrigatório")
            else:
                qtd_base_grd = safe_float(cat_grd.get('QTD_PALETE',1250),1250) if cat_grd else 1250
                unidade_grd = cat_grd.get('UNIDADE','KG') if cat_grd else "KG"
                total_grd = safe_float(qtd_grd)*qtd_base_grd
                registro_grd = {"NUM_GRD":num_grd,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"ID":id_grd,"DESCRICAO":desc_grd,"LOTE":lote_grd.upper(),"MARCA":marca_grd,"QTD_PALETES":qtd_grd,"TOTAL_QTD":total_grd,"UNIDADE":unidade_grd,"ORIGEM":origem_grd,"DESTINO":destino_grd,"RESPONSAVEL":resp_grd,"OS":os_grd}
                st.session_state.lista_grd.append(registro_grd)
                pd.DataFrame(st.session_state.lista_grd).to_csv(ARQ_GRD,index=False)
                st.session_state.lista_mov.append({"ID":id_grd,"LOTE":lote_grd.upper(),"MARCA":marca_grd,"DESCRICAO":desc_grd,"TIPO":"SAIDA","PALETES":qtd_grd,"QTD_POR_PALETE":qtd_base_grd,"TOTAL_QTD":total_grd,"UNIDADE":unidade_grd,"MOTIVO":f"GRD {num_grd}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":origem_grd,"OBS":f"GRD {num_grd}"})
                st.session_state.lista_mov.append({"ID":id_grd,"LOTE":lote_grd.upper(),"MARCA":marca_grd,"DESCRICAO":desc_grd,"TIPO":"ENTRADA","PALETES":qtd_grd,"QTD_POR_PALETE":qtd_base_grd,"TOTAL_QTD":total_grd,"UNIDADE":unidade_grd,"FABRICACAO":date.today().strftime("%d/%m/%Y"),"VALIDO_ATE":calcular_valido_ate(date.today().strftime("%d/%m/%Y"),12),"MOTIVO":f"GRD {num_grd}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":destino_grd,"OBS":f"GRD {num_grd}"})
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success(f"✅ GRD {num_grd} gerada")
        if st.session_state.lista_grd:
            df_grd = pd.DataFrame(st.session_state.lista_grd)
            st.dataframe(df_grd.sort_values(by='NUM_GRD', ascending=False), use_container_width=True)
            if not df_grd.empty:
                ultima = df_grd.iloc[-1]
                msg_grd = f"📦 GRD {ultima.get('NUM_GRD')} - {ultima.get('DATA')} {ultima.get('HORA')}\nID {ultima.get('ID')} - {ultima.get('DESCRICAO')}\n{ultima.get('QTD_PALETES')} PAL = {ultima.get('TOTAL_QTD')} {ultima.get('UNIDADE')}\n{ultima.get('ORIGEM')} -> {ultima.get('DESTINO')}\nOS {ultima.get('OS')}"
                st.link_button("📱 ENVIAR GRD NO ZAP", f"https://wa.me/?text={urllib.parse.quote(msg_grd)}", type="primary", use_container_width=True)

with tab6:
    st.subheader("📈 Gráficos Gestor - Números Visíveis")
    saldos=get_saldos_completos()
    lista=[{"ID":d.get('ID'),"DESCRIÇÃO":d.get('DESCRICAO'),"LOCAL":d.get('LOCAL'),"MARCA":d.get('MARCA'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0)),"SALDO_PAL":safe_float(d.get('SALDO_PALETES',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)
    if not df.empty:
        df['ID_DESC'] = df['ID'] + " - " + df['DESCRIÇÃO']
        df['TEXTO'] = df['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
        fig1=px.bar(df.groupby('ID_DESC')[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(20), x='ID_DESC', y='SALDO_QTD', text='TEXTO', title="TOP 20 IDs - Números Visíveis", color='SALDO_QTD')
        fig1.update_traces(textposition='outside', textfont_size=14, textfont_family="Arial Black")
        fig1.update_layout(height=700, xaxis_tickangle=-30)
        st.plotly_chart(fig1, use_container_width=True)

        c1,c2=st.columns(2)
        with c1:
            df_local = df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index()
            df_local['TEXTO'] = df_local['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig2=px.bar(df_local, x='LOCAL', y='SALDO_QTD', text='TEXTO', title="Saldo por Local - Números Visíveis", color='LOCAL')
            fig2.update_traces(textposition='outside', textfont_size=18, textfont_family="Arial Black")
            st.plotly_chart(fig2, use_container_width=True)
        with c2:
            df_marca = df.groupby('MARCA')[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(10)
            df_marca['TEXTO'] = df_marca['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig3=px.bar(df_marca, x='MARCA', y='SALDO_QTD', text='TEXTO', title="Top Marcas", color='MARCA')
            fig3.update_traces(textposition='outside', textfont_size=16)
            st.plotly_chart(fig3, use_container_width=True)

        fig_pizza = px.pie(df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index(), values='SALDO_QTD', names='LOCAL', title="Distribuição 3 Locais", hole=0.3)
        fig_pizza.update_traces(textinfo='value+percent+label', textfont_size=18, textfont_family="Arial Black")
        st.plotly_chart(fig_pizza, use_container_width=True)

st.caption(f"V10 DASHBOARD 24H - Números gigantes - TV sempre ligada - Brasília {agora_br.strftime('%d/%m/%Y %H:%M:%S')}")
