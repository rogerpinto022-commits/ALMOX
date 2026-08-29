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

TIPOS_EMBALAGEM = ["PALETE", "CAIXA", "SACO", "FARDO", "BAG", "TAMBOR", "UNIDADE"]

def safe_float(v, d=0.0):
    try:
        if v is None or str(v).strip() == "": return float(d)
        return float(str(v).replace(",", "."))
    except: return float(d)

def parse_data_hora(valor):
    try:
        if valor is None or str(valor).strip() == "": return dt.now(fuso).replace(tzinfo=None)
        s = str(valor).strip()
        if " " in s and ":" in s:
            try: return dt.strptime(s, "%d/%m/%Y %H:%M:%S")
            except: return dt.strptime(s, "%d/%m/%Y %H:%M")
    except: pass
    try: return dt.strptime(str(valor).split(" ")[0], "%d/%m/%Y")
    except: return dt.now(fuso).replace(tzinfo=None)

def carregar(caminho):
    if not os.path.exists(caminho): return []
    try: df = pd.read_csv(caminho, dtype=str, encoding='utf-8').fillna("")
    except:
        try: df = pd.read_csv(caminho, dtype=str, encoding='latin-1').fillna("")
        except: return []
    df.columns = [str(c).upper().strip() for c in df.columns]
    if "MOV" in caminho.upper():
        if "DATA_HORA" not in df.columns: df["DATA_HORA"] = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
        if "DATA" not in df.columns: df["DATA"] = df["DATA_HORA"].astype(str).str.split(" ").str[0]
    return df.to_dict('records')

def salvar_tudo():
    try:
        if st.session_state.cad: pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD, index=False, encoding='utf-8')
        if st.session_state.mov: pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False, encoding='utf-8')
        if st.session_state.grd: pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD, index=False, encoding='utf-8')
        return True
    except: return False

def df_safe_sort(df, asc=False):
    try:
        if df is None or df.empty: return df
        if "DATA_HORA" in df.columns: return df.sort_values(by="DATA_HORA", ascending=asc)
        return df
    except: return df

def get_saldos():
    saldos = {}
    # Mapa de caracteristicas por ID
    carac_por_id = {}
    for r in st.session_state.cad:
        idp = str(r.get('ID','')).upper().strip()
        if idp and idp not in carac_por_id:
            carac_por_id[idp] = {
                'DESCRICAO': str(r.get('DESCRICAO','')).upper(),
                'TIPO_EMBALAGEM': str(r.get('TIPO_EMBALAGEM','PALETE')).upper(),
                'QTD_POR_EMBALAGEM': safe_float(r.get('QTD_POR_EMBALAGEM',1250),1250),
                'MARCA': str(r.get('MARCA','SEM MARCA')).upper()
            }

    for r in st.session_state.cad:
        try:
            idp = str(r.get('ID','')).upper().strip(); lote = str(r.get('LOTE','')).upper().strip()
            if not idp: continue
            local = str(r.get('LOCAL',LOCAL_GALPAO)).upper()
            if "SALA" in local: local=LOCAL_SALA
            elif "OFIC" in local: local=LOCAL_OFICINA
            else: local=LOCAL_GALPAO
            if not lote: continue
            marca = str(r.get('MARCA','SEM MARCA')).upper()
            carac = carac_por_id.get(idp, {})
            chave=f"{idp}__{local}__{marca}__{lote}"
            q=safe_float(r.get('TOTAL',0))
            if q==0: q=safe_float(r.get('QTD_POR_EMBALAGEM',0))*safe_float(r.get('ENTRADA',0))
            if chave not in saldos:
                saldos[chave]={'ID':idp,'DESCRICAO':carac.get('DESCRICAO',''), 'TIPO_EMBALAGEM':carac.get('TIPO_EMBALAGEM','PALETE'), 'QTD_POR_EMBALAGEM':carac.get('QTD_POR_EMBALAGEM',1250), 'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':q,'EMBALAGENS':safe_float(r.get('ENTRADA',0)),'ULT_ATUAL':str(r.get('FABRICACAO','')), 'CALCULO': f"{safe_float(r.get('ENTRADA',0))} x {carac.get('QTD_POR_EMBALAGEM',1250)} = {q}"}
            else: saldos[chave]['SALDO']+=q; saldos[chave]['EMBALAGENS']+=safe_float(r.get('ENTRADA',0))
        except: continue

    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip(); lote=str(m.get('LOTE','')).upper().strip()
            if not idp or not lote: continue
            local=str(m.get('LOCAL_MOV',LOCAL_GALPAO)).upper()
            if "SALA" in local: local=LOCAL_SALA
            elif "OFIC" in local: local=LOCAL_OFICINA
            else: local=LOCAL_GALPAO
            marca=str(m.get('MARCA','SEM MARCA')).upper()
            carac = carac_por_id.get(idp, {})
            chave=f"{idp}__{local}__{marca}__{lote}"
            if chave not in saldos and m.get('TIPO')=="ENTRADA":
                saldos[chave]={'ID':idp,'DESCRICAO':carac.get('DESCRICAO',''),'TIPO_EMBALAGEM':carac.get('TIPO_EMBALAGEM','PALETE'),'QTD_POR_EMBALAGEM':carac.get('QTD_POR_EMBALAGEM',1250),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':0,'EMBALAGENS':0,'ULT_ATUAL':str(m.get('DATA_HORA','')), 'CALCULO':''}
            if chave not in saldos: continue
            if m.get('TIPO')=="ENTRADA":
                saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0)); saldos[chave]['EMBALAGENS']+=safe_float(m.get('PALETES',0)); saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
                saldos[chave]['CALCULO']=f"{safe_float(m.get('PALETES',0))} {carac.get('TIPO_EMBALAGEM','')} x {carac.get('QTD_POR_EMBALAGEM',0)} = {safe_float(m.get('TOTAL_QTD',0))}"
            else:
                saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0)); saldos[chave]['EMBALAGENS']-=safe_float(m.get('PALETES',0)); saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
        except: continue
    return saldos, carac_por_id

