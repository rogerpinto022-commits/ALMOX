import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="REFORMA DE FORNOS V6", layout="wide", page_icon="🔥")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_EMAILS = "emails.csv"

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
        if "LOCAL" not in df.columns: df["LOCAL"] = LOCAL_GALPAO
        if "MARCA" not in df.columns: df["MARCA"] = "SEM MARCA"
        return df.to_dict('records')
    except:
        try: os.remove(caminho)
        except: pass
        return []

if 'lista_cadastro' not in st.session_state: st.session_state.lista_cadastro=carregar_seguro(ARQ_CAD)
if 'lista_mov' not in st.session_state: st.session_state.lista_mov=carregar_seguro(ARQ_MOV)
if 'logado' not in st.session_state: st.session_state.logado=False

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
st.sidebar.subheader("⚙️ Controles")
auto = st.sidebar.toggle("🔄 AUTO 10s", value=False)
if auto: components.html("""<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>""", height=0)
manter = st.sidebar.toggle("🔒 MANTER ABERTO", value=True)
if manter: components.html("""<script>let wakeLock=null; async function requestLock(){ try{ if('wakeLock' in navigator){ wakeLock=await navigator.wakeLock.request('screen'); } }catch(e){} } requestLock();</script>""", height=0)
if st.sidebar.button("🔴 FECHAR", type="primary", use_container_width=True):
    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
    pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
    st.session_state.clear(); st.stop()

def calcular_valido_ate(fab_str, tempo_meses):
    try:
        fab=datetime.strptime(fab_str, "%d/%m/%Y")
        valido=fab + relativedelta(months=int(safe_float(tempo_meses,12)))
        return valido.strftime("%d/%m/%Y")
    except: return "00/00/0000"

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
            saldos[chave]=r.copy()
            saldos[chave]['ID']=id_prod; saldos[chave]['LOCAL']=local; saldos[chave]['MARCA']=marca; saldos[chave]['LOTE_ORIG']=lote
            saldos[chave]['SALDO_PALETES']=entrada_pal; saldos[chave]['SALDO_QTD']=total
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
        chave = f"{id_prod}__{local_mov}__{marca}__{lote}"
        if chave not in saldos and tipo=="ENTRADA":
            saldos[chave]={'ID':id_prod,'LOCAL':local_mov,'MARCA':marca,'LOTE_ORIG':lote,'DESCRICAO':m.get('DESCRICAO',''),'FABRICACAO':m.get('FABRICACAO',''),'VALIDO_ATE':m.get('VALIDO_ATE',''),'UNIDADE':m.get('UNIDADE','KG'),'QTD_PALETE_BASE':safe_float(m.get('QTD_POR_PALETE',0)),'SALDO_PALETES':0,'SALDO_QTD':0}
        if chave not in saldos: continue
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

def get_catalogo_por_id(id_digitado):
    id_digitado=str(id_digitado).strip().upper()
    itens=[r for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==id_digitado]
    return itens[-1] if itens else None

st.markdown(f"<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00;'>🔥 REFORMA DE FORNOS | {agora_br.strftime('%d/%m/%Y %H:%M')} Brasília 🔥</h1>", unsafe_allow_html=True)
tab1,tab2,tab3,tab4,tab5=st.tabs(["📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 ESTOQUE","📊 BUSCA POR ID","📈 GRAFICOS"])

