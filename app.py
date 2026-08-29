import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
import plotly.express as px
from datetime import datetime as dt

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_GRD = "grd.csv"
ARQ_EMAILS = "emails.csv"

LOCAL_GALPAO = "GALPAO DE MATERIAIS REFRATARIOS"
LOCAL_SALA = "SALA ANEXA"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"
LOCAIS = [LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]
LOCAIS_ACESSO = ["AMBOS", LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]
TEMPO_QUARENTENA_HORAS = 48

def safe_float(v, d=0.0):
    try: return float(str(v).replace(",","."))
    except: return float(d)

def carregar(caminho):
    if not os.path.exists(caminho): return []
    try:
        df = pd.read_csv(caminho).fillna("")
        df.columns = [str(c).upper() for c in df.columns]
        return df.to_dict('records')
    except: return []

if 'cad' not in st.session_state: st.session_state.cad = carregar(ARQ_CAD)
if 'mov' not in st.session_state: st.session_state.mov = carregar(ARQ_MOV)
if 'grd' not in st.session_state: st.session_state.grd = carregar(ARQ_GRD)

if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)

if 'logado' not in st.session_state: st.session_state.logado=False
if 'usuario' not in st.session_state: st.session_state.usuario=None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA DE FORNOS</h1>", unsafe_allow_html=True)
    e = st.text_input("Email")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        df_e = pd.read_csv(ARQ_EMAILS)
        df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
        u = df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
        if not u.empty:
            st.session_state.logado=True
            st.session_state.usuario=u.iloc[0].to_dict()
            st.rerun()
        else: st.error("Invalido")
    st.stop()

user = st.session_state.usuario
is_admin = str(user.get('EMAIL','')).lower()=="admin@admin.com"
st.sidebar.write(f"Logado: {user.get('NOME')}")
if st.sidebar.button("Sair"):
    st.session_state.logado=False
    st.session_state.usuario=None
    st.rerun()

import streamlit.components.v1 as components
if st.sidebar.toggle("AUTO 10s TV", value=True):
    components.html("<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>", height=0)

def parse_data_hora(valor):
    try:
        if " " in str(valor) and ":" in str(valor):
            return dt.strptime(str(valor), "%d/%m/%Y %H:%M:%S")
    except: pass
    try:
        if " " in str(valor) and ":" in str(valor):
            return dt.strptime(str(valor), "%d/%m/%Y %H:%M")
    except: pass
    try: return dt.strptime(str(valor).split(" ")[0], "%d/%m/%Y")
    except: return dt.now(fuso).replace(tzinfo=None)

