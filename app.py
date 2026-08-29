import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
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
    try:
        if v is None or str(v).strip()=="": return float(d)
        return float(str(v).replace(",","."))
    except: return float(d)

def carregar(caminho):
    if not os.path.exists(caminho): return []
    try:
        df = pd.read_csv(caminho, dtype=str).fillna("")
        df.columns = [str(c).upper() for c in df.columns]
        if "MOVIMENTACAO" in caminho.upper() or "MOV" in caminho.upper():
            if "DATA_HORA" not in df.columns:
                if "DATA" in df.columns:
                    df["DATA_HORA"] = df["DATA"].astype(str) + " 00:00:00"
                else:
                    df["DATA_HORA"] = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
            if "DATA" not in df.columns:
                df["DATA"] = df["DATA_HORA"].astype(str).str.split(" ").str[0]
        return df.to_dict('records')
    except Exception as e:
        return []

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
        try:
            df_e = pd.read_csv(ARQ_EMAILS, dtype=str)
            df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
            u = df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
            if not u.empty:
                st.session_state.logado=True
                st.session_state.usuario=u.iloc[0].to_dict()
                st.rerun()
            else: st.error("Invalido")
        except Exception as ex: st.error(f"Erro: {ex}")
    st.stop()

user = st.session_state.usuario
is_admin = str(user.get('EMAIL','')).lower()=="admin@admin.com"
st.sidebar.write(f"Logado: {user.get('NOME')}")

import streamlit.components.v1 as components
auto_on = st.sidebar.toggle("AUTO 5min TV - TELA LIGADA", value=True)
if auto_on:
    components.html("""
    <script>
    let wakeLock = null;
    async function keepScreenOn(){ try{ if('wakeLock' in navigator){ wakeLock = await navigator.wakeLock.request('screen'); } }catch(e){} }
    keepScreenOn();
    setTimeout(()=>{ window.parent.location.reload(); }, 300000);
    document.addEventListener('visibilitychange', ()=>{ if(wakeLock!==null && document.visibilityState==='visible'){ keepScreenOn(); } });
    </script>
    <p style='color:green;font-size:10px;'>TELA LIGADA + AUTO 5min</p>
    """, height=30)

if st.sidebar.button("Sair"):
    st.session_state.logado=False
    st.session_state.usuario=None
    st.rerun()

def parse_data_hora(valor):
    try:
        if valor is None or str(valor).strip()=="": return dt.now(fuso).replace(tzinfo=None)
        s=str(valor).strip()
        if " " in s and ":" in s:
            try: return dt.strptime(s, "%d/%m/%Y %H:%M:%S")
            except: return dt.strptime(s, "%d/%m/%Y %H:%M")
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
            saldos[chave]={'ID':idp,'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':q,'PAL':safe_float(r.get('ENTRADA',0)),'QTD_PAL':safe_float(r.get('QTD_PALETE',0)),'ULT_ATUAL':str(r.get('FABRICACAO',''))}
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
            saldos[chave]={'ID':idp,'DESCRICAO':str(m.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':0,'PAL':0,'QTD_PAL':0,'ULT_ATUAL':str(m.get('DATA_HORA', m.get('DATA','')))}
        if chave not in saldos: continue
        if m.get('TIPO')=="ENTRADA":
            saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0))
            saldos[chave]['PAL']+=safe_float(m.get('PALETES',0))
            saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA', m.get('DATA','')))
        else:
            saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0))
            saldos[chave]['PAL']-=safe_float(m.get('PALETES',0))
            saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA', m.get('DATA','')))
    return saldos