with tab1:
    st.subheader("📝 CADASTRO - AUTO PREENCHIMENTO PELO ID (Lote opcional)")
    id_digitado_cad = st.text_input("Digite o ID para puxar último cadastro", placeholder="Ex: 1", key="id_busca_cad")
    desc_default=""; marca_default=""; qtd_default=1250.0; unidade_default="KG"; tempo_default=12; local_default=LOCAL_GALPAO; fab_default=date.today()
    if id_digitado_cad:
        ultimo = get_catalogo_por_id(id_digitado_cad)
        if ultimo:
            desc_default=ultimo.get('DESCRICAO',''); marca_default=ultimo.get('MARCA','')
            qtd_default=safe_float(ultimo.get('QTD_PALETE',1250),1250); unidade_default=ultimo.get('UNIDADE','KG')
            tempo_default=int(safe_float(ultimo.get('TEMPO_VALIDADE',12),12)); local_default=ultimo.get('LOCAL',LOCAL_GALPAO)
            st.success(f"✅ ID {id_digitado_cad} encontrado! Puxando: {desc_default} | Marca {marca_default}")
    with st.form("form_cad", clear_on_submit=False):
        c1,c2,c3=st.columns(3)
        with c1:
            id_in=st.text_input("ID* (obrigatório)", value=id_digitado_cad.upper() if id_digitado_cad else "1")
            desc_in=st.text_input("DESCRIÇÃO*", value=desc_default)
            marca_in=st.text_input("MARCA* (1 ID pode ter várias)", value=marca_default)
            lote_in=st.text_input("LOTE (OPCIONAL aqui)", value="", placeholder="Deixe em branco")
            local_in=st.selectbox("LOCAL*", LOCAIS, index=LOCAIS.index(local_default) if local_default in LOCAIS else 0)
        with c2:
            fab_in=st.date_input("FABRICAÇÃO*", value=fab_default)
            tempo_in=st.number_input("VALIDADE MESES*", value=tempo_default, min_value=1)
            unidade_in=st.selectbox("UNIDADE*", ["KG","UNIDADE","SACO","BLOCO","TIJOLO","LATA","CAIXA","METRO","LITRO"], index=0)
            qtd_in=st.number_input(f"QTD/PALETE*", value=float(qtd_default))
        with c3:
            ent_in=st.number_input("QTD PALETES (se tiver lote)", value=0.0)
            if safe_float(qtd_in)>0 and safe_float(ent_in)>0:
                st.metric(f"TOTAL", f"{safe_float(qtd_in)*safe_float(ent_in):,.0f}")
        if st.form_submit_button("💾 CADASTRAR CATÁLOGO", type="primary", use_container_width=True):
            if not id_in.strip() or not desc_in.strip() or not marca_in.strip():
                st.error("ID, Descrição e Marca obrigatórios")
            else:
                fab_str=fab_in.strftime("%d/%m/%Y"); valido=calcular_valido_ate(fab_str, tempo_in)
                total=safe_float(qtd_in)*safe_float(ent_in) if lote_in.strip() else 0
                st.session_state.lista_cadastro.append({"ID":id_in.strip().upper(),"DESCRICAO":desc_in.upper().strip(),"MARCA":marca_in.upper().strip(),"LOTE":lote_in.strip().upper(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido,"QTD_PALETE":safe_float(qtd_in),"ENTRADA":safe_float(ent_in),"TOTAL":total,"UNIDADE":unidade_in.upper(),"LOCAL":local_in,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                st.success(f"✅ ID {id_in} salvo!"); st.rerun()

with tab2:
    st.subheader("🔄 MOVIMENTAÇÃO - AQUI NASCE O LOTE")
    ids_disponiveis = sorted(list(set([str(r.get('ID','')).strip().upper() for r in st.session_state.lista_cadastro if r.get('ID')])))
    id_busca_mov = st.text_input("🔍 DIGITE O ID PARA PUXAR", placeholder="Ex: 1", key="busca_id_mov")
    if not ids_disponiveis: st.warning("Cadastre ID primeiro")
    else:
        c1,c2,c3=st.columns(3)
        with c1:
            id_mov_sel = st.selectbox("ID*", options=ids_disponiveis, index=ids_disponiveis.index(id_busca_mov.upper()) if id_busca_mov and id_busca_mov.upper() in ids_disponiveis else 0)
            catalogo = get_catalogo_por_id(id_mov_sel)
            marcas_do_id = sorted(list(set([str(r.get('MARCA','')).upper() for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==id_mov_sel.upper()])))
            saldos_atual = get_saldos_completos()
            lotes_existentes = sorted(list(set([d.get('LOTE_ORIG','') for d in saldos_atual.values() if d.get('ID','').upper()==id_mov_sel.upper()])))
            lote_mov = st.text_input(f"LOTE* (novo ou existente)", placeholder="Ex: LOTE001")
            marca_mov=st.selectbox("MARCA*", options=marcas_do_id if marcas_do_id else ["SEM MARCA"])
            qtd_base=safe_float(catalogo.get('QTD_PALETE',1250),1250) if catalogo else 1250
            unidade_base=catalogo.get('UNIDADE','KG') if catalogo else "KG"
            local_mov=st.selectbox("LOCAL ORIGEM*", LOCAIS)
        with c2:
            tipo_mov=st.selectbox("TIPO*", ["ENTRADA","SAIDA","TRANSFERENCIA"])
            paletes_mov=st.number_input(f"QTD PALETES", value=1.0, min_value=0.1, step=0.5)
            total_qtd_mov=safe_float(paletes_mov)*safe_float(qtd_base)
            st.metric(f"TOTAL {unidade_base}", f"{total_qtd_mov:,.0f}")
            local_dest = st.selectbox("Destino TRANSFER", LOCAIS, index=1)
            fab_mov = st.date_input("FABRICAÇÃO LOTE (FIFO)", value=date.today())
            tempo_mov = st.number_input("Validade meses", value=int(catalogo.get('TEMPO_VALIDADE',12)) if catalogo else 12, min_value=1)
            valido_mov = calcular_valido_ate(fab_mov.strftime("%d/%m/%Y"), tempo_mov)
        with c3:
            motivo=st.text_input("MOTIVO*","REFORMA FORNO")
            chave_atual=f"{id_mov_sel.upper()}__{local_mov}__{marca_mov}__{lote_mov.upper()}"
            saldo_atual=get_saldos_completos().get(chave_atual,{})
            if saldo_atual: st.metric(f"SALDO", f"{safe_float(saldo_atual.get('SALDO_PALETES',0)):.1f} PAL")
        if st.button("✅ CONFIRMAR (LOTE NASCE AQUI)", type="primary", use_container_width=True):
            if not lote_mov.strip():
                st.error("LOTE obrigatório na movimentação")
            else:
                if tipo_mov=="ENTRADA":
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"DESCRICAO":catalogo.get('DESCRICAO','') if catalogo else "","TIPO":"ENTRADA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"FABRICACAO":fab_mov.strftime("%d/%m/%Y"),"VALIDO_ATE":valido_mov,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"ENTRADA LOTE {lote_mov}"})
                elif tipo_mov=="SAIDA":
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"TIPO":"SAIDA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"SAIDA"})
                else:
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"TIPO":"SAIDA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"MOTIVO":f"TRANSFER -> {local_dest}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"TRANSFER"})
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov.strip().upper(),"MARCA":marca_mov.upper(),"DESCRICAO":catalogo.get('DESCRICAO','') if catalogo else "","TIPO":"ENTRADA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"FABRICACAO":fab_mov.strftime("%d/%m/%Y"),"VALIDO_ATE":valido_mov,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_dest,"OBS":f"TRANSFER"})
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success("✅ OK"); st.rerun()

with tab3:
    saldos=get_saldos_completos()
    df_estoque=[{"ID":r.get('ID'),"LOTE":r.get('LOTE_ORIG'),"MARCA":r.get('MARCA'),"LOCAL":r.get('LOCAL'),"FAB":r.get('FABRICACAO'),"SALDO PAL":safe_float(r.get('SALDO_PALETES',0)),"SALDO QTD":safe_float(r.get('SALDO_QTD',0))} for r in saldos.values() if safe_float(r.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(df_estoque)
    if not df.empty: st.dataframe(df, use_container_width=True, height=600)
    else: st.info("Sem estoque")

with tab4:
    id_busca = st.text_input("Digite o ID", key="busca_tab4")
    if id_busca:
        dados = buscar_por_id(id_busca)
        if dados:
            df_busca = pd.DataFrame([{"ID": d.get('ID'),"LOTE": d.get('LOTE_ORIG'),"MARCA": d.get('MARCA'),"LOCAL": d.get('LOCAL'),"FAB": d.get('FABRICACAO'),"SALDO QTD": safe_float(d.get('SALDO_QTD',0))} for d in dados])
            st.success(f"TOTAL ID {id_busca}: {df_busca['SALDO QTD'].sum():,.0f}")
            st.dataframe(df_busca, use_container_width=True)
            fig = px.bar(df_busca, x='LOCAL', y='SALDO QTD', color='MARCA', barmode='group', title=f'ID {id_busca}')
            st.plotly_chart(fig, use_container_width=True)

with tab5:
    saldos=get_saldos_completos()
    lista=[{"ID":d.get('ID'),"LOCAL":d.get('LOCAL'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)
    if not df.empty:
        fig1=px.bar(df, x='ID', y='SALDO_QTD', color='LOCAL', barmode="group", title="Saldo por ID - 3 locais")
        st.plotly_chart(fig1, use_container_width=True)