def get_saldo_sala_com_quarentena(tempo_horas=None):
    if tempo_horas is None: tempo_horas = st.session_state.get('tempo_quarentena',48)
    agora_dt = datetime.now(fuso).replace(tzinfo=None)
    saldos,_ = get_saldos()
    total={}; pend={}; disp={}
    for k,v in saldos.items():
        if v['LOCAL']==LOCAL_SALA and v['SALDO']>0:
            total[k]=v.copy(); disp[k]=v.copy()
    for m in st.session_state.mov:
        try:
            if str(m.get('LOCAL_MOV','')).upper()!=LOCAL_SALA.upper(): continue
            if m.get('TIPO')!="ENTRADA": continue
            idp=str(m.get('ID','')).upper().strip(); lote=str(m.get('LOTE','')).upper().strip()
            marca=str(m.get('MARCA','SEM MARCA')).upper()
            chave=f"{idp}__{LOCAL_SALA}__{marca}__{lote}"
            data_mov=parse_data_hora(m.get('DATA_HORA',''))
            diff=(agora_dt-data_mov).total_seconds()/3600
            if diff < tempo_horas:
                q=safe_float(m.get('TOTAL_QTD',0))
                if chave not in pend:
                    pend[chave]={'ID':idp,'LOTE':lote,'QTD_PENDENTE':q,'DATA_ENTRADA':str(m.get('DATA_HORA','')),'HORAS_RESTANTES':tempo_horas-diff,'DATA_LIBERACAO':data_mov+timedelta(hours=tempo_horas)}
                else: pend[chave]['QTD_PENDENTE']+=q
                if chave in disp:
                    disp[chave]['SALDO']-=q
                    if disp[chave]['SALDO']<0: disp[chave]['SALDO']=0
        except: continue
    disp={k:v for k,v in disp.items() if v['SALDO']>0}
    return total,pend,disp

# SESSION
if 'inicializado' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD); st.session_state.mov=carregar(ARQ_MOV); st.session_state.grd=carregar(ARQ_GRD); st.session_state.inicializado=True
if 'tempo_quarentena' not in st.session_state: st.session_state.tempo_quarentena=48
if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'logado' not in st.session_state: st.session_state.logado=False
if 'usuario' not in st.session_state: st.session_state.usuario=None
if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA DE FORNOS</h1>", unsafe_allow_html=True)
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS,dtype=str).fillna(""); df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
        u=df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
        if not u.empty: st.session_state.logado=True; st.session_state.usuario=u.iloc[0].to_dict(); st.rerun()
        else: st.error("Invalido")
    st.stop()