def get_saldo_sala_com_quarentena():
    agora_dt = datetime.now(fuso).replace(tzinfo=None)
    saldos = get_saldos()
    saldo_sala_total = {}
    saldo_sala_pendente = {}
    saldo_sala_disponivel = {}
    for k,v in saldos.items():
        if v['LOCAL']==LOCAL_SALA and v['SALDO']>0:
            saldo_sala_total[k]=v.copy()
            saldo_sala_disponivel[k]=v.copy()
    for m in st.session_state.mov:
        try:
            if str(m.get('LOCAL_MOV','')).upper()!=LOCAL_SALA.upper(): continue
            if m.get('TIPO')!="ENTRADA": continue
            idp=str(m.get('ID','')).upper().strip()
            lote=str(m.get('LOTE','')).upper().strip()
            marca=str(m.get('MARCA','SEM MARCA')).upper()
            chave=f"{idp}__{LOCAL_SALA}__{marca}__{lote}"
            data_mov = parse_data_hora(m.get('DATA_HORA', m.get('DATA','')))
            diff_horas = (agora_dt - data_mov).total_seconds()/3600
            if diff_horas < TEMPO_QUARENTENA_HORAS:
                q = safe_float(m.get('TOTAL_QTD',0))
                pal = safe_float(m.get('PALETES',0))
                if chave not in saldo_sala_pendente:
                    saldo_sala_pendente[chave]={'ID':idp,'LOTE':lote,'MARCA':marca,'DESCRICAO':str(m.get('DESCRICAO','')).upper(),'QTD_PENDENTE':q,'PAL_PENDENTE':pal,'DATA_ENTRADA':str(m.get('DATA_HORA', m.get('DATA',''))),'HORAS_RESTANTES':TEMPO_QUARENTENA_HORAS-diff_horas,'DATA_LIBERACAO':data_mov+timedelta(hours=TEMPO_QUARENTENA_HORAS),'ULT_ATUAL':str(m.get('DATA_HORA',''))}
                else:
                    saldo_sala_pendente[chave]['QTD_PENDENTE']+=q
                    saldo_sala_pendente[chave]['PAL_PENDENTE']+=pal
                if chave in saldo_sala_disponivel:
                    saldo_sala_disponivel[chave]['SALDO']-=q
                    saldo_sala_disponivel[chave]['PAL']-=pal
                    if saldo_sala_disponivel[chave]['SALDO']<0: saldo_sala_disponivel[chave]['SALDO']=0
                    if saldo_sala_disponivel[chave]['PAL']<0: saldo_sala_disponivel[chave]['PAL']=0
        except: continue
    saldo_sala_disponivel = {k:v for k,v in saldo_sala_disponivel.items() if v['SALDO']>0}
    return saldo_sala_total, saldo_sala_pendente, saldo_sala_disponivel

def df_safe_sort(df, asc=False):
    try:
        if df.empty: return df
        if "DATA_HORA" in df.columns:
            return df.sort_values(by="DATA_HORA", ascending=asc)
        if "DATA" in df.columns:
            df["_dt"] = df["DATA"].apply(lambda x: parse_data_hora(x))
            return df.sort_values(by="_dt", ascending=asc).drop(columns=["_dt"], errors='ignore')
        return df
    except: return df

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')}")
tabs = st.tabs(["ADMIN","DASHBOARD","CADASTRO AUTO","MOV AUTO","ESTOQUE","BUSCA ID","GRD SALA 48H AUTO","GRAFICOS","HISTORICO FILTRO"])
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
    st.header("2 - DASHBOARD SALA ANEXA IDS INDIVIDUAIS + DATA/HORA")
    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    df_total = pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    if not df_total.empty:
        c1,c2,c3=st.columns(3)
        with c1: st.metric("SALA TOTAL", f"{df_total['SALDO'].sum():,.0f}")
        with c2: st.metric(f"BLOQ <{TEMPO_QUARENTENA_HORAS}H", f"{sum([v['QTD_PENDENTE'] for v in pendente_sala.values()]) if pendente_sala else 0:,.0f}")
        with c3: st.metric("DISP GRD", f"{sum([v['SALDO'] for v in disp_sala.values()]) if disp_sala else 0:,.0f}")
        st.dataframe(df_total.sort_values(by='ID'), use_container_width=True)
        df_id = df_total.groupby(['ID','DESCRICAO'], as_index=False)['SALDO'].sum()
        fig=px.bar(df_id, x='ID', y='SALDO', color='ID', text='SALDO')
        st.plotly_chart(fig, use_container_width=True, key="dash_final")

