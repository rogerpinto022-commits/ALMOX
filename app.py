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
tabs = st.tabs(["ADMIN","DASHBOARD","CADASTRO","MOVIMENTACAO","ESTOQUE","BUSCA ID","GRD SALA ANEXA 48H IDS INDIVIDUAIS","GRAFICOS","HISTORICO"])
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
    st.header("2 - DASHBOARD SALA ANEXA INDIVIDUAL POR ID + DATA/HORA ATUALIZACAO")
    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    df_total = pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    df_disp = pd.DataFrame(list(disp_sala.values())) if disp_sala else pd.DataFrame()
    if not df_total.empty:
        st.subheader("📦 ESTOQUE SALA ANEXA - INDIVIDUAL POR ID - COM DATA/HORA ULTIMA ATUALIZACAO")
        # Mostra individual por ID
        df_ind = df_total.copy()
        df_ind['DATA_HORA_ATUALIZACAO'] = df_ind['ULT_ATUAL']
        df_ind['HORA_ATUAL'] = agora.strftime("%d/%m/%Y %H:%M:%S")
        st.dataframe(df_ind[['ID','DESCRICAO','LOTE','MARCA','SALDO','PAL','QTD_PAL','LOCAL','DATA_HORA_ATUALIZACAO']].sort_values(by='ID'), use_container_width=True)
        # Agrupa por ID individual
        df_por_id = df_total.groupby(['ID','DESCRICAO'], as_index=False)['SALDO'].sum()
        df_por_id['TEXTO']=df_por_id['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_por_id, x='ID', y='SALDO', text='TEXTO', color='ID', title="SALA ANEXA - ESTOQUE INDIVIDUAL POR ID - NUMEROS GRANDES")
        fig.update_traces(textposition='inside', textfont=dict(size=20, color='white', family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Sem estoque SALA ANEXA")

with tab_cad:
    st.header("3 - CADASTRO AUTOMATICO")
    id_in = st.text_input("ID* AUTO", key="id_cad_auto")
    desc_auto=""; marca_auto=""; qtd_auto=1250.0; lote_auto=""; encontrou=False
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_in.upper().strip():
                desc_auto=r.get('DESCRICAO',''); marca_auto=r.get('MARCA',''); qtd_auto=safe_float(r.get('QTD_PALETE',1250.0),1250.0); lote_auto=r.get('LOTE',''); encontrou=True; break
    if encontrou:
        st.success(f"✅ ID {id_in.upper()} JA CADASTRADO {desc_auto} | {marca_auto}")
        with st.form("form_cadastro_auto"):
            st.text_input("ID", value=id_in.upper(), disabled=True)
            st.text_input("DESCRICAO", value=desc_auto, disabled=True)
            st.text_input("MARCA", value=marca_auto, disabled=True)
            lote_novo = st.text_input(f"LOTE BASE {lote_auto}", key="lote_novo_auto")
            locais_sel=st.multiselect("LOCAIS*", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad_auto")
            ent_in=st.number_input("PALETES*", value=1.0, min_value=0.1, key="ent_cad_auto")
            if st.form_submit_button("CADASTRAR AUTO", type="primary"):
                lote_final = lote_novo.upper() if lote_novo else lote_auto
                if lote_final and locais_sel:
                    for local_cad in locais_sel:
                        total=qtd_auto*ent_in
                        st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_auto.upper(),"MARCA":marca_auto.upper(),"LOTE":lote_final.upper(),"QTD_PALETE":qtd_auto,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                    st.success("OK"); st.rerun()
    else:
        with st.form("form_cadastro_novo"):
            st.text_input("ID", value=id_in.upper() if id_in else "", disabled=True)
            desc_in=st.text_input("DESCRICAO*", key="desc_cad_novo")
            marca_in=st.text_input("MARCA*", key="marca_cad_novo")
            lote_in=st.text_input("LOTE*", key="lote_cad_novo")
            locais_sel=st.multiselect("LOCAIS*", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad_novo")
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
    st.header("4 - MOVIMENTACAO")
    ids_raw = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
    ids = sorted(list(set(ids_raw)))
    if ids:
        id_sel=st.selectbox("ID* AUTO", options=ids, key="id_mov")
        cat=None
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==id_sel: cat=r; break
        desc=cat.get('DESCRICAO','') if cat else ""
        marca_cat=cat.get('MARCA','') if cat else ""
        qtd_cat=safe_float(cat.get('QTD_PALETE',1250)) if cat else 1250
        st.text_input("Descricao Auto", value=desc, disabled=True, key="desc_mov")
        lote=st.text_input("LOTE*", key="lote_mov")
        marca=st.text_input("MARCA AUTO", value=marca_cat, key="marca_mov")
        local_sel=st.selectbox("LOCAL*", LOCAIS, key="local_mov")
        tipo=st.selectbox("TIPO*", ["ENTRADA","SAIDA"], key="tipo_mov")
        pal=st.number_input("PALETES*", value=1.0, min_value=0.1, key="pal_mov")
        if st.button("CONFIRMAR COM DATA/HORA", type="primary", key="btn_mov"):
            if lote:
                agora_str = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                tot=pal*qtd_cat
                if local_sel==LOCAL_GALPAO and tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                elif local_sel==LOCAL_GALPAO and tipo=="SAIDA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                elif local_sel==LOCAL_SALA and tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                elif local_sel==LOCAL_SALA and tipo=="SAIDA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                elif local_sel==LOCAL_OFICINA and tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                else:
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success(f"OK {agora_str}"); st.rerun()

with tab_est:
    st.header("5 - ESTOQUE SALA ANEXA - IDS INDIVIDUAIS + DATA/HORA ATUALIZACAO")
    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    saldos=get_saldos()
    lista_sala=[v for v in saldos.values() if v['LOCAL']==LOCAL_SALA and v['SALDO']>0]
    if lista_sala:
        df=pd.DataFrame(lista_sala)
        df['DATA_HORA_ULT_ATUALIZACAO']=df['ULT_ATUAL']
        df['AGORA']=agora.strftime("%d/%m/%Y %H:%M:%S")
        st.dataframe(df[['ID','DESCRICAO','LOTE','MARCA','SALDO','PAL','LOCAL','DATA_HORA_ULT_ATUALIZACAO','AGORA']].sort_values(by=['ID','LOTE']), use_container_width=True)
        st.info("Cada ID (ex: 15 e 16) mostra separado mesmo sendo mesmo produto acabado")

with tab_busca:
    st.header("6 - BUSCA ID")
    id_b=st.text_input("ID BUSCA", key="id_busca")
    if id_b:
        saldos=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper() and v['SALDO']>0]
        if lista:
            df=pd.DataFrame(lista)
            df['DATA_HORA_ATUALIZACAO']=df['ULT_ATUAL']
            st.dataframe(df, use_container_width=True)

with tab_grd:
    st.header(f"7 - GRD SALA ANEXA - IDS INDIVIDUAIS - ID 15 E 16 SEPARADOS - MESMO NUMERO GRD - REGRA {TEMPO_QUARENTENA_HORAS}H + DATA/HORA ATUALIZACAO")
    st.info(f"REGRA: GRD so SALA ANEXA. IDs 15 e 16 sao produtos diferentes mas formam 1 produto acabado. No GRD pode mostrar mesmo numero GRD para ID 15 e ID 16, mas estoque SALA ANEXA mostra IDs separados. GRD considera so >{TEMPO_QUARENTENA_HORAS}H. Mostra DATA/HORA atualizacao.")

    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    df_total = pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    df_pend = pd.DataFrame(list(pendente_sala.values())) if pendente_sala else pd.DataFrame()
    df_disp = pd.DataFrame(list(disp_sala.values())) if disp_sala else pd.DataFrame()

    total_geral = df_total['SALDO'].sum() if not df_total.empty else 0
    total_pend = df_pend['QTD_PENDENTE'].sum() if not df_pend.empty else 0
    total_disp = df_disp['SALDO'].sum() if not df_disp.empty else 0

    c1,c2,c3=st.columns(3)
    with c1: st.metric("SALA TOTAL GERAL (todos IDs)", f"{total_geral:,.0f}")
    with c2: st.metric(f"BLOQUEADO <{TEMPO_QUARENTENA_HORAS}H", f"{total_pend:,.0f}")
    with c3: st.metric("DISPONIVEL >48H PARA GRD", f"{total_disp:,.0f}")

    # ESTOQUE SALA ANEXA INDIVIDUAL POR ID - COM DATA/HORA ATUALIZACAO
    st.subheader("📦 ESTOQUE SALA ANEXA - IDS INDIVIDUAIS SEPARADOS (ID 15 e 16 separados) + DATA/HORA ULTIMA ATUALIZACAO")
    if not df_total.empty:
        df_show = df_total.copy()
        df_show['DATA_HORA_ULTIMA_ATUALIZACAO']=df_show['ULT_ATUAL']
        df_show['DATA_HORA_AGORA']=agora.strftime("%d/%m/%Y %H:%M:%S")
        df_show['STATUS_48H']=df_show['ID'].apply(lambda x: "PENDENTE <48H tem parte bloqueada" if any(p['ID']==x for p in pendente_sala.values()) else "LIBERADO >48H")
        st.dataframe(df_show[['ID','DESCRICAO','LOTE','MARCA','SALDO','PAL','STATUS_48H','DATA_HORA_ULTIMA_ATUALIZACAO','DATA_HORA_AGORA','LOCAL']].sort_values(by='ID'), use_container_width=True)

        # Agrupa individual por ID para mostrar
        df_id_individual = df_total.groupby(['ID','DESCRICAO'], as_index=False).agg({'SALDO':'sum','PAL':'sum'}).sort_values(by='ID')
        df_id_individual['TEXTO']=df_id_individual['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_id_individual['DATA_HORA_ATUALIZACAO']=agora.strftime("%d/%m/%Y %H:%M:%S")
        st.write("### 📊 RESUMO INDIVIDUAL POR ID (ID 15 separado de ID 16) + DATA/HORA ATUALIZACAO")
        st.dataframe(df_id_individual, use_container_width=True)
        fig=px.bar(df_id_individual, x='ID', y='SALDO', text='TEXTO', color='ID', title="SALA ANEXA - IDS INDIVIDUAIS - 15 e 16 separados")
        fig.update_traces(textposition='inside', textfont=dict(size=18, color='white', family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)

    # PENDENTES INDIVIDUAIS
    if pendente_sala:
        st.subheader(f"⏳ PENDENTES <{TEMPO_QUARENTENA_HORAS}H - INDIVIDUAL POR ID - COM DATA/HORA")
        lista_pend=[]
        for k,v in pendente_sala.items():
            lista_pend.append({
                'ID':v['ID'],
                'DESCRICAO':v['DESCRICAO'],
                'LOTE':v['LOTE'],
                'MARCA':v['MARCA'],
                'QTD_PENDENTE':v['QTD_PENDENTE'],
                'DATA_ENTRADA':v['DATA_ENTRADA'],
                'DATA_LIBERACAO':v['DATA_LIBERACAO'].strftime("%d/%m/%Y %H:%M:%S"),
                'HORAS_RESTANTES':f"{v['HORAS_RESTANTES']:.1f}h",
                'DATA_HORA_ATUALIZACAO':agora.strftime("%d/%m/%Y %H:%M:%S")
            })
        st.dataframe(pd.DataFrame(lista_pend).sort_values(by='ID'), use_container_width=True)

    # DISPONIVEL PARA GRD INDIVIDUAL
    st.subheader(f"✅ DISPONIVEL PARA GRD >{TEMPO_QUARENTENA_HORAS}H - IDS INDIVIDUAIS - ID 15 E 16 SEPARADOS")
    if not df_disp.empty:
        df_disp_show = df_disp.copy()
        df_disp_show['DATA_HORA_ULTIMA_ATUALIZACAO']=df_disp_show['ULT_ATUAL']
        df_disp_show['DATA_HORA_AGORA']=agora.strftime("%d/%m/%Y %H:%M:%S")
        st.dataframe(df_disp_show[['ID','DESCRICAO','LOTE','MARCA','SALDO','PAL','DATA_HORA_ULTIMA_ATUALIZACAO','DATA_HORA_AGORA']].sort_values(by='ID'), use_container_width=True)
    else:
        st.warning("Nenhum disponivel >48H")

    # GERAR GRD COM MESMO NUMERO PARA IDS DIFERENTES
    st.divider()
    st.subheader("🚚 GERAR GRD - MESMO NUMERO GRD PARA IDS DIFERENTES (ID 15 + ID 16 = mesmo produto acabado)")

    ids_disponiveis_sala = sorted(list(set([v['ID'] for v in disp_sala.values()]))) if disp_sala else []

    if not ids_disponiveis_sala:
        st.error(f"Sem IDs liberados >{TEMPO_QUARENTENA_HORAS}H para GRD")
    else:
        st.success(f"IDs liberados na SALA ANEXA: {', '.join(ids_disponiveis_sala)} - Cada ID mostra separado, mas GRD pode usar mesmo numero")

        # Opcao 1: GRD individual por ID
        # Opcao 2: GRD conjunto mesmo numero para varios IDs
        tipo_grd = st.radio("Tipo GRD", ["GRD INDIVIDUAL 1 ID por vez", "GRD CONJUNTO mesmo numero para VARIOS IDs (ex: ID 15 + ID 16 juntos)"], key="tipo_grd")

        if tipo_grd == "GRD INDIVIDUAL 1 ID por vez":
            id_g=st.selectbox("ID PARA GRD INDIVIDUAL", options=ids_disponiveis_sala, key="id_grd_sala_ind")
            saldo_disp_id = [v for v in disp_sala.values() if v['ID']==id_g]
            total_disp_id = sum([v['SALDO'] for v in saldo_disp_id])
            st.info(f"ID {id_g} disponivel total: {total_disp_id:,.0f} UN")
            lotes_disp = sorted(list(set([v['LOTE'] for v in saldo_disp_id])))
            lote_sel = st.selectbox("LOTE", options=lotes_disp, key="lote_grd_ind")
            saldo_lote = [v for v in saldo_disp_id if v['LOTE']==lote_sel][0]
            qtd_pal_grd = st.number_input(f"PALETES MAX {saldo_lote['PAL']:.1f}", value=1.0, min_value=0.1, max_value=float(saldo_lote['PAL']+0.1), key="qtd_grd_ind")
            os_g=st.text_input("OS/FORNO*", key="os_grd_ind")
            if st.button("GERAR GRD INDIVIDUAL", type="primary", key="btn_grd_ind"):
                num=f"GRD-SALA-{agora.strftime('%Y%m%d%H%M%S')}"
                tot= qtd_pal_grd * saldo_lote['QTD_PAL'] if saldo_lote['QTD_PAL']>0 else qtd_pal_grd*1250
                st.session_state.grd.append({"NUM_GRD":num,"ID":id_g,"DESCRICAO":saldo_lote['DESCRICAO'],"LOTE":lote_sel.upper(),"MARCA":saldo_lote['MARCA'].upper(),"QTD_PALETES":qtd_pal_grd,"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S"),"TIPO_GRD":"INDIVIDUAL"})
                pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel.upper(),"MARCA":saldo_lote['MARCA'].upper(),"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"SAIDA","PALETES":qtd_pal_grd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel.upper(),"MARCA":saldo_lote['MARCA'].upper(),"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"ENTRADA","PALETES":qtd_pal_grd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success(f"GRD {num} ID {id_g} gerada {agora.strftime('%d/%m/%Y %H:%M:%S')}"); st.rerun()

        else: # CONJUNTO MESMO NUMERO PARA VARIOS IDS
            st.write("### GRD CONJUNTO - MESMO NUMERO PARA VARIOS IDS (ex: ID 15 = 100 UN + ID 16 = 100 UN, mesmo GRD, produto acabado)")
            ids_multi = st.multiselect("SELECIONE VARIOS IDS PARA MESMO GRD (ex: 15 e 16)", options=ids_disponiveis_sala, default=ids_disponiveis_sala[:2] if len(ids_disponiveis_sala)>=2 else ids_disponiveis_sala, key="ids_grd_conjunto")

            if ids_multi:
                # Mostra cada ID individual com seu saldo
                st.write("#### IDs selecionados - individual:")
                for id_sel in ids_multi:
                    saldo_id = [v for v in disp_sala.values() if v['ID']==id_sel]
                    total_id = sum([v['SALDO'] for v in saldo_id])
                    st.write(f"**ID {id_sel}: {total_id:,.0f} UN disponivel** - {saldo_id[0]['DESCRICAO'] if saldo_id else ''} - Ult atual: {saldo_id[0]['ULT_ATUAL'] if saldo_id else ''}")

                # Para cada ID, escolher lote e qtd
                qtds_por_id = {}
                lotes_por_id = {}
                for id_sel in ids_multi:
                    saldo_id = [v for v in disp_sala.values() if v['ID']==id_sel]
                    lotes_id = sorted(list(set([v['LOTE'] for v in saldo_id])))
                    lote_id = st.selectbox(f"LOTE para ID {id_sel}", options=lotes_id, key=f"lote_conj_{id_sel}")
                    lotes_por_id[id_sel]=lote_id
                    saldo_lote = [v for v in saldo_id if v['LOTE']==lote_id][0]
                    qtd = st.number_input(f"PALETES ID {id_sel} MAX {saldo_lote['PAL']:.1f} PAL ({saldo_lote['SALDO']:,.0f} UN)", value=1.0, min_value=0.1, max_value=float(saldo_lote['PAL']+0.1), key=f"qtd_conj_{id_sel}")
                    qtds_por_id[id_sel]={'qtd_pal':qtd, 'saldo_lote':saldo_lote}

                os_g=st.text_input("OS/FORNO DESTINO (mesmo para todos IDs)*", key="os_grd_conj")
                obs=st.text_input("OBS produto acabado (ex: KIT FORNO 15+16)", key="obs_grd_conj")

                if st.button(f"GERAR GRD CONJUNTO MESMO NUMERO PARA {len(ids_multi)} IDS - DATA/HORA {agora.strftime('%d/%m/%Y %H:%M:%S')}", type="primary", use_container_width=True, key="btn_grd_conj"):
                    num_conjunto = f"GRD-SALA-CONJ-{agora.strftime('%Y%m%d%H%M%S')}"
                    for id_sel in ids_multi:
                        info = qtds_por_id[id_sel]
                        saldo_lote = info['saldo_lote']
                        qtd_pal = info['qtd_pal']
                        tot = qtd_pal * saldo_lote['QTD_PAL'] if saldo_lote['QTD_PAL']>0 else qtd_pal*1250
                        st.session_state.grd.append({
                            "NUM_GRD":num_conjunto,
                            "ID":id_sel,
                            "DESCRICAO":saldo_lote['DESCRICAO'],
                            "LOTE":lotes_por_id[id_sel].upper(),
                            "MARCA":saldo_lote['MARCA'].upper(),
                            "QTD_PALETES":qtd_pal,
                            "TOTAL_QTD":tot,
                            "ORIGEM":LOCAL_SALA,
                            "DESTINO":LOCAL_OFICINA,
                            "OS":os_g,
                            "OBS":f"{obs} - CONJUNTO {len(ids_multi)} IDS MESMO GRD",
                            "DATA":agora.strftime("%d/%m/%Y"),
                            "DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),
                            "DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S"),
                            "TIPO_GRD":f"CONJUNTO MESMO NUMERO - {len(ids_multi)} IDS"
                        })
                        st.session_state.mov.append({"ID":id_sel,"LOTE":lotes_por_id[id_sel].upper(),"MARCA":saldo_lote['MARCA'].upper(),"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"SAIDA","PALETES":qtd_pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                        st.session_state.mov.append({"ID":id_sel,"LOTE":lotes_por_id[id_sel].upper(),"MARCA":saldo_lote['MARCA'].upper(),"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"ENTRADA","PALETES":qtd_pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})

                    pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                    st.success(f"✅ GRD CONJUNTO {num_conjunto} GERADA para {len(ids_multi)} IDS - Mesmo numero GRD - IDs: {', '.join(ids_multi)} - Data/Hora: {agora.strftime('%d/%m/%Y %H:%M:%S')}")
                    st.rerun()

    st.divider()
    if st.session_state.grd:
        st.subheader("📜 GRDs GERADAS - COM DATA/HORA ATUALIZACAO - IDS INDIVIDUAIS MAS MESMO NUMERO QUANDO CONJUNTO")
        df_grd = pd.DataFrame(st.session_state.grd)
        if 'DATA_HORA_ATUALIZACAO' not in df_grd.columns:
            df_grd['DATA_HORA_ATUALIZACAO']=df_grd.get('DATA_HORA', df_grd.get('DATA',''))
        st.dataframe(df_grd.sort_values(by='DATA_HORA', ascending=False), use_container_width=True)

        # Resumo por NUM_GRD - mostra que mesmo numero tem varios IDs
        if 'NUM_GRD' in df_grd.columns:
            st.write("### 📊 RESUMO POR NUMERO GRD - Mostra mesmo numero com varios IDs (ex: ID 15 e 16 mesmo GRD)")
            df_resumo = df_grd.groupby('NUM_GRD', as_index=False).agg({'ID': lambda x: ', '.join(sorted(set(x))), 'TOTAL_QTD':'sum', 'QTD_PALETES':'sum', 'DATA_HORA':'first', 'DATA_HORA_ATUALIZACAO':'first', 'TIPO_GRD':'first'})
            st.dataframe(df_resumo, use_container_width=True)

with tab_graf:
    st.header("8 - GRAFICOS")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if not df.empty:
        df_local=df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        fig=px.bar(df_local, x='LOCAL', y='SALDO', color='LOCAL')
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    st.header("9 - HISTORICO")
    if st.session_state.mov:
        df_mov=pd.DataFrame(st.session_state.mov)
        st.dataframe(df_mov.sort_values(by='DATA_HORA', ascending=False) if 'DATA_HORA' in df_mov.columns else df_mov, use_container_width=True)

st.caption(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')} - GRD SALA ANEXA IDS INDIVIDUAIS 15/16 MESMO NUMERO + DATA/HORA ATUALIZACAO + REGRA 48H")