user=st.session_state.usuario
is_admin=str(user.get('EMAIL','')).lower()=="admin@admin.com"
import streamlit.components.v1 as components
components.html("<script>let w=null;async function k(){try{if('wakeLock' in navigator){w=await navigator.wakeLock.request('screen');}}catch(e){}}k();</script><p style='color:green;font-size:12px;'>✅ TELA LIGADA - CALCULO AUTOMATICO</p>",height=30)
st.sidebar.write(f"Logado: {user.get('NOME')}")
st.sidebar.metric("⏰ QUARENTENA", f"{st.session_state.tempo_quarentena}H")
st.sidebar.write(f"📦 CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
if st.session_state.cad: st.sidebar.download_button("BAIXAR CAD",pd.DataFrame(st.session_state.cad).to_csv(index=False),"cad.csv")
if st.session_state.mov: st.sidebar.download_button("BAIXAR MOV",pd.DataFrame(st.session_state.mov).to_csv(index=False),"mov.csv")
if st.sidebar.button("Sair"): salvar_tudo(); st.session_state.logado=False; st.session_state.usuario=None; st.rerun()

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')}")
tabs=st.tabs(["ADMIN","DASHBOARD","CADASTRO CARACTERISTICAS","MOV - LOTE+LOCAL","ESTOQUE CALCULADO","BUSCA ID","GRD VOCE DECIDE HORAS","GRAFICO EMPILHADO POR ID","HISTORICO"])
tab_admin, tab_dash, tab_cad, tab_mov, tab_est, tab_busca, tab_grd, tab_graf, tab_hist = tabs

with tab_admin:
    st.header("1 - ADMIN")
    if is_admin:
        with st.form("form_admin"):
            email_new=st.text_input("Email"); nome_new=st.text_input("Nome"); senha_new=st.text_input("Senha")
            local_new=st.selectbox("Local",LOCAIS_ACESSO); status_new=st.selectbox("Status",["LIBERADO","BLOQUEADO"])
            if st.form_submit_button("SALVAR"):
                if email_new and senha_new:
                    df=pd.read_csv(ARQ_EMAILS); df=df[df['EMAIL'].astype(str).str.lower()!=email_new.lower()]
                    novo=pd.DataFrame([{"EMAIL":email_new.lower(),"SENHA":senha_new,"LOCAL":local_new,"STATUS":status_new,"NOME":nome_new.upper()}])
                    pd.concat([df,novo],ignore_index=True).to_csv(ARQ_EMAILS,index=False); st.rerun()
        st.dataframe(pd.read_csv(ARQ_EMAILS),use_container_width=True)

with tab_dash:
    st.header(f"2 - DASHBOARD - {st.session_state.tempo_quarentena}H")
    total_sala,pend,disp = get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    saldos,_=get_saldos()
    if not total_sala: total_sala={k:v for k,v in saldos.items() if v['LOCAL']==LOCAL_SALA and v['SALDO']>0}; disp=total_sala.copy()
    df_total=pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    if df_total.empty: st.error(f"SEM ESTOQUE {LOCAL_SALA}");
    else:
        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric("SALA TOTAL",f"{df_total['SALDO'].sum():,.0f}")
        with c2: st.metric(f"BLOQ <{st.session_state.tempo_quarentena}H",f"{sum([v['QTD_PENDENTE'] for v in pend.values()]) if pend else 0:,.0f}")
        with c3: st.metric(f"DISP >{st.session_state.tempo_quarentena}H",f"{pd.DataFrame(list(disp.values()))['SALDO'].sum() if disp else df_total['SALDO'].sum():,.0f}")
        with c4: st.metric("IDS",f"{df_total['ID'].nunique()}")
        st.dataframe(df_total[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','LOTE','SALDO','EMBALAGENS','ULT_ATUAL','CALCULO','LOCAL']],use_container_width=True)

# ========== 3 CADASTRO CARACTERISTICAS - VOCE PREENCHE ID DESCRICAO TIPO EMBALAGEM QTD POR EMBALAGEM ==========
with tab_cad:
    st.header("3 - CADASTRO - CARACTERISTICAS DO PRODUTO - SISTEMA CALCULA")
    st.info("ℹ️ Preencha: ID + Descrição + Tipo Embalagem + Qtd por Embalagem. Sistema calcula total na movimentação e mostra no estoque e gráfico")

    id_in = st.text_input("ID* - Ex: 15", key="cad_id")

    existe=False
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==id_in.upper().strip():
                existe=True; break

    if existe:
        st.warning(f"ID {id_in.upper()} JA CADASTRADO")
        st.dataframe(pd.DataFrame([r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_in.upper()])[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','MARCA']],use_container_width=True)
    else:
        with st.form("form_cad_carac"):
            st.text_input("ID*", value=id_in.upper() if id_in else "", disabled=True, key="id_form_carac")
            c1,c2=st.columns(2)
            with c1:
                desc = st.text_input("DESCRIÇÃO* - Ex: TIJOLO REFRATARIO 65% ALUMINA", key="desc_carac")
                tipo_emb = st.selectbox("TIPO DE EMBALAGEM* - Ex: PALETE, CAIXA, SACO", TIPOS_EMBALAGEM, key="tipo_emb_carac")
            with c2:
                qtd_emb = st.number_input("QTD POR EMBALAGEM* - Ex: 1250 unidades por palete", min_value=0.1, value=1250.0, step=10.0, key="qtd_emb_carac")
                marca = st.text_input("MARCA (opcional)", key="marca_carac")

            st.write(f"### SISTEMA VAI CALCULAR: X {tipo_emb} x {qtd_emb} = TOTAL")
            st.caption(f"Ex: 2 {tipo_emb} x {qtd_emb} = {2*qtd_emb:,.0f} unidades")

            if st.form_submit_button("✅ CADASTRAR CARACTERISTICAS - GUARDA", type="primary", use_container_width=True):
                if not id_in or not desc:
                    st.error("ID e DESCRIÇÃO são obrigatórios")
                else:
                    st.session_state.cad.append({
                        "ID": id_in.upper().strip(),
                        "DESCRICAO": desc.upper(),
                        "TIPO_EMBALAGEM": tipo_emb.upper(),
                        "QTD_POR_EMBALAGEM": qtd_emb,
                        "QTD_PALETE": qtd_emb,
                        "MARCA": marca.upper() if marca else "SEM MARCA",
                        "LOTE": "",
                        "ENTRADA": 0,
                        "TOTAL": 0,
                        "LOCAL": "",
                        "FABRICACAO": agora.strftime("%d/%m/%Y %H:%M:%S")
                    })
                    salvar_tudo()
                    st.success(f"✅ CARACTERISTICAS ID {id_in.upper()} GUARDADAS - {desc} - {tipo_emb} {qtd_emb}/emb - AGORA VA EM MOV PREENCHER LOTE")
                    st.rerun()

    st.divider()
    st.subheader("CARACTERISTICAS CADASTRADAS - SISTEMA CALCULA A PARTIR DISSO")
    if st.session_state.cad:
        # IDs unicos com caracteristicas
        uniq={}
        for r in st.session_state.cad:
            idp=str(r.get('ID','')).upper()
            if idp and idp not in uniq and str(r.get('TIPO_EMBALAGEM',''))!="":
                uniq[idp]=r
            elif idp and idp not in uniq:
                # tenta achar com tipo
                for rr in st.session_state.cad:
                    if str(rr.get('ID','')).upper()==idp and str(rr.get('TIPO_EMBALAGEM',''))!="":
                        uniq[idp]=rr; break
                if idp not in uniq: uniq[idp]=r
        df_uniq=pd.DataFrame(list(uniq.values()))
        cols=[c for c in ['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','MARCA'] if c in df_uniq.columns]
        st.dataframe(df_uniq[cols].sort_values(by='ID'),use_container_width=True)

# ========== 4 MOV - LOTE + LOCAL - SISTEMA CALCULA ==========
with tab_mov:
    st.header("4 - MOVIMENTAÇÃO - LOTE + ENTRADA/SAIDA + LOCAL - SISTEMA CALCULA AUTOMATICO")
    id_mov=st.text_input("ID* - TEM QUE ESTAR CADASTRADO EM CARACTERISTICAS",key="mov_id")
    desc_m=""; tipo_emb_m="PALETE"; qtd_emb_m=1250.0; marca_m=""; enc_m=False; lotes=[]
    if id_mov:
        up=id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==up and str(r.get('TIPO_EMBALAGEM',''))!="":
                desc_m=r.get('DESCRICAO',''); tipo_emb_m=r.get('TIPO_EMBALAGEM','PALETE'); qtd_emb_m=safe_float(r.get('QTD_POR_EMBALAGEM',r.get('QTD_PALETE',1250)),1250); marca_m=r.get('MARCA',''); enc_m=True; break
        if not enc_m:
            for r in st.session_state.cad:
                if str(r.get('ID','')).upper().strip()==up:
                    desc_m=r.get('DESCRICAO',''); marca_m=r.get('MARCA',''); enc_m=True; break
        saldos,_=get_saldos()
        for v in saldos.values():
            if v['ID']==up and v['SALDO']>0 and v['LOTE'] not in lotes and v['LOTE']!="": lotes.append(v['LOTE'])

    if not id_mov: st.info("DIGITE ID CADASTRADO")
    elif not enc_m: st.error(f"ID {id_mov.upper()} NAO TEM CARACTERISTICAS - CADASTRE EM CARACTERISTICAS PRIMEIRO")
    else:
        st.success(f"ID {id_mov.upper()} - {desc_m} - {tipo_emb_m} com {qtd_emb_m:,.0f} por embalagem - SISTEMA VAI CALCULAR")
        saldo_id=[v for v in get_saldos()[0].values() if v['ID']==id_mov.upper() and v['SALDO']>0]
        if saldo_id: st.dataframe(pd.DataFrame(saldo_id)[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','LOTE','LOCAL','SALDO','EMBALAGENS','ULT_ATUAL','CALCULO']],use_container_width=True)

        with st.form("form_mov_calc"):
            st.text_input("ID",value=id_mov.upper(),disabled=True)
            st.write(f"Característica: **{tipo_emb_m} - {qtd_emb_m:,.0f} por embalagem** - Cálculo automático")
            c1,c2=st.columns(2)
            with c1:
                if lotes: sel=st.selectbox("LOTE* - EXISTENTE OU NOVO",lotes+["NOVO LOTE"]); lote_final=st.text_input("NOVO LOTE*") if sel=="NOVO LOTE" else sel
                else: lote_final=st.text_input("LOTE* - OBRIGATORIO")
            with c2: marca_final=st.text_input("MARCA",value=marca_m)
            c1,c2,c3=st.columns(3)
            with c1: local_final=st.selectbox("LOCAL* - ONDE FICA",LOCAIS)
            with c2: tipo_final=st.selectbox("TIPO* - ENTRADA/SAIDA",["ENTRADA","SAIDA"])
            with c3: qtd_emb_final=st.number_input(f"QTD {tipo_emb_m}* - SISTEMA CALCULA",min_value=0.1,value=1.0,step=1.0)

            total_calc = qtd_emb_final * qtd_emb_m
            st.metric(f"🔢 SISTEMA CALCULA AUTOMATICO: {qtd_emb_final} {tipo_emb_m} x {qtd_emb_m:,.0f} = ", f"{total_calc:,.0f} unidades")

            if st.form_submit_button(f"CONFIRMAR {tipo_final} - GUARDA - CALCULO {total_calc:,.0f}",type="primary",use_container_width=True):
                if not lote_final:
                    st.error("LOTE OBRIGATORIO")
                else:
                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    base={"ID":id_mov.upper(),"LOTE":lote_final.upper().strip(),"MARCA":marca_final.upper() if marca_final else "SEM MARCA","DESCRICAO":desc_m,"PALETES":qtd_emb_final,"TOTAL_QTD":total_calc,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":tipo_emb_m,"QTD_POR_EMBALAGEM":qtd_emb_m}
                    if local_final==LOCAL_GALPAO and tipo_final=="ENTRADA": st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_GALPAO})
                    elif local_final==LOCAL_GALPAO and tipo_final=="SAIDA":
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_GALPAO}); st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                    elif local_final==LOCAL_SALA and tipo_final=="ENTRADA":
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_GALPAO}); st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_SALA})
                    elif local_final==LOCAL_SALA and tipo_final=="SAIDA":
                        st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_SALA}); st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                    else: st.session_state.mov.append({**base,"TIPO":tipo_final,"LOCAL_MOV":local_final})
                    salvar_tudo(); st.success(f"✅ GUARDADO - CALCULO {total_calc:,.0f} - MOV:{len(st.session_state.mov)}"); st.rerun()
    if st.session_state.mov: st.dataframe(df_safe_sort(pd.DataFrame(st.session_state.mov),False).head(20),use_container_width=True)