with tab_cad:
    st.header("3 - CADASTRO AUTO - SO ID")
    id_in = st.text_input("DIGITE ID*", key="id_cad_auto_final")
    desc_auto=""; marca_auto=""; qtd_auto=1250.0; lote_auto=""; encontrou=False
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_in.upper().strip():
                desc_auto=r.get('DESCRICAO',''); marca_auto=r.get('MARCA',''); qtd_auto=safe_float(r.get('QTD_PALETE',1250.0),1250.0); lote_auto=r.get('LOTE',''); encontrou=True; break
    if encontrou:
        st.success(f"ID {id_in.upper()} AUTO {desc_auto} | {marca_auto}")
        with st.form("form_cad_auto_final"):
            st.text_input("ID AUTO", value=id_in.upper(), disabled=True)
            st.text_input("DESC AUTO", value=desc_auto, disabled=True)
            lote_novo = st.text_input(f"LOTE BASE {lote_auto}", key="lote_novo_auto_final")
            locais_sel=st.multiselect("LOCAIS*", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad_auto_final")
            ent_in=st.number_input("PALETES*", value=1.0, min_value=0.1, key="ent_cad_auto_final")
            if st.form_submit_button("CADASTRAR AUTO", type="primary"):
                lote_final = lote_novo.upper() if lote_novo else lote_auto
                if lote_final and locais_sel:
                    for local_cad in locais_sel:
                        total=qtd_auto*ent_in
                        st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_auto.upper(),"MARCA":marca_auto.upper(),"LOTE":lote_final.upper(),"QTD_PALETE":qtd_auto,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                    st.success("OK"); st.rerun()
    else:
        if id_in: st.warning(f"NOVO ID {id_in.upper()}")
        with st.form("form_cad_novo_final"):
            st.text_input("ID", value=id_in.upper() if id_in else "", disabled=True)
            desc_in=st.text_input("DESCRICAO*", key="desc_cad_novo_final")
            marca_in=st.text_input("MARCA*", key="marca_cad_novo_final")
            lote_in=st.text_input("LOTE*", key="lote_cad_novo_final")
            locais_sel=st.multiselect("LOCAIS*", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad_novo_final")
            qtd_in=st.number_input("QTD/PAL*", value=1250.0, key="qtd_cad_novo_final")
            ent_in=st.number_input("PALETES", value=0.0, key="ent_cad_novo2_final")
            if st.form_submit_button("CADASTRAR NOVO", type="primary"):
                if id_in and desc_in and marca_in and lote_in and locais_sel:
                    for local_cad in locais_sel:
                        total=qtd_in*ent_in
                        st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                    st.success("OK"); st.rerun()

with tab_mov:
    st.header("4 - MOVIMENTACAO AUTO - SO ID")
    id_mov_in = st.text_input("DIGITE ID* AUTO", key="id_mov_auto_final")
    desc_mov_auto=""; marca_mov_auto=""; qtd_mov_auto=1250.0; encontrou_mov=False; lotes_existentes=[]
    if id_mov_in:
        id_mov_up = id_mov_in.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_mov_up:
                desc_mov_auto=r.get('DESCRICAO',''); marca_mov_auto=r.get('MARCA',''); qtd_mov_auto=safe_float(r.get('QTD_PALETE',1250.0),1250.0); encontrou_mov=True
                if r.get('LOTE','') and str(r.get('LOTE','')).upper() not in lotes_existentes: lotes_existentes.append(str(r.get('LOTE','')).upper())
        for v in get_saldos().values():
            if v['ID']==id_mov_up and v['SALDO']>0 and v['LOTE'] not in lotes_existentes: lotes_existentes.append(v['LOTE'])
    if not id_mov_in: st.info("DIGITE ID")
    elif not encontrou_mov: st.error(f"ID {id_mov_in.upper()} NAO CADASTRADO")
    else:
        st.success(f"ID {id_mov_in.upper()} AUTO {desc_mov_auto} | {marca_mov_auto} | LOTES: {', '.join(lotes_existentes)}")
        saldo_id = [v for v in get_saldos().values() if v['ID']==id_mov_in.upper() and v['SALDO']>0]
        if saldo_id: st.dataframe(pd.DataFrame(saldo_id), use_container_width=True)
        with st.form("form_mov_auto_final"):
            st.text_input("ID AUTO", value=id_mov_in.upper(), disabled=True)
            st.text_input("DESC AUTO", value=desc_mov_auto, disabled=True)
            if lotes_existentes:
                lote_sel = st.selectbox("LOTE AUTO", options=lotes_existentes+["NOVO LOTE"], key="lote_mov_sel_final")
                lote_final = st.text_input("NOVO LOTE*", key="lote_mov_novo_final") if lote_sel=="NOVO LOTE" else lote_sel
            else: lote_final = st.text_input("LOTE*", key="lote_mov_sem_final")
            marca_final = st.text_input("MARCA AUTO", value=marca_mov_auto, key="marca_mov_final")
            local_sel = st.selectbox("LOCAL*", options=LOCAIS, key="local_mov_final")
            tipo_sel = st.selectbox("TIPO*", options=["ENTRADA","SAIDA"], key="tipo_mov_final")
            pal_sel = st.number_input("PALETES*", value=1.0, min_value=0.1, key="pal_mov_final")
            if st.form_submit_button(f"CONFIRMAR MOV AUTO ID {id_mov_in.upper()} - {agora.strftime('%H:%M:%S')}", type="primary", use_container_width=True):
                if lote_final:
                    agora_str = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    tot=pal_sel*qtd_mov_auto
                    base={"ID":id_mov_in.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper(),"DESCRICAO":desc_mov_auto,"PALETES":pal_sel,"TOTAL_QTD":tot,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str}
                    if local_sel==LOCAL_GALPAO and tipo_sel=="ENTRADA":
                        st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_GALPAO})
                    elif local_sel==LOCAL_GALPAO and tipo_sel=="SAIDA":
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_GALPAO})
                        st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                    elif local_sel==LOCAL_SALA and tipo_sel=="ENTRADA":
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_GALPAO})
                        st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_SALA})
                    elif local_sel==LOCAL_SALA and tipo_sel=="SAIDA":
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_SALA})
                        st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                    elif local_sel==LOCAL_OFICINA and tipo_sel=="ENTRADA":
                        st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                    else:
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_OFICINA})
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                    st.success("OK"); st.rerun()
    st.divider()
    st.write("ULTIMAS 20 MOV - SEM ERRO")
    if st.session_state.mov:
        df_tmp = pd.DataFrame(st.session_state.mov)
        df_tmp = df_safe_sort(df_tmp, False)
        st.dataframe(df_tmp.head(20), use_container_width=True)

