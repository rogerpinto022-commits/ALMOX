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
tabs = st.tabs(["ADMIN","DASHBOARD","CADASTRO","MOVIMENTACAO","ESTOQUE","BUSCA ID","GRD SALA ANEXA","GRAFICOS","HISTORICO COM FILTRO ID E ENTRADA/SAIDA"])
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
        st.plotly_chart(fig, use_container_width=True)

with tab_cad:
    st.header("3 - CADASTRO AUTOMATICO")
    id_in = st.text_input("ID* AUTO", key="id_cad_auto")
    desc_auto=""; marca_auto=""; qtd_auto=1250.0; lote_auto=""; encontrou=False
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_in.upper().strip():
                desc_auto=r.get('DESCRICAO',''); marca_auto=r.get('MARCA',''); qtd_auto=safe_float(r.get('QTD_PALETE',1250.0),1250.0); lote_auto=r.get('LOTE',''); encontrou=True; break
    if encontrou:
        st.success(f"✅ ID {id_in.upper()} JA CADASTRADO {desc_auto}")
        with st.form("form_cadastro_auto"):
            st.text_input("ID", value=id_in.upper(), disabled=True)
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
        if st.button("CONFIRMAR", type="primary", key="btn_mov"):
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
                st.success("OK"); st.rerun()

with tab_est:
    st.header("5 - ESTOQUE - IDS INDIVIDUAIS + DATA/HORA")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        st.dataframe(df.sort_values(by='ID'), use_container_width=True)

with tab_busca:
    st.header("6 - BUSCA ID - COM HISTORICO SEPARADO ENTRADA/SAIDA + DIA/SEMANA/MES/ANO")
    id_b = st.text_input("DIGITE ID PARA BUSCA COMPLETA", key="id_busca_full")
    if id_b:
        id_b_upper=id_b.upper().strip()
        saldos=get_saldos()
        lista_saldo=[v for v in saldos.values() if v['ID']==id_b_upper and v['SALDO']>0]
        if lista_saldo:
            df_saldo=pd.DataFrame(lista_saldo)
            st.dataframe(df_saldo, use_container_width=True)

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
            with c1: tipo_periodo=st.selectbox(f"AGRUPAR ID {id_b_upper} POR", ["DIA","SEMANA","MES","ANO"], key=f"periodo_busca_{id_b_upper}")
            with c2: tipo_filtro=st.selectbox(f"FILTRAR ID {id_b_upper} POR TIPO", ["TODOS","ENTRADA","SAIDA"], key=f"tipo_busca_{id_b_upper}")

            df_f=df_mov.copy()
            if tipo_filtro!="TODOS": df_f=df_f[df_f['TIPO']==tipo_filtro]

            col_agrup = {'DIA':'DIA','SEMANA':'SEMANA','MES':'MES','ANO':'ANO'}[tipo_periodo]

            df_ent=df_f[df_f['TIPO']=="ENTRADA"]
            df_sai=df_f[df_f['TIPO']=="SAIDA"]

            c1,c2,c3=st.columns(3)
            with c1: st.metric(f"ENTRADAS ID {id_b_upper}", f"{df_ent['QTD'].sum():,.0f}")
            with c2: st.metric(f"SAIDAS ID {id_b_upper}", f"{df_sai['QTD'].sum():,.0f}")
            with c3: st.metric(f"SALDO ID {id_b_upper}", f"{df_ent['QTD'].sum()-df_sai['QTD'].sum():,.0f}")

            # GRAFICO SEPARADO
            df_g=df_f.groupby([col_agrup,'TIPO'], as_index=False)['QTD'].sum()
            if not df_g.empty:
                fig=px.bar(df_g, x=col_agrup, y='QTD', color='TIPO', barmode='group', title=f"ID {id_b_upper} POR {tipo_periodo} - {tipo_filtro}")
                st.plotly_chart(fig, use_container_width=True)

            col1,col2=st.columns(2)
            with col1:
                st.write(f"### 🟢 ENTRADAS ID {id_b_upper} POR {tipo_periodo}")
                df_ent_g=df_ent.groupby(col_agrup, as_index=False)['QTD'].sum()
                if not df_ent_g.empty:
                    fig_ent=px.bar(df_ent_g, x=col_agrup, y='QTD', title=f"ENTRADAS ID {id_b_upper}")
                    st.plotly_chart(fig_ent, use_container_width=True)
                st.dataframe(df_ent_g, use_container_width=True)
                st.dataframe(df_ent.sort_values(by='DATA_DT', ascending=False), use_container_width=True, height=200)

            with col2:
                st.write(f"### 🔴 SAIDAS ID {id_b_upper} POR {tipo_periodo}")
                df_sai_g=df_sai.groupby(col_agrup, as_index=False)['QTD'].sum()
                if not df_sai_g.empty:
                    fig_sai=px.bar(df_sai_g, x=col_agrup, y='QTD', title=f"SAIDAS ID {id_b_upper}", color_discrete_sequence=['red'])
                    st.plotly_chart(fig_sai, use_container_width=True)
                st.dataframe(df_sai_g, use_container_width=True)
                st.dataframe(df_sai.sort_values(by='DATA_DT', ascending=False), use_container_width=True, height=200)

