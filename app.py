import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit.components.v1 as components
import urllib.parse

st.set_page_config(page_title="REFORMA FORNOS FINAL OK", layout="wide", page_icon="🔥")
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
    e = st.text_input("Email login", key="email_login").lower().strip()
    s = st.text_input("Senha login", type="password", key="senha_login")
    if st.button("Entrar", type="primary", key="btn_login"):
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
auto = st.sidebar.toggle("🔄 AUTO 10s (TV)", value=True, key="auto_toggle")
if auto:
    components.html("<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>", height=0)
manter = st.sidebar.toggle("🔒 MANTER LIGADO", value=True, key="manter_toggle")
if manter:
    components.html("<script>let w=null;async function r(){try{if('wakeLock' in navigator){w=await navigator.wakeLock.request('screen');}}catch(e){}}r();</script>", height=0)
if st.sidebar.button("🔴 FECHAR / BACKUP", type="primary", use_container_width=True, key="btn_fechar"):
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

st.markdown(f"<h1 style='text-align:center; background:#000; color:#00ff66; padding:15px; border-radius:12px; border:4px solid #ff4e00;'>🔥 REFORMA DE FORNOS | {agora_br.strftime('%d/%m/%Y %H:%M:%S')} | FINAL OK 🔥</h1>", unsafe_allow_html=True)

tab_dash, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🖥️ DASHBOARD 24H","📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 ESTOQUE","📊 BUSCA POR ID","📦 GRD + ZAP","📈 GRAFICOS"])