with tab_est:
    st.header("5 - ESTOQUE")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista: st.dataframe(pd.DataFrame(lista).sort_values(by='ID'), use_container_width=True)

with tab_busca:
    st.header("6 - BUSCA ID - ENTRADA/SAIDA DIA/SEMANA/MES/ANO")
    id_b = st.text_input("ID BUSCA", key="id_busca_final")
    if id_b:
        id_b_upper=id_b.upper().strip()
        saldos=get_saldos()
        lista_saldo=[v for v in saldos.values() if v['ID']==id_b_upper and v['SALDO']>0]
        if lista_saldo: st.dataframe(pd.DataFrame(lista_saldo), use_container_width=True)
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
            with c1: tipo_periodo=st.selectbox("AGRUPAR", ["DIA","SEMANA","MES","ANO"], key=f"periodo_busca_{id_b_upper}")
            with c2: tipo_filtro=st.selectbox("TIPO", ["TODOS","ENTRADA","SAIDA"], key=f"tipo_busca_{id_b_upper}")
            df_f=df_mov.copy()
            if tipo_filtro!="TODOS": df_f=df_f[df_f['TIPO']==tipo_filtro]
            col_agrup = {'DIA':'DIA','SEMANA':'SEMANA','MES':'MES','ANO':'ANO'}[tipo_periodo]
            df_g=df_f.groupby([col_agrup,'TIPO'], as_index=False)['QTD'].sum()
            if not df_g.empty:
                fig=px.bar(df_g, x=col_agrup, y='QTD', color='TIPO', barmode='group')
                st.plotly_chart(fig, use_container_width=True, key=f"busca_{id_b_upper}_{tipo_periodo}_{tipo_filtro}")