with tab_grd:
    st.header(f"7 - GRD SALA ANEXA - IDS INDIVIDUAIS - REGRA {TEMPO_QUARENTENA_HORAS}H + DATA/HORA")
    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    df_disp = pd.DataFrame(list(disp_sala.values())) if disp_sala else pd.DataFrame()
    if not df_disp.empty:
        df_disp['DATA_HORA_ATUALIZACAO']=agora.strftime("%d/%m/%Y %H:%M:%S")
        st.dataframe(df_disp[['ID','DESCRICAO','LOTE','SALDO','DATA_HORA_ATUALIZACAO']].sort_values(by='ID'), use_container_width=True)

    # GRD conjunto mesmo numero
    ids_disponiveis_sala = sorted(list(set([v['ID'] for v in disp_sala.values()]))) if disp_sala else []
    if ids_disponiveis_sala:
        tipo_grd = st.radio("Tipo GRD", ["INDIVIDUAL", "CONJUNTO MESMO NUMERO (ID 15+16)"], key="tipo_grd_main")
        if tipo_grd=="INDIVIDUAL":
            id_g=st.selectbox("ID", options=ids_disponiveis_sala, key="id_grd_ind2")
            saldo_id=[v for v in disp_sala.values() if v['ID']==id_g]
            lote_sel=st.selectbox("LOTE", options=sorted(list(set([v['LOTE'] for v in saldo_id]))), key="lote_grd_ind2")
            saldo_lote=[v for v in saldo_id if v['LOTE']==lote_sel][0]
            qtd=st.number_input(f"PALETES MAX {saldo_lote['PAL']:.1f}", value=1.0, key="qtd_grd_ind2")
            os_g=st.text_input("OS*", key="os_grd_ind2")
            if st.button("GERAR GRD INDIVIDUAL", type="primary", key="btn_grd_ind2"):
                num=f"GRD-SALA-{agora.strftime('%Y%m%d%H%M%S')}"
                tot=qtd*saldo_lote['QTD_PAL'] if saldo_lote['QTD_PAL']>0 else qtd*1250
                st.session_state.grd.append({"NUM_GRD":num,"ID":id_g,"DESCRICAO":saldo_lote['DESCRICAO'],"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"QTD_PALETES":qtd,"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"SAIDA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"ENTRADA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success(f"GRD {num}"); st.rerun()
        else:
            ids_multi=st.multiselect("IDS MESMO GRD (ex 15 e 16)", options=ids_disponiveis_sala, default=ids_disponiveis_sala[:2] if len(ids_disponiveis_sala)>=2 else ids_disponiveis_sala, key="ids_conj2")
            if ids_multi:
                qtds={}
                for id_sel in ids_multi:
                    saldo_id=[v for v in disp_sala.values() if v['ID']==id_sel]
                    lote_id=st.selectbox(f"LOTE ID {id_sel}", options=sorted(list(set([v['LOTE'] for v in saldo_id]))), key=f"lote_conj2_{id_sel}")
                    saldo_lote=[v for v in saldo_id if v['LOTE']==lote_id][0]
                    qtd=st.number_input(f"PAL ID {id_sel} MAX {saldo_lote['PAL']:.1f}", value=1.0, key=f"qtd_conj2_{id_sel}")
                    qtds[id_sel]={'lote':lote_id,'saldo_lote':saldo_lote,'qtd':qtd}
                os_g=st.text_input("OS*", key="os_conj2")
                if st.button("GERAR GRD CONJUNTO MESMO NUMERO", type="primary", key="btn_conj2"):
                    num=f"GRD-CONJ-{agora.strftime('%Y%m%d%H%M%S')}"
                    for id_sel in ids_multi:
                        info=qtds[id_sel]
                        tot=info['qtd']*info['saldo_lote']['QTD_PAL'] if info['saldo_lote']['QTD_PAL']>0 else info['qtd']*1250
                        st.session_state.grd.append({"NUM_GRD":num,"ID":id_sel,"DESCRICAO":info['saldo_lote']['DESCRICAO'],"LOTE":info['lote'],"MARCA":info['saldo_lote']['MARCA'],"QTD_PALETES":info['qtd'],"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S"),"TIPO_GRD":"CONJUNTO"})
                        st.session_state.mov.append({"ID":id_sel,"LOTE":info['lote'],"MARCA":info['saldo_lote']['MARCA'],"DESCRICAO":info['saldo_lote']['DESCRICAO'],"TIPO":"SAIDA","PALETES":info['qtd'],"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                        st.session_state.mov.append({"ID":id_sel,"LOTE":info['lote'],"MARCA":info['saldo_lote']['MARCA'],"DESCRICAO":info['saldo_lote']['DESCRICAO'],"TIPO":"ENTRADA","PALETES":info['qtd'],"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                    st.success(f"GRD CONJUNTO {num} IDS {', '.join(ids_multi)}"); st.rerun()
    if st.session_state.grd:
        st.dataframe(pd.DataFrame(st.session_state.grd).sort_values(by='DATA_HORA', ascending=False), use_container_width=True)

with tab_graf:
    st.header("8 - GRAFICOS")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        fig=px.bar(df.groupby('LOCAL', as_index=False)['SALDO'].sum(), x='LOCAL', y='SALDO', color='LOCAL')
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    st.header("9 - HISTORICO COMPLETO COM FILTRO ID INDIVIDUAL OU TODOS + ENTRADA/SAIDA + DIA/SEMANA/MES/ANO")

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

        # FILTROS
        ids_raw_hist = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
        ids_hist = sorted(list(set(ids_raw_hist)))
        ids_hist_com_todos = ["TODOS"] + ids_hist

        c1,c2,c3,c4 = st.columns(4)
        with c1:
            id_filtro = st.selectbox("FILTRAR POR ID - INDIVIDUAL OU TODOS", options=ids_hist_com_todos, key="filtro_id_hist")
        with c2:
            tipo_filtro_hist = st.selectbox("TIPO - ENTRADA OU SAIDA OU TODOS", options=["TODOS","ENTRADA","SAIDA"], key="filtro_tipo_hist")
        with c3:
            periodo_hist = st.selectbox("AGRUPAR POR PERIODO", options=["DIA","SEMANA","MES","ANO"], key="filtro_periodo_hist")
        with c4:
            local_filtro = st.selectbox("LOCAL - TODOS OU ESPECIFICO", options=["TODOS"]+LOCAIS, key="filtro_local_hist")

        # APLICA FILTROS
        df_filtrado = df_mov_all.copy()

        if id_filtro!= "TODOS":
            df_filtrado = df_filtrado[df_filtrado['ID'].astype(str).str.upper()==id_filtro]

        if tipo_filtro_hist!= "TODOS":
            df_filtrado = df_filtrado[df_filtrado['TIPO']==tipo_filtro_hist]

        if local_filtro!= "TODOS":
            df_filtrado = df_filtrado[df_filtrado['LOCAL_MOV']==local_filtro]

        if df_filtrado.empty:
            st.warning(f"Sem dados para ID={id_filtro} TIPO={tipo_filtro_hist} LOCAL={local_filtro}")
        else:
            # METRICAS
            df_ent = df_filtrado[df_filtrado['TIPO']=="ENTRADA"]
            df_sai = df_filtrado[df_filtrado['TIPO']=="SAIDA"]

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric(f"ENTRADAS ({id_filtro})", f"{df_ent['QTD'].sum():,.0f} UN", f"{df_ent['PAL'].sum():.1f} PAL")
            with c2: st.metric(f"SAIDAS ({id_filtro})", f"{df_sai['QTD'].sum():,.0f} UN", f"{df_sai['PAL'].sum():.1f} PAL")
            with c3: st.metric(f"SALDO ({id_filtro})", f"{df_ent['QTD'].sum()-df_sai['QTD'].sum():,.0f} UN")
            with c4: st.metric(f"QTD MOV ({id_filtro})", f"{len(df_filtrado)}")

            # COLUNA AGRUPAMENTO
            col_agrup = {'DIA':'DIA','SEMANA':'SEMANA','MES':'MES','ANO':'ANO'}[periodo_hist]

            # GRAFICO GERAL AGRUPADO ENTRADA VS SAIDA
            df_g_geral = df_filtrado.groupby([col_agrup,'TIPO'], as_index=False)['QTD'].sum()
            df_g_geral['TEXTO']=df_g_geral['QTD'].apply(lambda x: f"{x:,.0f}")
            if not df_g_geral.empty:
                fig_geral = px.bar(df_g_geral, x=col_agrup, y='QTD', color='TIPO', barmode='group', text='TEXTO', title=f"HISTORICO {id_filtro} - {tipo_filtro_hist} - POR {periodo_hist} - ENTRADA VS SAIDA")
                fig_geral.update_traces(textposition='inside', textfont=dict(size=12, color='white', family='Arial Black'))
                fig_geral.update_layout(height=600)
                st.plotly_chart(fig_geral, use_container_width=True)

            # GRAFICOS SEPARADOS ENTRADA E SAIDA
            col1,col2 = st.columns(2)
            with col1:
                st.subheader(f"🟢 ENTRADAS - ID {id_filtro} - POR {periodo_hist}")
                df_ent_g = df_ent.groupby(col_agrup, as_index=False)['QTD'].sum().sort_values(by=col_agrup)
                df_ent_g['TEXTO']=df_ent_g['QTD'].apply(lambda x: f"{x:,.0f}")
                if not df_ent_g.empty:
                    fig_ent = px.bar(df_ent_g, x=col_agrup, y='QTD', text='TEXTO', title=f"ENTRADAS {id_filtro} POR {periodo_hist}", color='QTD', color_continuous_scale='Greens')
                    fig_ent.update_traces(textposition='inside', textfont=dict(size=14, color='white'))
                    fig_ent.update_layout(height=400)
                    st.plotly_chart(fig_ent, use_container_width=True)
                st.dataframe(df_ent_g, use_container_width=True)
                st.write(f"Detalhado ENTRADAS {id_filtro}")
                st.dataframe(df_ent.sort_values(by='DATA_DT', ascending=False), use_container_width=True, height=250)

            with col2:
                st.subheader(f"🔴 SAIDAS - ID {id_filtro} - POR {periodo_hist}")
                df_sai_g = df_sai.groupby(col_agrup, as_index=False)['QTD'].sum().sort_values(by=col_agrup)
                df_sai_g['TEXTO']=df_sai_g['QTD'].apply(lambda x: f"{x:,.0f}")
                if not df_sai_g.empty:
                    fig_sai = px.bar(df_sai_g, x=col_agrup, y='QTD', text='TEXTO', title=f"SAIDAS {id_filtro} POR {periodo_hist}", color='QTD', color_continuous_scale='Reds')
                    fig_sai.update_traces(textposition='inside', textfont=dict(size=14, color='white'))
                    fig_sai.update_layout(height=400)
                    st.plotly_chart(fig_sai, use_container_width=True)
                st.dataframe(df_sai_g, use_container_width=True)
                st.write(f"Detalhado SAIDAS {id_filtro}")
                st.dataframe(df_sai.sort_values(by='DATA_DT', ascending=False), use_container_width=True, height=250)

            # TABELA GERAL AGRUPADA
            st.divider()
            st.subheader(f"📊 TABELA AGRUPADA POR {periodo_hist} - ID {id_filtro} - TIPO {tipo_filtro_hist} - LOCAL {local_filtro}")
            df_tabela = df_filtrado.groupby([col_agrup,'ID','TIPO','LOCAL_MOV'], as_index=False)['QTD'].sum()
            st.dataframe(df_tabela.sort_values(by=col_agrup, ascending=False), use_container_width=True, height=300)

            # HISTORICO DETALHADO COMPLETO FILTRADO
            st.subheader(f"📜 HISTORICO DETALHADO - ID {id_filtro} - {tipo_filtro_hist} - {local_filtro}")
            st.dataframe(df_filtrado.sort_values(by='DATA_DT', ascending=False), use_container_width=True, height=400)

            # GRAFICO POR LOCAL SE TODOS
            if local_filtro=="TODOS":
                df_local = df_filtrado.groupby(['LOCAL_MOV','TIPO'], as_index=False)['QTD'].sum()
                if not df_local.empty:
                    fig_local = px.bar(df_local, x='LOCAL_MOV', y='QTD', color='TIPO', barmode='group', title=f"POR LOCAL - ID {id_filtro} - {tipo_filtro_hist}")
                    st.plotly_chart(fig_local, use_container_width=True)

            # GRAFICO POR ID SE TODOS
            if id_filtro=="TODOS":
                df_id_g = df_filtrado.groupby(['ID','TIPO'], as_index=False)['QTD'].sum()
                df_top_ids = df_id_g.groupby('ID', as_index=False)['QTD'].sum().sort_values(by='QTD', ascending=False).head(10)
                df_top_ids['TEXTO']=df_top_ids['QTD'].apply(lambda x: f"{x:,.0f}")
                fig_ids = px.bar(df_top_ids, x='ID', y='QTD', text='TEXTO', color='ID', title=f"TOP 10 IDS - {tipo_filtro_hist} - POR {periodo_hist}")
                fig_ids.update_traces(textposition='inside', textfont=dict(size=14, color='white'))
                st.plotly_chart(fig_ids, use_container_width=True)

st.caption(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')} - HISTORICO COM FILTRO ID INDIVIDUAL/TODOS + ENTRADA/SAIDA + DIA/SEMANA/MES/ANO")