# ========== 5 ESTOQUE CALCULADO - MOSTRA CARACTERISTICAS + CALCULO + DATA/HORA ==========
with tab_est:
    st.header("5 - ESTOQUE - SISTEMA CALCULOU - MOSTRA CARACTERISTICAS + DATA/HORA ULTIMA ATUALIZACAO")
    saldos,carac = get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista: st.info("Sem estoque")
    else:
        df_est=pd.DataFrame(lista)
        df_est['DATA_HORA_ULTIMA_ATUALIZACAO']=df_est['ULT_ATUAL']
        df_est['AGORA']=agora.strftime("%d/%m/%Y %H:%M:%S")
        df_est['SALDO_FORMATADO']=df_est['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_est['CALCULO_SISTEMA']=df_est['CALCULO']
        st.dataframe(df_est[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','LOTE','MARCA','LOCAL','EMBALAGENS','SALDO','SALDO_FORMATADO','CALCULO_SISTEMA','DATA_HORA_ULTIMA_ATUALIZACAO','AGORA']].sort_values(by='ID'),use_container_width=True,height=600)
        c1,c2,c3=st.columns(3)
        with c1: st.metric("SALDO TOTAL SISTEMA CALCULOU",f"{df_est['SALDO'].sum():,.0f}")
        with c2: st.metric("TOTAL EMBALAGENS",f"{df_est['EMBALAGENS'].sum():,.1f}")
        with c3: st.metric("QTD IDS",f"{df_est['ID'].nunique()}")

with tab_busca:
    st.header("6 - BUSCA ID")
    id_b=st.text_input("ID BUSCA",key="busca_id")
    if id_b:
        saldos,_=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper().strip() and v['SALDO']>0]
        if lista: st.dataframe(pd.DataFrame(lista)[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','LOTE','LOCAL','SALDO','DATA_HORA_ULTIMA_ATUALIZACAO' if 'DATA_HORA_ULTIMA_ATUALIZACAO' in pd.DataFrame(lista).columns else 'ULT_ATUAL']],use_container_width=True)

with tab_grd:
    st.header(f"7 - GRD - VOCE DECIDE HORAS - {st.session_state.tempo_quarentena}H")
    c_h1,c_h2,c_h3=st.columns([2,1,1])
    with c_h1: nova_hora=st.number_input("⏰ VOCE DECIDE HORAS",min_value=1,max_value=720,value=int(st.session_state.tempo_quarentena),step=1,key="input_horas_grd")
    with c_h2:
        if st.button("💾 SALVAR HORAS",type="primary"):
            st.session_state.tempo_quarentena=int(nova_hora); st.success(f"AGORA {nova_hora}H"); st.rerun()
    with c_h3: st.metric("VOCE DECIDIU",f"{st.session_state.tempo_quarentena}H")
    total_sala,pend,disp=get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    saldos,_=get_saldos()
    if not total_sala: total_sala={k:v for k,v in saldos.items() if v['LOCAL']==LOCAL_SALA and v['SALDO']>0}; disp=total_sala.copy()
    df_total=pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    if not df_total.empty: st.dataframe(df_total[['ID','DESCRICAO','TIPO_EMBALAGEM','LOTE','SALDO','ULT_ATUAL']],use_container_width=True)
    ids_disp=sorted(list(set([v['ID'] for v in disp.values()]))) if disp else []
    if ids_disp:
        id_g=st.selectbox("ID",ids_disp,key="id_grd")
        saldo_id=[v for v in disp.values() if v['ID']==id_g]
        lote_sel=st.selectbox("LOTE",sorted(list(set([v['LOTE'] for v in saldo_id]))),key="lote_grd")
        saldo_lote=[v for v in saldo_id if v['LOTE']==lote_sel][0]
        qtd=st.number_input(f"QTD {saldo_lote['TIPO_EMBALAGEM']} MAX {saldo_lote['EMBALAGENS']:.1f}",value=1.0,key="qtd_grd")
        os_g=st.text_input("OS*",key="os_grd")
        if st.button(f"GERAR GRD {st.session_state.tempo_quarentena}H",type="primary"):
            num=f"GRD-{agora.strftime('%Y%m%d%H%M%S')}"; tot=qtd*saldo_lote['QTD_POR_EMBALAGEM']
            st.session_state.grd.append({"NUM_GRD":num,"ID":id_g,"DESCRICAO":saldo_lote['DESCRICAO'],"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"QTD_PALETES":qtd,"TOTAL_QTD":tot,"ORIGEM":LOCAL_SALA,"DESTINO":LOCAL_OFICINA,"OS":os_g,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
            st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"SAIDA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
            st.session_state.mov.append({"ID":id_g,"LOTE":lote_sel,"MARCA":saldo_lote['MARCA'],"DESCRICAO":saldo_lote['DESCRICAO'],"TIPO":"ENTRADA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":agora.strftime("%d/%m/%Y"),"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S")})
            salvar_tudo(); st.success(f"GRD {num} GUARDADO CALCULO {tot:,.0f}"); st.rerun()
    if st.session_state.grd: st.dataframe(df_safe_sort(pd.DataFrame(st.session_state.grd),False),use_container_width=True)

# ========== 8 GRAFICO EMPILHADO POR ID - CADA BARRA UMA COR - DATA/HORA ULTIMA ATUALIZACAO + NUMEROS GRANDES ==========
with tab_graf:
    st.header(f"8 - GRAFICO BARRAS EMPILHADAS - CADA ID UMA COR - SALDO CALCULADO + DATA/HORA ULTIMA ATUALIZACAO - {agora.strftime('%d/%m/%Y %H:%M:%S')}")

    saldos,carac = get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]

    if not lista:
        st.warning("Sem estoque para gráfico - cadastre características e faça movimentação")
    else:
        df_estoque=pd.DataFrame(lista)

        # PEGA ULTIMA DATA/HORA POR ID
        ultimas={}
        for m in st.session_state.mov:
            try:
                idp=str(m.get('ID','')).upper().strip()
                if not idp: continue
                dh=str(m.get('DATA_HORA',m.get('DATA','')))
                dtm=parse_data_hora(dh)
                if idp not in ultimas or dtm>ultimas[idp]['dt']:
                    ultimas[idp]={'dt':dtm,'data_hora':dh,'tipo':m.get('TIPO','')}
            except: continue

        df_estoque['DATA_HORA_ULTIMA_ATUALIZACAO']=df_estoque['ID'].apply(lambda x: ultimas.get(x,{}).get('data_hora', df_estoque[df_estoque['ID']==x]['ULT_ATUAL'].iloc[0] if not df_estoque[df_estoque['ID']==x].empty else 'SEM MOV'))
        df_estoque['ULTIMO_TIPO']=df_estoque['ID'].apply(lambda x: ultimas.get(x,{}).get('tipo',''))

        # GRAFICO 1 - BARRAS EMPILHADAS - CADA ID UMA COR - LOCAL EMPILHADO
        df_emp = df_estoque.groupby(['ID','LOCAL'],as_index=False)['SALDO'].sum()
        df_ult = df_estoque.groupby('ID',as_index=False).agg({'DATA_HORA_ULTIMA_ATUALIZACAO':'first','ULTIMO_TIPO':'first','SALDO':'sum','DESCRICAO':'first','TIPO_EMBALAGEM':'first','QTD_POR_EMBALAGEM':'first'}).rename(columns={'SALDO':'TOTAL_ID'})
        df_emp = df_emp.merge(df_ult,on='ID',how='left')
        df_emp['TEXTO_GRANDE']=df_emp['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_emp=df_emp.sort_values(by='ID')

        # CORES DIFERENTES POR ID
        fig_stack = px.bar(
            df_emp,
            x='ID',
            y='SALDO',
            color='LOCAL',
            text='TEXTO_GRANDE',
            title=f"SALDO TOTAL EMPILHADO POR LOCAL - CADA ID UMA BARRA - {agora.strftime('%d/%m/%Y %H:%M:%S')}<br>DATA/HORA ULTIMA ATUALIZACAO NO HOVER",
            hover_data=['DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','DATA_HORA_ULTIMA_ATUALIZACAO','ULTIMO_TIPO','TOTAL_ID'],
            barmode='stack',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_stack.update_traces(textposition='inside', textfont=dict(size=20, color='white', family='Arial Black'))
        fig_stack.update_layout(height=650, title_font_size=20, xaxis_title="ID DO MATERIAL - CADA BARRA UMA COR DIFERENTE", yaxis_title="SALDO TOTAL CALCULADO PELO SISTEMA", font=dict(size=14))
        st.plotly_chart(fig_stack,use_container_width=True,key=f"stack_{agora.strftime('%H%M%S')}")

        # GRAFICO 2 - BARRAS SIMPLES - CADA ID UMA COR DIFERENTE - NUMEROS GIGANTES + DATA/HORA
        df_total_id = df_estoque.groupby(['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM'],as_index=False).agg({'SALDO':'sum','DATA_HORA_ULTIMA_ATUALIZACAO':'first','ULTIMO_TIPO':'first'})
        df_total_id['TEXTO_NUM']=df_total_id['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_total_id['LABEL_GIGANTE']=df_total_id.apply(lambda r: f"{r['SALDO']:,.0f}<br>{r['DATA_HORA_ULTIMA_ATUALIZACAO']}",axis=1)
        df_total_id=df_total_id.sort_values(by='SALDO',ascending=False)

        fig_total = px.bar(
            df_total_id,
            x='ID',
            y='SALDO',
            text='TEXTO_NUM',
            color='ID',
            title=f"SALDO EM ESTOQUE POR ID - CADA BARRA COR DIFERENTE - NUMEROS GRANDES + DATA/HORA ULTIMA ATUALIZACAO - {agora.strftime('%d/%m/%Y %H:%M:%S')}",
            hover_data=['DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','DATA_HORA_ULTIMA_ATUALIZACAO','ULTIMO_TIPO'],
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig_total.update_traces(textposition='outside', textfont=dict(size=20, color='black', family='Arial Black'), cliponaxis=False)
        fig_total.update_layout(height=700, title_font_size=22, xaxis_title="ID - CADA COR UMA ID DIFERENTE", yaxis_title="SALDO TOTAL QUE O SISTEMA CALCULOU", showlegend=True)
        st.plotly_chart(fig_total,use_container_width=True,key=f"total_{agora.strftime('%H%M%S')}")

        # TABELA COM CALCULO + DATA/HORA ULTIMA ATUALIZACAO - NUMEROS GRANDES
        st.subheader("📊 TABELA - SALDO CALCULADO + DATA/HORA ULTIMA ATUALIZACAO - NUMEROS GRANDES")
        df_total_id['AGORA']=agora.strftime("%d/%m/%Y %H:%M:%S")
        df_total_id['CALCULO_SISTEMA']=df_total_id.apply(lambda r: f"{r['TIPO_EMBALAGEM']} x {r['QTD_POR_EMBALAGEM']:,.0f} = {r['SALDO']:,.0f}",axis=1)
        df_total_id['SALDO_FORMATADO']=df_total_id['SALDO'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_total_id[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','SALDO','SALDO_FORMATADO','CALCULO_SISTEMA','DATA_HORA_ULTIMA_ATUALIZACAO','ULTIMO_TIPO','AGORA']].sort_values(by='SALDO',ascending=False),use_container_width=True,height=500)

        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric("🔢 SALDO TOTAL SISTEMA CALCULOU",f"{df_estoque['SALDO'].sum():,.0f}")
        with c2:
            if ultimas:
                ultima_geral=max([v['dt'] for v in ultimas.values()])
                st.metric("🕐 ULTIMA ATUALIZACAO GERAL",ultima_geral.strftime("%d/%m/%Y %H:%M:%S"))
        with c3: st.metric("📦 QTD IDS - CADA COR",f"{df_estoque['ID'].nunique()}")
        with c4: st.metric("⏰ VOCE DECIDIU",f"{st.session_state.tempo_quarentena}H")

with tab_hist:
    st.header("9 - HISTORICO")
    if not st.session_state.mov: st.warning("Sem mov")
    else: st.dataframe(df_safe_sort(pd.DataFrame(st.session_state.mov),False),use_container_width=True,height=500)

st.caption(f"REFORMA FORNOS - CARACTERISTICAS ID DESCRICAO TIPO_EMBALAGEM QTD_POR_EMBALAGEM - SISTEMA CALCULA - ESTOQUE + GRAFICO BARRAS EMPILHADAS CADA ID COR DIFERENTE + DATA/HORA ULTIMA ATUALIZACAO - {agora.strftime('%d/%m/%Y %H:%M:%S')} - CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