with tab_grd:
    st.header(f"7 - GRD SALA ANEXA 48H - IDS 15/16 MESMO NUMERO - DATA/HORA")
    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena()
    df_total = pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    df_disp = pd.DataFrame(list(disp_sala.values())) if disp_sala else pd.DataFrame()
    df_pend = pd.DataFrame(list(pendente_sala.values())) if pendente_sala else pd.DataFrame()
    if not df_total.empty: st.dataframe(df_total.sort_values(by='ID'), use_container_width=True)
    if not df_pend.empty:
        df_pend_show = pd.DataFrame([{'ID':v['ID'],'LOTE':v['LOTE'],'QTD':v['QTD_PENDENTE'],'ENTRADA':v['DATA_ENTRADA'],'LIBERACAO':v['DATA_LIBERACAO'].strftime("%d/%m/%Y %H:%M:%S"),'REST':f"{v['HORAS_RESTANTES']:.1f}h"} for v in pendente_sala.values()])
        st.dataframe(df_pend_show, use_container_width=True)
    ids_disponiveis = sorted(list(set([v['ID'] for v in disp_sala.values()]))) if disp_sala else []
    if ids_disponiveis:
        tipo_grd = st.radio("Tipo GRD", ["INDIVIDUAL", "CONJUNTO MESMO NUMERO"], key="tipo_grd_final")
        if tipo_grd=="INDIVIDUAL":
            id_g=st.selectbox("ID", options=ids_disponiveis, key="id_grd_final")
            saldo_id=[v for v in disp_sala.values() if v['ID']==id_g]
            lote_sel=st.selectbox("LOTE", options=sorted(list(set([v['LOTE'] for v in saldo_id]))), key="lote_grd_final")
            saldo_lote=[v for v in saldo_id if v['LOTE']==lote_sel][0]
            qtd=st.number_input(f"PAL MAX {saldo_lote['PAL']:.1f}", value=1.0, key="qtd_grd_final")
            os_g=st.text_input("OS*", key="os_grd_final")
            if st.button("GERAR GRD INDIVIDUAL", type="primary", key="btn_grd_final"):
                num=f"GRD-SALA-{agora.strftime('%Y%m%d%H%M%S')}"
                tot=qtd*saldo_lote['QTD_PAL'] if saldo_lote['QTD_PAL']>0 else qtd*1250
                st.session_state.grd.append({"NUM_GRD":num,"ID":id_g,"DESCRICAO":saldo_lote['DESCRICAO'],"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"QTD_PALETES":qtd,"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_HORA_ATUALIZACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"SAIDA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"ENTRADA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success(f"GRD {num}"); st.rerun()
        else:
            ids_multi=st.multiselect("IDS MESMO GRD", options=ids_disponiveis, default=ids_disponiveis[:2] if len(ids_disponiveis)>=2 else ids_disponiveis, key="ids_conj_final")
            if ids_multi:
                qtds={}
                for id_sel in ids_multi:
                    saldo_id=[v for v in disp_sala.values() if v['ID']==id_sel]
                    lote_id=st.selectbox(f"LOTE ID {id_sel}", options=sorted(list(set([v['LOTE'] for v in saldo_id]))), key=f"lote_conj_final_{id_sel}")
                    saldo_lote=[v for v in saldo_id if v['LOTE']==lote_id][0]
                    qtd=st.number_input(f"PAL ID {id_sel} MAX {saldo_lote['PAL']:.1f}", value=1.0, key=f"qtd_conj_final_{id_sel}")
                    qtds[id_sel]={'lote':lote_id,'saldo_lote':saldo_lote,'qtd':qtd}
                os_g=st.text_input("OS* CONJUNTO", key="os_conj_final")
                if st.button("GERAR GRD CONJUNTO MESMO NUMERO", type="primary", use_container_width=True, key="btn_conj_final"):
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
        df_grd_show = pd.DataFrame(st.session_state.grd)
        df_grd_show = df_safe_sort(df_grd_show, False)
        st.dataframe(df_grd_show, use_container_width=True)

with tab_graf:
    st.header("8 - GRAFICOS")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        fig=px.bar(df.groupby('LOCAL', as_index=False)['SALDO'].sum(), x='LOCAL', y='SALDO', color='LOCAL')
        st.plotly_chart(fig, use_container_width=True, key="graf_final_v2")

with tab_hist:
    st.header("9 - HISTORICO FILTRO ID/TODOS + ENTRADA/SAIDA + DIA/SEMANA/MES/ANO")
    if not st.session_state.mov: st.warning("Sem mov")
    else:
        try:
            df_mov_all = pd.DataFrame(st.session_state.mov)
            if "DATA_HORA" not in df_mov_all.columns: df_mov_all["DATA_HORA"] = df_mov_all.get("DATA","")
            df_mov_all['DATA_DT'] = df_mov_all['DATA'].apply(lambda x: parse_data_hora(x))
            df_mov_all['DIA'] = df_mov_all['DATA_DT'].dt.strftime("%d/%m/%Y")
            df_mov_all['SEMANA'] = df_mov_all['DATA_DT'].dt.strftime("%Y-W%W")
            df_mov_all['MES'] = df_mov_all['DATA_DT'].dt.strftime("%m/%Y")
            df_mov_all['ANO'] = df_mov_all['DATA_DT'].dt.strftime("%Y")
            df_mov_all['QTD'] = df_mov_all['TOTAL_QTD'].apply(lambda x: safe_float(x))
            ids_raw = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
            ids_hist = ["TODOS"] + sorted(list(set(ids_raw)))
            c1,c2,c3,c4 = st.columns(4)
            with c1: id_filtro = st.selectbox("ID", options=ids_hist, key="filtro_id_final")
            with c2: tipo_filtro = st.selectbox("TIPO", options=["TODOS","ENTRADA","SAIDA"], key="filtro_tipo_final")
            with c3: periodo = st.selectbox("PERIODO", options=["DIA","SEMANA","MES","ANO"], key="filtro_periodo_final")
            with c4: local_filtro = st.selectbox("LOCAL", options=["TODOS"]+LOCAIS, key="filtro_local_final")
            df_f = df_mov_all.copy()
            if id_filtro!="TODOS": df_f = df_f[df_f['ID'].astype(str).str.upper()==id_filtro]
            if tipo_filtro!="TODOS": df_f = df_f[df_f['TIPO']==tipo_filtro]
            if local_filtro!="TODOS": df_f = df_f[df_f['LOCAL_MOV']==local_filtro]
            if not df_f.empty:
                df_ent = df_f[df_f['TIPO']=="ENTRADA"]
                df_sai = df_f[df_f['TIPO']=="SAIDA"]
                c1,c2,c3,c4 = st.columns(4)
                with c1: st.metric(f"ENT {id_filtro}", f"{df_ent['QTD'].sum():,.0f}")
                with c2: st.metric(f"SAI {id_filtro}", f"{df_sai['QTD'].sum():,.0f}")
                with c3: st.metric(f"SALDO {id_filtro}", f"{df_ent['QTD'].sum()-df_sai['QTD'].sum():,.0f}")
                with c4: st.metric("QTD MOV", f"{len(df_f)}")
                col_agrup = {'DIA':'DIA','SEMANA':'SEMANA','MES':'MES','ANO':'ANO'}[periodo]
                df_g = df_f.groupby([col_agrup,'TIPO'], as_index=False)['QTD'].sum()
                if not df_g.empty:
                    fig=px.bar(df_g, x=col_agrup, y='QTD', color='TIPO', barmode='group', text='QTD')
                    st.plotly_chart(fig, use_container_width=True, key=f"hist_{id_filtro}_{tipo_filtro}_{periodo}_{local_filtro}")
                st.dataframe(df_safe_sort(df_f, False), use_container_width=True, height=400)
        except Exception as e:
            st.error(f"Erro hist: {e}")
            st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

st.caption(f"REFORMA FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')} - FINAL 100% - AUTO 5min + SEM KeyError")