def get_saldos():
    saldos={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper().strip()
        lote=str(r.get('LOTE','')).upper().strip()
        if not idp or not lote: continue
        local=str(r.get('LOCAL',LOCAL_GALPAO)).upper()
        if "SALA" in local: local=LOCAL_SALA
        elif "OFIC" in local: local=LOCAL_OFICINA
        else: local=LOCAL_GALPAO
        marca=str(r.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{local}__{marca}__{lote}"
        q=safe_float(r.get('TOTAL',0))
        if q==0: q=safe_float(r.get('QTD_PALETE',0))*safe_float(r.get('ENTRADA',0))
        if chave not in saldos:
            saldos[chave]={'ID':idp,'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':q,'PAL':safe_float(r.get('ENTRADA',0)),'QTD_PAL':safe_float(r.get('QTD_PALETE',0)),'ULT_ATUAL':r.get('FABRICACAO','')}
        else:
            saldos[chave]['SALDO']+=q
            saldos[chave]['PAL']+=safe_float(r.get('ENTRADA',0))
    for m in st.session_state.mov:
        idp=str(m.get('ID','')).upper().strip()
        lote=str(m.get('LOTE','')).upper().strip()
        if not idp or not lote: continue
        local=str(m.get('LOCAL_MOV',LOCAL_GALPAO)).upper()
        if "SALA" in local: local=LOCAL_SALA
        elif "OFIC" in local: local=LOCAL_OFICINA
        else: local=LOCAL_GALPAO
        marca=str(m.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{local}__{marca}__{lote}"
        if chave not in saldos and m.get('TIPO')=="ENTRADA":
            saldos[chave]={'ID':idp,'DESCRICAO':str(m.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':0,'PAL':0,'QTD_PAL':0,'ULT_ATUAL':m.get('DATA_HORA', m.get('DATA',''))}
        if chave not in saldos: continue
        if m.get('TIPO')=="ENTRADA":
            saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0))
            saldos[chave]['PAL']+=safe_float(m.get('PALETES',0))
            saldos[chave]['ULT_ATUAL']=m.get('DATA_HORA', m.get('DATA',''))
        else:
            saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0))
            saldos[chave]['PAL']-=safe_float(m.get('PALETES',0))
            saldos[chave]['ULT_ATUAL']=m.get('DATA_HORA', m.get('DATA',''))
    return saldos

def get_saldo_sala_com_quarentena():
    agora = datetime.now(fuso).replace(tzinfo=None)
    saldos = get_saldos()
    saldo_sala_total = {}
    saldo_sala_pendente = {}
    saldo_sala_disponivel = {}
    for k,v in saldos.items():
        if v['LOCAL']==LOCAL_SALA and v['SALDO']>0:
            saldo_sala_total[k]=v.copy()
            saldo_sala_disponivel[k]=v.copy()
    for m in st.session_state.mov:
        if str(m.get('LOCAL_MOV','')).upper()!=LOCAL_SALA.upper(): continue
        if m.get('TIPO')!="ENTRADA": continue
        idp=str(m.get('ID','')).upper().strip()
        lote=str(m.get('LOTE','')).upper().strip()
        marca=str(m.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{LOCAL_SALA}__{marca}__{lote}"
        data_mov = parse_data_hora(m.get('DATA_HORA', m.get('DATA','')))
        diff_horas = (agora - data_mov).total_seconds()/3600
        if diff_horas < TEMPO_QUARENTENA_HORAS:
            q = safe_float(m.get('TOTAL_QTD',0))
            pal = safe_float(m.get('PALETES',0))
            if chave not in saldo_sala_pendente:
                saldo_sala_pendente[chave]={'ID':idp,'LOTE':lote,'MARCA':marca,'DESCRICAO':str(m.get('DESCRICAO','')).upper(),'QTD_PENDENTE':q,'PAL_PENDENTE':pal,'DATA_ENTRADA':m.get('DATA_HORA', m.get('DATA','')),'HORAS_RESTANTES':TEMPO_QUARENTENA_HORAS-diff_horas,'DATA_LIBERACAO':data_mov+timedelta(hours=TEMPO_QUARENTENA_HORAS),'ULT_ATUAL':m.get('DATA_HORA','')}
            else:
                saldo_sala_pendente[chave]['QTD_PENDENTE']+=q
                saldo_sala_pendente[chave]['PAL_PENDENTE']+=pal
            if chave in saldo_sala_disponivel:
                saldo_sala_disponivel[chave]['SALDO']-=q
                saldo_sala_disponivel[chave]['PAL']-=pal
                if saldo_sala_disponivel[chave]['SALDO']<0: saldo_sala_disponivel[chave]['SALDO']=0
                if saldo_sala_disponivel[chave]['PAL']<0: saldo_sala_disponivel[chave]['PAL']=0
    saldo_sala_disponivel = {k:v for k,v in saldo_sala_disponivel.items() if v['SALDO']>0}
    return saldo_sala_total, saldo_sala_pendente, saldo_sala_disponivel

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')}")
tabs = st.tabs(["ADMIN","DASHBOARD","CADASTRO AUTO","MOVIMENTACAO AUTO","ESTOQUE","BUSCA ID","GRD SALA ANEXA AUTO","GRAFICOS","HISTORICO FILTRO"])
tab_admin, tab_dash, tab_cad, tab_mov, tab_est, tab_busca, tab_grd, tab_graf, tab_hist = tabs

with tab_admin:
    st.header("1 - ADMINISTRACAO")
    if not is_admin: st.warning("Apenas admin")
    else:
        with st.form("form_user_admin"):
            email_new=st.text_input("Email novo")
            nome_new=st.text_input("Nome")
            senha_new=st.text_input("Senha")
            local_new=st.selectbox("Local acesso", LOCAIS_ACESSO)
            status_new=st.selectbox("Status", ["LIBERADO","BLOQUEADO"])
            if st.form_submit_button("SALVAR", type="primary"):
                if email_new and senha_new:
                    df=pd.read_csv(ARQ_EMAILS)
                    df=df[df['EMAIL'].astype(str).str.lower()!=email_new.lower()]
                    novo=pd.DataFrame([{"EMAIL":email_new.lower(),"SENHA":senha_new,"LOCAL":local_new,"STATUS":status_new,"NOME":nome_new.upper()}])
                    df=pd.concat([df,novo], ignore_index=True)
                    df.to_csv(ARQ_EMAILS,index=False)
                    st.success("Salvo"); st.rerun()
        st.dataframe(pd.read_csv(ARQ_EMAILS), use_container_width=True)

with tab_dash:
    st.header("2 - DASHBOARD")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista) if lista else pd.DataFrame()
    if not df.empty:
        df_g=df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        fig=px.bar(df_g, x='LOCAL', y='SALDO', color='LOCAL')
        st.plotly_chart(fig, use_container_width=True, key="dash_local")

with tab_cad:
    st.header("3 - CADASTRO 100% AUTOMATICO - SO DIGITAR ID")
    id_in = st.text_input("DIGITE ID* - SE JA EXISTE PREENCHE TUDO AUTOMATICO", key="id_cad_auto")
    desc_auto = ""; marca_auto = ""; qtd_auto = 1250.0; lote_auto = ""; encontrou=False
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_in.upper().strip():
                desc_auto=r.get('DESCRICAO',''); marca_auto=r.get('MARCA',''); qtd_auto=safe_float(r.get('QTD_PALETE',1250.0),1250.0); lote_auto=r.get('LOTE',''); encontrou=True; break
    if encontrou:
        st.success(f"✅ ID {id_in.upper()} JA CADASTRADO - AUTO {desc_auto} | {marca_auto} | {qtd_auto}")
        with st.form("form_cadastro_auto"):
            st.text_input("ID AUTOMATICO", value=id_in.upper(), disabled=True)
            st.text_input("DESCRICAO AUTOMATICA", value=desc_auto, disabled=True)
            st.text_input("MARCA AUTOMATICA", value=marca_auto, disabled=True)
            st.text_input("QTD/PAL AUTOMATICA", value=str(qtd_auto), disabled=True)
            lote_novo = st.text_input(f"LOTE BASE {lote_auto} - vazio usa mesmo ou novo", key="lote_novo_auto")
            locais_sel=st.multiselect("LOCAIS* (VARIOS)", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad_auto")
            ent_in=st.number_input("PALETES POR LOCAL*", value=1.0, min_value=0.1, key="ent_cad_auto")
            if st.form_submit_button("✅ CADASTRAR AUTOMATICO", type="primary", use_container_width=True):
                lote_final = lote_novo.upper() if lote_novo else lote_auto
                if lote_final and locais_sel:
                    for local_cad in locais_sel:
                        total=qtd_auto*ent_in
                        st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_auto.upper(),"MARCA":marca_auto.upper(),"LOTE":lote_final.upper(),"QTD_PALETE":qtd_auto,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                    st.success("OK"); st.rerun()
    else:
        if id_in: st.warning(f"🆕 ID {id_in.upper()} NOVO - Cadastre primeira vez")
        with st.form("form_cadastro_novo"):
            st.text_input("ID", value=id_in.upper() if id_in else "", disabled=True)
            desc_in=st.text_input("DESCRICAO* PARA NOVO", key="desc_cad_novo")
            marca_in=st.text_input("MARCA* PARA NOVO", key="marca_cad_novo")
            lote_in=st.text_input("LOTE* OBRIGATORIO", key="lote_cad_novo")
            locais_sel=st.multiselect("LOCAIS* (VARIOS)", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad_novo")
            qtd_in=st.number_input("QTD/PAL*", value=1250.0, key="qtd_cad_novo")
            ent_in=st.number_input("PALETES", value=0.0, key="ent_cad_novo2")
            if st.form_submit_button("CADASTRAR NOVO", type="primary"):
                if id_in and desc_in and marca_in and lote_in and locais_sel:
                    for local_cad in locais_sel:
                        total=qtd_in*ent_in
                        st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                    st.success("OK"); st.rerun()

with tab_mov:
    st.header("4 - MOVIMENTACAO 100% AUTOMATICA - SO DIGITAR ID")
    id_mov_in = st.text_input("DIGITE ID* - AUTO PREENCHE DESCRICAO/MARCA/QTD/LOTES", key="id_mov_auto_input", placeholder="Ex: 15, 16, 101")

    desc_mov_auto=""; marca_mov_auto=""; qtd_mov_auto=1250.0; encontrou_mov=False
    lotes_existentes=[]; marcas_existentes=[]; locs_existentes=[]

    if id_mov_in:
        id_mov_up = id_mov_in.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_mov_up:
                desc_mov_auto=r.get('DESCRICAO','')
                marca_mov_auto=r.get('MARCA','')
                qtd_mov_auto=safe_float(r.get('QTD_PALETE',1250.0),1250.0)
                encontrou_mov=True
                if r.get('LOTE','') not in lotes_existentes: lotes_existentes.append(r.get('LOTE',''))
                if r.get('MARCA','') not in marcas_existentes: marcas_existentes.append(r.get('MARCA',''))
                if r.get('LOCAL','') not in locs_existentes: locs_existentes.append(r.get('LOCAL',''))

        # Pega tambem lotes da movimentacao
        saldos = get_saldos()
        lotes_saldo = [v['LOTE'] for v in saldos.values() if v['ID']==id_mov_up and v['SALDO']>0]
        for l in lotes_saldo:
            if l not in lotes_existentes: lotes_existentes.append(l)

    if not id_mov_in:
        st.info("👆 DIGITE O ID ACIMA PARA MOVIMENTACAO AUTOMATICA")
    elif not encontrou_mov:
        st.error(f"❌ ID {id_mov_in.upper()} NAO CADASTRADO - Va na aba CADASTRO AUTO primeiro")
    else:
        st.success(f"✅ ID {id_mov_in.upper()} ENCONTRADO - AUTOMATICO: {desc_mov_auto} | {marca_mov_auto} | {qtd_mov_auto} UN/PAL")
        if lotes_existentes:
            st.info(f"📦 LOTES EXISTENTES PARA ID {id_mov_in.upper()}: {', '.join(lotes_existentes)} | MARCAS: {', '.join(marcas_existentes)}")

        # MOSTRA SALDO ATUAL AUTOMATICO POR LOCAL
        saldos = get_saldos()
        saldo_id = [v for v in saldos.values() if v['ID']==id_mov_in.upper() and v['SALDO']>0]
        if saldo_id:
            df_saldo_auto = pd.DataFrame(saldo_id)
            c1,c2,c3,c4=st.columns(4)
            with c1: st.metric("SALDO TOTAL AUTO", f"{df_saldo_auto['SALDO'].sum():,.0f} UN")
            with c2: st.metric("GALPAO AUTO", f"{df_saldo_auto[df_saldo_auto['LOCAL']==LOCAL_GALPAO]['SALDO'].sum():,.0f}")
            with c3: st.metric("SALA AUTO", f"{df_saldo_auto[df_saldo_auto['LOCAL']==LOCAL_SALA]['SALDO'].sum():,.0f}")
            with c4: st.metric("OFICINA AUTO", f"{df_saldo_auto[df_saldo_auto['LOCAL']==LOCAL_OFICINA]['SALDO'].sum():,.0f}")
            st.dataframe(df_saldo_auto[['ID','DESCRICAO','LOTE','MARCA','LOCAL','SALDO','PAL','ULT_ATUAL']].sort_values(by='LOCAL'), use_container_width=True)

        with st.form("form_mov_auto"):
            st.text_input("ID AUTOMATICO", value=id_mov_in.upper(), disabled=True)
            st.text_input("DESCRICAO AUTOMATICA", value=desc_mov_auto, disabled=True)
            st.text_input("MARCA AUTOMATICA BASE", value=marca_mov_auto, disabled=True)
            st.text_input("QTD/PAL AUTOMATICA", value=str(qtd_mov_auto), disabled=True)

            # LOTE AUTOMATICO - mostra existentes e deixa escolher ou digitar novo
            if lotes_existentes:
                lote_sel = st.selectbox(f"LOTE AUTOMATICO - EXISTENTES PARA ID {id_mov_in.upper()} + OPCAO NOVO LOTE", options=lotes_existentes+["DIGITAR NOVO LOTE"], key="lote_mov_auto_sel")
                if lote_sel=="DIGITAR NOVO LOTE":
                    lote_final = st.text_input("DIGITE NOVO LOTE* OBRIGATORIO", key="lote_mov_auto_novo")
                else:
                    lote_final = lote_sel
                    st.text_input("LOTE SELECIONADO AUTOMATICO", value=lote_final, disabled=True)
            else:
                lote_final = st.text_input("LOTE* OBRIGATORIO - ID SEM LOTE AINDA", key="lote_mov_auto_sem")

            marca_final = st.text_input("MARCA EDITAVEL AUTOMATICA (ja vem preenchida, pode mudar)", value=marca_mov_auto, key="marca_mov_auto_final")
            local_sel = st.selectbox("LOCAL* PARA MOVIMENTACAO", options=LOCAIS, index=0, key="local_mov_auto")
            tipo_sel = st.selectbox("TIPO* - ENTRADA/SAIDA", options=["ENTRADA","SAIDA"], key="tipo_mov_auto")
            pal_sel = st.number_input("PALETES* - QTD AUTOMATICA", value=1.0, min_value=0.1, key="pal_mov_auto")

            # PREVIA AUTOMATICA
            if lote_final:
                tot_prev = pal_sel * qtd_mov_auto
                if local_sel==LOCAL_GALPAO and tipo_sel=="ENTRADA":
                    st.success(f"✅ PREVIA AUTO: ENTRADA GALPAO +{tot_prev:,.0f} UN ({pal_sel} PAL x {qtd_mov_auto} UN)")
                elif local_sel==LOCAL_GALPAO and tipo_sel=="SAIDA":
                    st.warning(f"⚠️ PREVIA AUTO: SAIDA GALPAO -{tot_prev:,.0f} + ENTRADA OFICINA +{tot_prev:,.0f}")
                elif local_sel==LOCAL_SALA and tipo_sel=="ENTRADA":
                    st.info(f"ℹ️ PREVIA AUTO: SAIDA GALPAO -{tot_prev:,.0f} + ENTRADA SALA ANEXA +{tot_prev:,.0f} (fica {TEMPO_QUARENTENA_HORAS}H bloqueado para GRD)")
                elif local_sel==LOCAL_SALA and tipo_sel=="SAIDA":
                    st.warning(f"⚠️ PREVIA AUTO: SAIDA SALA ANEXA -{tot_prev:,.0f} + ENTRADA OFICINA +{tot_prev:,.0f}")
                elif local_sel==LOCAL_OFICINA and tipo_sel=="ENTRADA":
                    st.success(f"✅ PREVIA AUTO: ENTRADA OFICINA +{tot_prev:,.0f}")
                else:
                    st.error(f"🔴 PREVIA AUTO: SAIDA OFICINA -{tot_prev:,.0f} - CONSUMO FINAL")

            if st.form_submit_button(f"✅ CONFIRMAR MOVIMENTACAO AUTOMATICA ID {id_mov_in.upper()} COM DATA/HORA", type="primary", use_container_width=True):
                if not lote_final:
                    st.error("LOTE obrigatorio")
                else:
                    agora_str = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    tot=pal_sel*qtd_mov_auto
                    if local_sel==LOCAL_GALPAO and tipo_sel=="ENTRADA":
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"ENTRADA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    elif local_sel==LOCAL_GALPAO and tipo_sel=="SAIDA":
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"SAIDA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"ENTRADA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    elif local_sel==LOCAL_SALA and tipo_sel=="ENTRADA":
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"SAIDA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"ENTRADA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    elif local_sel==LOCAL_SALA and tipo_sel=="SAIDA":
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"SAIDA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"ENTRADA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    elif local_sel==LOCAL_OFICINA and tipo_sel=="ENTRADA":
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"ENTRADA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    else:
                        st.session_state.mov.append({"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"TIPO":"SAIDA","PALETES":pal_sel,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})

                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                    st.success(f"✅ MOVIMENTACAO AUTOMATICA ID {id_mov_in.upper()} CONFIRMADA {agora_str} - {tipo_sel} {tot:,.0f} UN em {local_sel}"); st.rerun()

    st.divider()
    st.write("ULTIMAS MOVIMENTACOES AUTOMATICAS")
    if st.session_state.mov:
        st.dataframe(pd.DataFrame(st.session_state.mov).tail(20).sort_values(by='DATA_HORA', ascending=False), use_container_width=True)

with tab_est:
    st.header("5 - ESTOQUE - IDS INDIVIDUAIS + DATA/HORA")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        st.dataframe(df.sort_values(by='ID'), use_container_width=True)

with tab_busca:
    st.header("6 - BUSCA ID - AUTOMATICA ENTRADA/SAIDA + DIA/SEMANA/MES/ANO")
    id_b = st.text_input("DIGITE ID BUSCA AUTOMATICA", key="id_busca_full_auto")
    if id_b:
        id_b_upper=id_b.upper().strip()
        saldos=get_saldos()
        lista_saldo=[v for v in saldos.values() if v['ID']==id_b_upper and v['SALDO']>0]
        if lista_saldo:
            st.dataframe(pd.DataFrame(lista_saldo), use_container_width=True)
        mov_filtrado=[m for m in st.session_state.mov if str(m.get('ID','')).upper()==id_b_upper]
        if mov_filtrado:
            df_mov=pd.DataFrame(mov_filtrado)
            df_mov['DATA_DT']=df_mov['DATA'].apply(lambda x: parse_data_hora(x))
            df_mov['DIA']=df_mov['DATA_DT'].dt.strftime("%d/%m/%Y")
            df_mov['SEMANA']=df_mov['DATA_DT'].dt.strftime("%Y-W%W")
            df_mov['MES']=df_mov['DATA_DT'].dt.strftime("%m/%Y")
            df_mov['ANO']=df_mov['DATA_DT'].dt.strftime("%Y")
            df_mov['QTD']=df_mov['TOTAL_QTD'].apply(lambda x: safe_float(x))
            c1,c2=st.columns(2)
            with c1: tipo_periodo=st.selectbox("AGRUPAR POR", ["DIA","SEMANA","MES","ANO"], key=f"periodo_busca_auto_{id_b_upper}")
            with c2: tipo_filtro=st.selectbox("TIPO", ["TODOS","ENTRADA","SAIDA"], key=f"tipo_busca_auto_{id_b_upper}")
            df_f=df_mov.copy()
            if tipo_filtro!="TODOS": df_f=df_f[df_f['TIPO']==tipo_filtro]
            col_agrup = {'DIA':'DIA','SEMANA':'SEMANA','MES':'MES','ANO':'ANO'}[tipo_periodo]
            df_g=df_f.groupby([col_agrup,'TIPO'], as_index=False)['QTD'].sum()
            if not df_g.empty:
                fig=px.bar(df_g, x=col_agrup, y='QTD', color='TIPO', barmode='group')
                st.plotly_chart(fig, use_container_width=True, key=f"busca_auto_{id_b_upper}_{tipo_periodo}_{tipo_filtro}")

with tab_grd:
    st.header(f"7 - GRD SALA ANEXA AUTO - IDS INDIVIDUAIS - REGRA {TEMPO_QUARENTENA_HORAS}H")
    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    df_disp = pd.DataFrame(list(disp_sala.values())) if disp_sala else pd.DataFrame()
    if not df_disp.empty:
        st.dataframe(df_disp.sort_values(by='ID'), use_container_width=True)
    ids_disponiveis_sala = sorted(list(set([v['ID'] for v in disp_sala.values()]))) if disp_sala else []
    if ids_disponiveis_sala:
        tipo_grd = st.radio("Tipo GRD AUTO", ["INDIVIDUAL AUTO", "CONJUNTO MESMO NUMERO AUTO (ID 15+16)"], key="tipo_grd_auto")
        if tipo_grd=="INDIVIDUAL AUTO":
            id_g=st.selectbox("ID AUTO", options=ids_disponiveis_sala, key="id_grd_ind_auto")
            saldo_id=[v for v in disp_sala.values() if v['ID']==id_g]
            lote_sel=st.selectbox("LOTE AUTO", options=sorted(list(set([v['LOTE'] for v in saldo_id]))), key="lote_grd_ind_auto")
            saldo_lote=[v for v in saldo_id if v['LOTE']==lote_sel][0]
            qtd=st.number_input(f"PALETES AUTO MAX {saldo_lote['PAL']:.1f}", value=1.0, key="qtd_grd_ind_auto")
            os_g=st.text_input("OS* AUTO", key="os_grd_ind_auto")
            if st.button("GERAR GRD AUTO INDIVIDUAL", type="primary", key="btn_grd_ind_auto"):
                num=f"GRD-SALA-{agora.strftime('%Y%m%d%H%M%S')}"
                tot=qtd*saldo_lote['QTD_PAL'] if saldo_lote['QTD_PAL']>0 else qtd*1250
                st.session_state.grd.append({"NUM_GRD":num,"ID":id_g,"DESCRICAO":saldo_lote['DESCRICAO'],"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"QTD_PALETES":qtd,"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"SAIDA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"ENTRADA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success(f"GRD {num}"); st.rerun()
        else:
            ids_multi=st.multiselect("IDS MESMO GRD AUTO", options=ids_disponiveis_sala, default=ids_disponiveis_sala[:2] if len(ids_disponiveis_sala)>=2 else ids_disponiveis_sala, key="ids_conj_auto")
            if ids_multi:
                qtds={}
                for id_sel in ids_multi:
                    saldo_id=[v for v in disp_sala.values() if v['ID']==id_sel]
                    lote_id=st.selectbox(f"LOTE AUTO ID {id_sel}", options=sorted(list(set([v['LOTE'] for v in saldo_id]))), key=f"lote_conj_auto_{id_sel}")
                    saldo_lote=[v for v in saldo_id if v['LOTE']==lote_id][0]
                    qtd=st.number_input(f"PAL AUTO ID {id_sel} MAX {saldo_lote['PAL']:.1f}", value=1.0, key=f"qtd_conj_auto_{id_sel}")
                    qtds[id_sel]={'lote':lote_id,'saldo_lote':saldo_lote,'qtd':qtd}
                os_g=st.text_input("OS* AUTO", key="os_conj_auto")
                if st.button("GERAR GRD AUTO CONJUNTO MESMO NUMERO", type="primary", key="btn_conj_auto"):
                    num=f"GRD-CONJ-{agora.strftime('%Y%m%d%H%M%S')}"
                    for id_sel in ids_multi:
                        info=qtds[id_sel]
                        tot=info['qtd']*info['saldo_lote']['QTD_PAL'] if info['saldo_lote']['QTD_PAL']>0 else info['qtd']*1250
                        st.session_state.grd.append({"NUM_GRD":num,"ID":id_sel,"DESCRICAO":info['saldo_lote']['DESCRICAO'],"LOTE":info['lote'],"MARCA":info['saldo_lote']['MARCA'],"QTD_PALETES":info['qtd'],"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S"),"TIPO_GRD":"CONJUNTO"})
                        st.session_state.mov.append({"ID":id_sel,"LOTE":info['lote'],"MARCA":info['saldo_lote']['MARCA'],"DESCRICAO":info['saldo_lote']['DESCRICAO'],"TIPO":"SAIDA","PALETES":info['qtd'],"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                        st.session_state.mov.append({"ID":id_sel,"LOTE":info['lote'],"MARCA":info['saldo_lote']['MARCA'],"DESCRICAO":info['saldo_lote']['DESCRICAO'],"TIPO":"ENTRADA","PALETES":info['qtd'],"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                    st.success(f"GRD CONJUNTO {num}"); st.rerun()
    if st.session_state.grd:
        st.dataframe(pd.DataFrame(st.session_state.grd).sort_values(by='DATA_HORA', ascending=False), use_container_width=True)

with tab_graf:
    st.header("8 - GRAFICOS AUTO")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        fig=px.bar(df.groupby('LOCAL', as_index=False)['SALDO'].sum(), x='LOCAL', y='SALDO', color='LOCAL')
        st.plotly_chart(fig, use_container_width=True, key="graf_auto")

with tab_hist:
    st.header("9 - HISTORICO COM FILTRO ID INDIVIDUAL/TODOS + ENTRADA/SAIDA + DIA/SEMANA/MES/ANO")
    if not st.session_state.mov:
        st.warning("Sem movimentacoes")
    else:
        df_mov_all = pd.DataFrame(st.session_state.mov)
        df_mov_all['DATA_DT'] = df_mov_all['DATA'].apply(lambda x: parse_data_hora(x))
        df_mov_all['DIA'] = df_mov_all['DATA_DT'].dt.strftime("%d/%m/%Y")
        df_mov_all['SEMANA'] = df_mov_all['DATA_DT'].dt.strftime("%Y-W%W")
        df_mov_all['MES'] = df_mov_all['DATA_DT'].dt.strftime("%m/%Y")
        df_mov_all['ANO'] = df_mov_all['DATA_DT'].dt.strftime("%Y")
        df_mov_all['QTD'] = df_mov_all['TOTAL_QTD'].apply(lambda x: safe_float(x))
        df_mov_all['PAL'] = df_mov_all['PALETES'].apply(lambda x: safe_float(x))
        ids_raw_hist = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
        ids_hist = sorted(list(set(ids_raw_hist)))
        ids_hist_com_todos = ["TODOS"] + ids_hist
        c1,c2,c3,c4 = st.columns(4)
        with c1: id_filtro = st.selectbox("ID - INDIVIDUAL OU TODOS", options=ids_hist_com_todos, key="filtro_id_hist_auto")
        with c2: tipo_filtro_hist = st.selectbox("TIPO - ENTRADA/SAIDA/TODOS", options=["TODOS","ENTRADA","SAIDA"], key="filtro_tipo_hist_auto")
        with c3: periodo_hist = st.selectbox("PERIODO", options=["DIA","SEMANA","MES","ANO"], key="filtro_periodo_hist_auto")
        with c4: local_filtro = st.selectbox("LOCAL", options=["TODOS"]+LOCAIS, key="filtro_local_hist_auto")
        df_filtrado = df_mov_all.copy()
        if id_filtro!= "TODOS": df_filtrado = df_filtrado[df_filtrado['ID'].astype(str).str.upper()==id_filtro]
        if tipo_filtro_hist!= "TODOS": df_filtrado = df_filtrado[df_filtrado['TIPO']==tipo_filtro_hist]
        if local_filtro!= "TODOS": df_filtrado = df_filtrado[df_filtrado['LOCAL_MOV']==local_filtro]
        if df_filtrado.empty:
            st.warning("Sem dados")
        else:
            df_ent = df_filtrado[df_filtrado['TIPO']=="ENTRADA"]
            df_sai = df_filtrado[df_filtrado['TIPO']=="SAIDA"]
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric(f"ENTRADAS ({id_filtro})", f"{df_ent['QTD'].sum():,.0f}")
            with c2: st.metric(f"SAIDAS ({id_filtro})", f"{df_sai['QTD'].sum():,.0f}")
            with c3: st.metric(f"SALDO ({id_filtro})", f"{df_ent['QTD'].sum()-df_sai['QTD'].sum():,.0f}")
            with c4: st.metric(f"QTD MOV", f"{len(df_filtrado)}")
            col_agrup = {'DIA':'DIA','SEMANA':'SEMANA','MES':'MES','ANO':'ANO'}[periodo_hist]
            df_g_geral = df_filtrado.groupby([col_agrup,'TIPO'], as_index=False)['QTD'].sum()
            df_g_geral['TEXTO']=df_g_geral['QTD'].apply(lambda x: f"{x:,.0f}")
            if not df_g_geral.empty:
                fig_geral = px.bar(df_g_geral, x=col_agrup, y='QTD', color='TIPO', barmode='group', text='TEXTO')
                st.plotly_chart(fig_geral, use_container_width=True, key=f"hist_auto_geral_{id_filtro}_{tipo_filtro_hist}_{periodo_hist}_{local_filtro}")
            col1,col2 = st.columns(2)
            with col1:
                st.subheader(f"🟢 ENTRADAS - ID {id_filtro} - {periodo_hist}")
                df_ent_g = df_ent.groupby(col_agrup, as_index=False)['QTD'].sum()
                if not df_ent_g.empty:
                    fig_ent = px.bar(df_ent_g, x=col_agrup, y='QTD', text='QTD')
                    st.plotly_chart(fig_ent, use_container_width=True, key=f"hist_auto_ent_{id_filtro}_{periodo_hist}_{local_filtro}")
                st.dataframe(df_ent_g, use_container_width=True)
            with col2:
                st.subheader(f"🔴 SAIDAS - ID {id_filtro} - {periodo_hist}")
                df_sai_g = df_sai.groupby(col_agrup, as_index=False)['QTD'].sum()
                if not df_sai_g.empty:
                    fig_sai = px.bar(df_sai_g, x=col_agrup, y='QTD', text='QTD')
                    st.plotly_chart(fig_sai, use_container_width=True, key=f"hist_auto_sai_{id_filtro}_{periodo_hist}_{local_filtro}")
                st.dataframe(df_sai_g, use_container_width=True)

st.caption(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')} - TODAS ABAS 100% AUTOMATICAS")