with tab_dash:
    st.subheader("🖥️ DASHBOARD 24H - GESTOR")
    saldos = get_saldos_completos()
    lista=[{"ID":d.get('ID'),"DESCRIÇÃO":d.get('DESCRICAO'),"LOCAL":d.get('LOCAL'),"MARCA":d.get('MARCA'),"LOTE":d.get('LOTE_ORIG'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0)),"SALDO_PAL":safe_float(d.get('SALDO_PALETES',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)
    if df.empty:
        st.warning("Sem estoque")
    else:
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: st.metric("TOTAL GERAL", f"{df['SALDO_QTD'].sum():,.0f}")
        with c2: st.metric("PALETES", f"{df['SALDO_PAL'].sum():.1f}")
        with c3: st.metric("GALPAO", f"{df[df['LOCAL']==LOCAL_GALPAO]['SALDO_QTD'].sum():,.0f}")
        with c4: st.metric("SALA ANEXA", f"{df[df['LOCAL']==LOCAL_SALA]['SALDO_QTD'].sum():,.0f}")
        with c5: st.metric("OFICINA", f"{df[df['LOCAL']==LOCAL_OFICINA]['SALDO_QTD'].sum():,.0f}")
        df_id = df.groupby(['ID','DESCRIÇÃO'])[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(10)
        df_id['ID_DESC'] = df_id['ID'] + " - " + df_id['DESCRIÇÃO'].str[:15]
        df_id['TEXTO'] = df_id['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
        fig = px.bar(df_id, x='ID_DESC', y='SALDO_QTD', text='TEXTO', title="TOP 10 IDs")
        fig.update_traces(textposition='outside', textfont_size=16)
        st.plotly_chart(fig, use_container_width=True)
        df_local = df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index()
        fig2 = px.pie(df_local, values='SALDO_QTD', names='LOCAL', title="POR LOCAL", hole=0.4)
        fig2.update_traces(textinfo='value+percent+label', textfont_size=16)
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df.sort_values(by='SALDO_QTD', ascending=False), use_container_width=True, height=400)

with tab1:
    st.subheader("📝 CADASTRO - EDITAR/EXCLUIR + MULTILOCAL")
    id_busca = st.text_input("🔍 DIGITE ID PARA RECONHECER", key="cad_busca_key_final", placeholder="Ex: 1")
    desc_default=""; marca_default=""; qtd_default=1250.0; id_default=id_busca.upper() if id_busca else "1"; lote_default=""
    if st.session_state.edit_idx is not None:
        try:
            reg=st.session_state.lista_cadastro[st.session_state.edit_idx]
            id_default=reg.get('ID',''); desc_default=reg.get('DESCRICAO',''); marca_default=reg.get('MARCA',''); qtd_default=safe_float(reg.get('QTD_PALETE',1250),1250); lote_default=reg.get('LOTE','')
            st.warning(f"EDITANDO IDX {st.session_state.edit_idx}")
        except: st.session_state.edit_idx=None
    elif id_busca:
        ult=get_ultimo_catalogo_por_id(id_busca)
        if ult: desc_default=ult.get('DESCRICAO',''); marca_default=ult.get('MARCA','')
    with st.form("form_cad_final_ok"):
        c1,c2=st.columns([2,1])
        with c1:
            id_in=st.text_input("ID* categoria", value=id_default, key="id_cad_final")
            desc_in=st.text_input("DESCRIÇÃO* mostra tudo", value=desc_default, key="desc_cad_final")
            marca_in=st.text_input("MARCA* varias", value=marca_default, key="marca_cad_final")
            lote_in=st.text_input("LOTE OPCIONAL", value=lote_default, key="lote_cad_final")
        with c2:
            st.markdown("📍 ONDE CADASTRAR?")
            chk1=st.checkbox(LOCAL_GALPAO, value=True, key="chk_galpao_final")
            chk2=st.checkbox(LOCAL_SALA, value=False, key="chk_sala_final")
            chk3=st.checkbox(LOCAL_OFICINA, value=False, key="chk_oficina_final")
        c3,c4,c5=st.columns(3)
        with c3:
            fab_in=st.date_input("FABRICAÇÃO*", value=date.today(), key="fab_cad_final")
            tempo_in=st.number_input("VALIDADE MESES*", value=12, min_value=1, key="tempo_cad_final")
        with c4:
            un_in=st.selectbox("UNIDADE*", ["KG","UNIDADE","SACO","BLOCO","TIJOLO","LATA","CAIXA"], key="un_cad_final")
            qtd_in=st.number_input("QTD/PALETE*", value=float(qtd_default), key="qtd_cad_final")
        with c5:
            ent_in=st.number_input("QTD PALETES", value=0.0, key="ent_cad_final")
        locs=[]
        if chk1: locs.append(LOCAL_GALPAO)
        if chk2: locs.append(LOCAL_SALA)
        if chk3: locs.append(LOCAL_OFICINA)
        b1,b2=st.columns(2)
        with b1: btn=st.form_submit_button("💾 CADASTRAR", type="primary", use_container_width=True)
        with b2: btn_c=st.form_submit_button("❌ CANCELAR", use_container_width=True)
        if btn_c: st.session_state.edit_idx=None; st.rerun()
        if btn:
            if not id_in or not desc_in or not marca_in: st.error("Preencha ID, Descrição, Marca")
            elif not locs and st.session_state.edit_idx is None: st.error("Selecione local")
            else:
                fab_str=fab_in.strftime("%d/%m/%Y"); val=calcular_valido_ate(fab_str, tempo_in); tot=safe_float(qtd_in)*safe_float(ent_in) if lote_in else 0
                if st.session_state.edit_idx is not None:
                    st.session_state.lista_cadastro[st.session_state.edit_idx]={"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":tempo_in,"VALIDO_ATE":val,"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":tot,"UNIDADE":un_in,"LOCAL":locs[0] if locs else LOCAL_GALPAO,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")}
                    st.session_state.edit_idx=None
                else:
                    for l in locs:
                        st.session_state.lista_cadastro.append({"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":tempo_in,"VALIDO_ATE":val,"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":tot,"UNIDADE":un_in,"LOCAL":l,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                st.rerun()
    st.divider()
    if st.session_state.lista_cadastro:
        for idx,reg in enumerate(st.session_state.lista_cadastro):
            if id_busca and id_busca.upper() not in str(reg.get('ID','')).upper(): continue
            c1,c2,c3,c4=st.columns([3,3,1,1])
            with c1: st.write(f"ID {reg.get('ID')} | {reg.get('DESCRICAO')} | {reg.get('MARCA')}")
            with c2: st.write(f"{reg.get('LOCAL')} | {reg.get('QTD_PALETE')} {reg.get('UNIDADE')}")
            with c3:
                if st.button("EDITAR", key=f"edit_final_{idx}", use_container_width=True): st.session_state.edit_idx=idx; st.rerun()
            with c4:
                if st.button("EXCLUIR", key=f"del_final_{idx}", type="primary", use_container_width=True): st.session_state.lista_cadastro.pop(idx); pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False); st.rerun()

with tab2:
    st.subheader("🔄 ENTRADA/SAIDA")
    ids=sorted(list(set([str(r.get('ID','')).upper() for r in st.session_state.lista_cadastro if r.get('ID')])))
    if not ids: st.warning("Cadastre ID primeiro")
    else:
        id_busca_mov=st.text_input("🔍 DIGITE ID", key="mov_busca_final", placeholder="Ex: 1")
        c1,c2=st.columns(2)
        with c1:
            id_sel=st.selectbox("ID* categoria", options=ids, index=ids.index(id_busca_mov.upper()) if id_busca_mov and id_busca_mov.upper() in ids else 0, key="id_mov_final")
            cat=get_ultimo_catalogo_por_id(id_sel)
            desc=cat.get('DESCRICAO','') if cat else ""
            st.text_input("DESCRIÇÃO AUTO", value=desc, disabled=True, key="desc_mov_final")
            lote=st.text_input("LOTE* OBRIGATORIO", placeholder="LOTE001", key="lote_mov_final")
            marca=st.selectbox("MARCA*", options=sorted(list(set([str(r.get('MARCA','')).upper() for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==id_sel]))), key="marca_mov_final")
            local_o=st.selectbox("LOCAL ORIGEM*", LOCAIS, key="local_orig_final")
        with c2:
            tipo=st.selectbox("TIPO*", ["ENTRADA","SAIDA","TRANSFERENCIA"], key="tipo_mov_final")
            pal=st.number_input("QTD PALETES", value=1.0, min_value=0.1, step=0.5, key="pal_mov_final")
            qtd_base=safe_float(cat.get('QTD_PALETE',1250),1250) if cat else 1250
            un=cat.get('UNIDADE','KG') if cat else "KG"
            st.metric(f"TOTAL {un}", f"{pal*qtd_base:,.0f}")
            dest=st.selectbox("DESTINO TRANSFER", LOCAIS, index=1, key="dest_mov_final")
            fab=st.date_input("FABRICAÇÃO LOTE FIFO", value=date.today(), key="fab_mov_final")
            tempo=st.number_input("VALIDADE MESES", value=12, min_value=1, key="tempo_mov_final")
            val=calcular_valido_ate(fab.strftime("%d/%m/%Y"), tempo)
            mot=st.text_input("MOTIVO*", value="REFORMA FORNO", key="mot_mov_final")
        if st.button("✅ CONFIRMAR MOVIMENTACAO", type="primary", use_container_width=True, key="btn_mov_final"):
            if not lote: st.error("LOTE obrigatório")
            else:
                tot=pal*qtd_base
                if tipo=="ENTRADA":
                    st.session_state.lista_mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca,"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":tot,"UNIDADE":un,"FABRICACAO":fab.strftime("%d/%m/%Y"),"VALIDO_ATE":val,"MOTIVO":mot,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_o,"OBS":f"ENTRADA {desc}"})
                elif tipo=="SAIDA":
                    st.session_state.lista_mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca,"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":tot,"UNIDADE":un,"MOTIVO":mot,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_o,"OBS":f"SAIDA {desc}"})
                else:
                    st.session_state.lista_mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca,"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":tot,"UNIDADE":un,"MOTIVO":f"TRANSFER->{dest}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_o,"OBS":f"TRANSFER {desc}"})
                    st.session_state.lista_mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca,"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":tot,"UNIDADE":un,"FABRICACAO":fab.strftime("%d/%m/%Y"),"VALIDO_ATE":val,"MOTIVO":mot,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":dest,"OBS":f"TRANSFER {desc}"})
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success("OK"); st.rerun()

with tab3:
    st.subheader("📦 ESTOQUE ATUAL")
    saldos=get_saldos_completos()
    df_est=[{"ID":r.get('ID'),"DESCRIÇÃO":r.get('DESCRICAO'),"LOTE":r.get('LOTE_ORIG'),"MARCA":r.get('MARCA'),"LOCAL":r.get('LOCAL'),"FAB":r.get('FABRICACAO'),"VALIDO":r.get('VALIDO_ATE'),"SALDO PAL":safe_float(r.get('SALDO_PALETES',0)),"SALDO QTD":safe_float(r.get('SALDO_QTD',0)),"UNIDADE":r.get('UNIDADE')} for r in saldos.values() if safe_float(r.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(df_est)
    if not df.empty: st.dataframe(df.sort_values(by=['ID','LOCAL']), use_container_width=True, height=600)
    else: st.info("Sem estoque")

with tab4:
    st.subheader("📊 BUSCA POR ID - RECONHECE TODOS")
    id_b=st.text_input("🔍 DIGITE ID", key="busca_id_final", placeholder="Ex: 1")
    if id_b:
        dados=buscar_por_id(id_b)
        cat=get_ultimo_catalogo_por_id(id_b)
        desc=cat.get('DESCRICAO','') if cat else (dados[0].get('DESCRICAO','') if dados else "")
        if dados:
            df_b=pd.DataFrame([{"ID":d.get('ID'),"DESCRIÇÃO":d.get('DESCRICAO'),"LOTE":d.get('LOTE_ORIG'),"MARCA":d.get('MARCA'),"LOCAL":d.get('LOCAL'),"FAB":d.get('FABRICACAO'),"SALDO QTD":safe_float(d.get('SALDO_QTD',0)),"SALDO PAL":safe_float(d.get('SALDO_PALETES',0))} for d in dados])
            tot=df_b['SALDO QTD'].sum()
            msg=f"ID {id_b} - {desc} TOTAL: {tot:,.0f}"
            c1,c2=st.columns([3,1])
            with c1: st.success(f"ID {id_b} - {desc} | TOTAL {tot:,.0f} | {len(df_b)} lotes")
            with c2: st.link_button("📱 ZAP", f"https://wa.me/?text={urllib.parse.quote(msg)}", type="primary", use_container_width=True, key="zap_busca_final")
            st.dataframe(df_b, use_container_width=True)
            fig=px.bar(df_b, x='LOCAL', y='SALDO QTD', color='MARCA', barmode='group', text='SALDO QTD', title=f"ID {id_b} - {desc}")
            fig.update_traces(textposition='outside', textfont_size=16)
            st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("📦 GRD - GUIA + ZAP")
    ids=sorted(list(set([str(r.get('ID','')).upper() for r in st.session_state.lista_cadastro if r.get('ID')])))
    if ids:
        c1,c2=st.columns(2)
        with c1:
            id_grd=st.selectbox("ID*", options=ids, key="grd_id_final")
            cat=get_ultimo_catalogo_por_id(id_grd)
            desc=cat.get('DESCRICAO','') if cat else ""
            st.text_input("DESCRIÇÃO GRD", value=desc, disabled=True, key="desc_grd_final")
            lote_grd=st.text_input("LOTE* GRD", key="grd_lote_final")
            marca_grd=st.selectbox("MARCA GRD*", options=sorted(list(set([str(r.get('MARCA','')).upper() for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==id_grd]))), key="grd_marca_final")
            qtd_grd=st.number_input("QTD PALETES GRD*", value=1.0, min_value=0.1, key="grd_qtd_final")
        with c2:
            ori=st.selectbox("ORIGEM* GRD", LOCAIS, key="grd_ori_final")
            dst=st.selectbox("DESTINO* GRD", [l for l in LOCAIS if l!=ori], key="grd_dst_final")
            os_grd=st.text_input("OS/FORNO*", key="grd_os_final")
            resp=st.text_input("RESPONSÁVEL*", value="OPERADOR", key="grd_resp_final")
            num=f"GRD-{datetime.now(fuso).strftime('%Y%m%d%H%M%S')}"
        if st.button("✅ GERAR GRD + BAIXA ESTOQUE", type="primary", use_container_width=True, key="btn_grd_final"):
            if not lote_grd: st.error("LOTE obrigatório")
            else:
                qb=safe_float(cat.get('QTD_PALETE',1250),1250) if cat else 1250
                un=cat.get('UNIDADE','KG') if cat else "KG"
                tot=qtd_grd*qb
                reg={"NUM_GRD":num,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"ID":id_grd,"DESCRICAO":desc,"LOTE":lote_grd.upper(),"MARCA":marca_grd,"QTD_PALETES":qtd_grd,"TOTAL_QTD":tot,"UNIDADE":un,"ORIGEM":ori,"DESTINO":dst,"RESPONSAVEL":resp,"OS":os_grd}
                st.session_state.lista_grd.append(reg)
                pd.DataFrame(st.session_state.lista_grd).to_csv(ARQ_GRD,index=False)
                st.session_state.lista_mov.append({"ID":id_grd,"LOTE":lote_grd.upper(),"MARCA":marca_grd,"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":qtd_grd,"QTD_POR_PALETE":qb,"TOTAL_QTD":tot,"UNIDADE":un,"MOTIVO":f"GRD {num}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":ori,"OBS":f"GRD {num}"})
                st.session_state.lista_mov.append({"ID":id_grd,"LOTE":lote_grd.upper(),"MARCA":marca_grd,"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":qtd_grd,"QTD_POR_PALETE":qb,"TOTAL_QTD":tot,"UNIDADE":un,"FABRICACAO":date.today().strftime("%d/%m/%Y"),"VALIDO_ATE":calcular_valido_ate(date.today().strftime("%d/%m/%Y"),12),"MOTIVO":f"GRD {num}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":dst,"OBS":f"GRD {num}"})
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success(f"GRD {num} gerada")
        if st.session_state.lista_grd:
            df_grd=pd.DataFrame(st.session_state.lista_grd)
            st.dataframe(df_grd.sort_values(by='NUM_GRD', ascending=False), use_container_width=True)
            if not df_grd.empty:
                ult=df_grd.iloc[-1]
                msg=f"GRD {ult.get('NUM_GRD')} ID {ult.get('ID')} - {ult.get('DESCRICAO')} {ult.get('QTD_PALETES')} PAL"
                st.link_button("📱 ENVIAR GRD NO ZAP", f"https://wa.me/?text={urllib.parse.quote(msg)}", type="primary", use_container_width=True, key="zap_grd_final")

with tab6:
    st.subheader("📈 GRAFICOS - NUMEROS VISIVEIS")
    saldos=get_saldos_completos()
    lista=[{"ID":d.get('ID'),"DESCRIÇÃO":d.get('DESCRICAO'),"LOCAL":d.get('LOCAL'),"MARCA":d.get('MARCA'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)
    if not df.empty:
        df['ID_DESC']=df['ID']+" - "+df['DESCRIÇÃO']
        df['TEXTO']=df['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df.groupby('ID_DESC')[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(20), x='ID_DESC', y='SALDO_QTD', text='TEXTO', title="TOP 20 IDs")
        fig.update_traces(textposition='outside', textfont_size=14)
        fig.update_layout(height=600, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
        c1,c2=st.columns(2)
        with c1:
            df_l=df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index()
            df_l['TEXTO']=df_l['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig2=px.bar(df_l, x='LOCAL', y='SALDO_QTD', text='TEXTO', title="POR LOCAL", color='LOCAL')
            fig2.update_traces(textposition='outside', textfont_size=18)
            st.plotly_chart(fig2, use_container_width=True)
        with c2:
            df_m=df.groupby('MARCA')[['SALDO_QTD']].sum().reset_index().sort_values(by='SALDO_QTD', ascending=False).head(10)
            df_m['TEXTO']=df_m['SALDO_QTD'].apply(lambda x: f"{x:,.0f}")
            fig3=px.bar(df_m, x='MARCA', y='SALDO_QTD', text='TEXTO', title="TOP MARCAS", color='MARCA')
            fig3.update_traces(textposition='outside', textfont_size=16)
            st.plotly_chart(fig3, use_container_width=True)
        fig_p=px.pie(df.groupby('LOCAL')[['SALDO_QTD']].sum().reset_index(), values='SALDO_QTD', names='LOCAL', title="DISTRIBUICAO", hole=0.3)
        fig_p.update_traces(textinfo='value+percent+label', textfont_size=16)
        st.plotly_chart(fig_p, use_container_width=True)

st.caption(f"V10.1 FINAL OK - TODAS ABAS FUNCIONANDO - {agora_br.strftime('%d/%m/%Y %H:%M:%S')}")
