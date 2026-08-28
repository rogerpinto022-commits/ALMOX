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

def safe_float(v, d=0.0):
    try:
        return float(str(v).replace(",","."))
    except:
        return float(d)

def carregar(caminho):
    if not os.path.exists(caminho):
        return []
    try:
        df = pd.read_csv(caminho).fillna("")
        df.columns = [str(c).upper() for c in df.columns]
        return df.to_dict('records')
    except:
        return []

if 'cad' not in st.session_state:
    st.session_state.cad = carregar(ARQ_CAD)
if 'mov' not in st.session_state:
    st.session_state.mov = carregar(ARQ_MOV)
if 'grd' not in st.session_state:
    st.session_state.grd = carregar(ARQ_GRD)

if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)

if 'logado' not in st.session_state:
    st.session_state.logado=False
if 'usuario' not in st.session_state:
    st.session_state.usuario=None

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
        else:
            st.error("Invalido")
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

def get_saldos():
    saldos={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper().strip()
        lote=str(r.get('LOTE','')).upper().strip()
        if not idp or not lote:
            continue
        local=str(r.get('LOCAL',LOCAL_GALPAO)).upper()
        if "SALA" in local: local=LOCAL_SALA
        elif "OFIC" in local: local=LOCAL_OFICINA
        else: local=LOCAL_GALPAO
        marca=str(r.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{local}__{marca}__{lote}"
        q=safe_float(r.get('TOTAL',0))
        if q==0: q=safe_float(r.get('QTD_PALETE',0))*safe_float(r.get('ENTRADA',0))
        if chave not in saldos:
            saldos[chave]={'ID':idp,'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':q,'PAL':safe_float(r.get('ENTRADA',0))}
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
            saldos[chave]={'ID':idp,'DESCRICAO':str(m.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':0,'PAL':0}
        if chave not in saldos: continue
        if m.get('TIPO')=="ENTRADA":
            saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0))
            saldos[chave]['PAL']+=safe_float(m.get('PALETES',0))
        else:
            saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0))
            saldos[chave]['PAL']-=safe_float(m.get('PALETES',0))
    return saldos

def excluir_estoque(idp, local, marca, lote):
    st.session_state.cad=[r for r in st.session_state.cad if not (str(r.get('ID','')).upper()==idp.upper() and str(r.get('LOTE','')).upper()==lote.upper() and str(r.get('MARCA','')).upper()==marca.upper() and str(r.get('LOCAL','')).upper()==local.upper())]
    st.session_state.mov=[m for m in st.session_state.mov if not (str(m.get('ID','')).upper()==idp.upper() and str(m.get('LOTE','')).upper()==lote.upper() and str(m.get('MARCA','')).upper()==marca.upper() and str(m.get('LOCAL_MOV','')).upper()==local.upper())]
    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M')}")

# TABS FIXOS - SEMPRE 9 - NUNCA QUEBRA
tabs = st.tabs(["ADMIN","DASHBOARD","CADASTRO","MOVIMENTACAO","ESTOQUE","BUSCA ID","GRD","GRAFICOS","HISTORICO"])
tab_admin = tabs[0]
tab_dash = tabs[1]
tab_cad = tabs[2]
tab_mov = tabs[3]
tab_est = tabs[4]
tab_busca = tabs[5]
tab_grd = tabs[6]
tab_graf = tabs[7]
tab_hist = tabs[8]

with tab_admin:
    st.header("1 - ADMINISTRACAO")
    if not is_admin:
        st.warning("Apenas admin@admin.com acessa aqui")
    else:
        with st.form("form_user_admin"):
            email_new=st.text_input("Email novo")
            nome_new=st.text_input("Nome")
            senha_new=st.text_input("Senha")
            local_new=st.selectbox("Local acesso", LOCAIS_ACESSO)
            status_new=st.selectbox("Status", ["LIBERADO","BLOQUEADO"])
            if st.form_submit_button("SALVAR USUARIO", type="primary"):
                if email_new and senha_new:
                    df=pd.read_csv(ARQ_EMAILS)
                    df=df[df['EMAIL'].astype(str).str.lower()!=email_new.lower()]
                    novo=pd.DataFrame([{"EMAIL":email_new.lower(),"SENHA":senha_new,"LOCAL":local_new,"STATUS":status_new,"NOME":nome_new.upper()}])
                    df=pd.concat([df,novo], ignore_index=True)
                    df.to_csv(ARQ_EMAILS,index=False)
                    st.success("Usuario salvo")
                    st.rerun()
        st.dataframe(pd.read_csv(ARQ_EMAILS), use_container_width=True)

with tab_dash:
    st.header("2 - DASHBOARD")
    saldos=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista) if lista else pd.DataFrame()
    if df.empty:
        st.warning("Sem estoque - cadastre na aba CADASTRO")
    else:
        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric("GERAL", f"{df['SALDO'].sum():,.0f}")
        with c2: st.metric("GALPAO", f"{df[df['LOCAL']==LOCAL_GALPAO]['SALDO'].sum():,.0f}")
        with c3: st.metric("SALA", f"{df[df['LOCAL']==LOCAL_SALA]['SALDO'].sum():,.0f}")
        with c4: st.metric("OFICINA", f"{df[df['LOCAL']==LOCAL_OFICINA]['SALDO'].sum():,.0f}")
        df_g=df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        df_g['TEXTO']=df_g['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_g, x='LOCAL', y='SALDO', text='TEXTO', color='LOCAL', title="ESTOQUE POR LOCAL")
        fig.update_traces(textposition='inside', textfont=dict(size=30, color='white', family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

with tab_cad:
    st.header("3 - CADASTRO - AUTO PREENCHIMENTO ID")
    id_in = st.text_input("DIGITE ID* - AUTO PREENCHE SE EXISTIR", key="id_cad_auto")
    desc_auto = ""
    marca_auto = ""
    qtd_auto = 1250.0
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip() == id_in.upper().strip():
                desc_auto = r.get('DESCRICAO','')
                marca_auto = r.get('MARCA','')
                qtd_auto = safe_float(r.get('QTD_PALETE',1250.0), 1250.0)
                st.success(f"ID {id_in.upper()} ENCONTRADO: {desc_auto} | {marca_auto}")
                break
        else:
            if id_in: st.info(f"ID {id_in.upper()} NOVO")
    with st.form("form_cadastro_mat"):
        st.text_input("ID CONFIRMADO", value=id_in.upper() if id_in else "", disabled=True)
        desc_in=st.text_input("DESCRICAO* AUTO", value=desc_auto, key="desc_cad")
        marca_in=st.text_input("MARCA* AUTO", value=marca_auto, key="marca_cad")
        lote_in=st.text_input("LOTE OPCIONAL", key="lote_cad")
        locais_sel=st.multiselect("LOCAIS PARA CADASTRAR* (VARIOS)", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad")
        qtd_in=st.number_input("QTD POR PALETE AUTO", value=qtd_auto, key="qtd_cad")
        ent_in=st.number_input("PALETES POR LOCAL - 0=SO CADASTRO", value=0.0, key="ent_cad")
        if st.form_submit_button("CADASTRAR NOS LOCAIS", type="primary"):
            if not id_in or not desc_in or not marca_in:
                st.error("Preencha ID, DESCRICAO e MARCA")
            elif not locais_sel:
                st.error("Selecione 1 LOCAL")
            else:
                for local_cad in locais_sel:
                    total=qtd_in*ent_in
                    st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.success(f"Cadastrado em {len(locais_sel)} locais")
                st.rerun()
    for i,r in enumerate(st.session_state.cad):
        c1,c2=st.columns([4,1])
        with c1: st.write(f"{r.get('LOCAL')} | ID {r.get('ID')} - {r.get('DESCRICAO')} - {r.get('MARCA')} - LOTE {r.get('LOTE')}")
        with c2:
            if st.button("Excluir", key=f"del_cad_{i}"):
                st.session_state.cad.pop(i)
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.rerun()

with tab_mov:
    st.header("4 - MOVIMENTACAO - AUTO PREENCHE ID")
    ids_raw = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
    ids = sorted(list(set(ids_raw)))
    if not ids:
        st.warning("Cadastre na aba CADASTRO")
    else:
        id_sel=st.selectbox("ID* AUTO", options=ids, key="id_mov")
        cat=None
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==id_sel: cat=r; break
        desc=cat.get('DESCRICAO','') if cat else ""
        marca_cat=cat.get('MARCA','') if cat else ""
        qtd_cat=safe_float(cat.get('QTD_PALETE',1250)) if cat else 1250
        st.text_input("Descricao Auto", value=desc, disabled=True, key="desc_mov")
        st.text_input("Marca Auto", value=marca_cat, disabled=True, key="marca_cat_mov")
        lote=st.text_input("LOTE* OBRIGATORIO", key="lote_mov")
        marca=st.text_input("MARCA* AUTO EDITAVEL", value=marca_cat, key="marca_mov")
        local_sel=st.selectbox("LOCAL*", LOCAIS, key="local_mov")
        tipo=st.selectbox("TIPO*", ["ENTRADA","SAIDA"], key="tipo_mov")
        pal=st.number_input("PALETES*", value=1.0, min_value=0.1, key="pal_mov")
        if lote:
            tot=pal*qtd_cat
            if local_sel==LOCAL_GALPAO and tipo=="ENTRADA": st.success(f"ENTRADA GALPAO +{tot:,.0f}")
            elif local_sel==LOCAL_GALPAO and tipo=="SAIDA": st.warning(f"SAIDA GALPAO -{tot:,.0f} + OFICINA +{tot:,.0f} AUTO")
            elif local_sel==LOCAL_SALA and tipo=="ENTRADA": st.info(f"ENTRADA SALA: GALPAO -{tot:,.0f} + SALA +{tot:,.0f} AUTO")
            elif local_sel==LOCAL_SALA and tipo=="SAIDA": st.warning(f"SAIDA SALA -{tot:,.0f} + OFICINA +{tot:,.0f} AUTO")
            elif local_sel==LOCAL_OFICINA and tipo=="ENTRADA": st.success(f"ENTRADA OFICINA +{tot:,.0f}")
            else: st.error(f"SAIDA OFICINA -{tot:,.0f} CONSUMO")
        if st.button("CONFIRMAR FLUXO AUTOMATICO", type="primary", use_container_width=True, key="btn_mov"):
            if not lote: st.error("LOTE obrigatorio")
            else:
                hoje=date.today().strftime("%d/%m/%Y")
                tot=pal*qtd_cat
                if local_sel==LOCAL_GALPAO and tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":hoje})
                elif local_sel==LOCAL_GALPAO and tipo=="SAIDA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":hoje})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":hoje})
                elif local_sel==LOCAL_SALA and tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_GALPAO,"DATA":hoje})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":hoje})
                elif local_sel==LOCAL_SALA and tipo=="SAIDA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_SALA,"DATA":hoje})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":hoje})
                elif local_sel==LOCAL_OFICINA and tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":hoje})
                else:
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":LOCAL_OFICINA,"DATA":hoje})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success("OK")
                st.rerun()
    if st.session_state.mov:
        st.dataframe(pd.DataFrame(st.session_state.mov).tail(20), use_container_width=True)

with tab_est:
    st.header("5 - ESTOQUE COM EXCLUIR")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'LOCAL':v['LOCAL'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in saldos.values() if v['SALDO']>0]
    if not lista:
        st.info("Sem estoque")
    else:
        df=pd.DataFrame(lista)
        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric("GERAL", f"{df['SALDO'].sum():,.0f}")
        with c2: st.metric("GALPAO", f"{df[df['LOCAL']==LOCAL_GALPAO]['SALDO'].sum():,.0f}")
        with c3: st.metric("SALA", f"{df[df['LOCAL']==LOCAL_SALA]['SALDO'].sum():,.0f}")
        with c4: st.metric("OFICINA", f"{df[df['LOCAL']==LOCAL_OFICINA]['SALDO'].sum():,.0f}")
        for idx, v in enumerate(sorted(lista, key=lambda x: (x['LOCAL'], x['ID']))):
            c1,c2,c3,c4,c5,c6,c7=st.columns([1,2,1,1,1,1,1])
            with c1: st.write(v['ID'])
            with c2: st.write(v['DESCRICAO'][:20])
            with c3: st.write(v['LOTE'])
            with c4: st.write(v['LOCAL'][:8])
            with c5: st.write(f"{v['SALDO']:,.0f}")
            with c6: st.write(f"{v['PAL']:.1f}")
            with c7:
                if st.button("Excluir", key=f"del_est_{idx}_{v['ID']}_{v['LOTE']}_{v['LOCAL']}"):
                    excluir_estoque(v['ID'], v['LOCAL'], v['MARCA'], v['LOTE'])
                    st.rerun()

with tab_busca:
    st.header("6 - BUSCA ID")
    id_b=st.text_input("ID BUSCA", key="id_busca")
    if id_b:
        saldos=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper() and v['SALDO']>0]
        if lista:
            df=pd.DataFrame([{'LOCAL':v['LOCAL'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'SALDO':v['SALDO']} for v in lista])
            df['TEXTO']=df['SALDO'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df, use_container_width=True)
            fig=px.bar(df, x='LOCAL', y='SALDO', text='TEXTO', color='LOCAL', title=f"ID {id_b}")
            fig.update_traces(textposition='inside', textfont=dict(size=28, color='white', family='Arial Black'))
            st.plotly_chart(fig, use_container_width=True)

with tab_grd:
    st.header("7 - GRD")
    ids_raw2 = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
    ids2 = sorted(list(set(ids_raw2)))
    if ids2:
        id_g=st.selectbox("ID GRD AUTO", options=ids2, key="id_grd")
        cat=None
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==id_g: cat=r; break
        desc=cat.get('DESCRICAO','') if cat else ""
        st.text_input("Descricao Auto", value=desc, disabled=True, key="desc_grd")
        lote=st.text_input("LOTE GRD*", key="lote_grd")
        marca=st.text_input("MARCA GRD*", value=cat.get('MARCA','') if cat else "", key="marca_grd")
        qtd=st.number_input("PALETES GRD*", value=1.0, key="qtd_grd")
        ori=st.selectbox("ORIGEM*", LOCAIS, key="ori_grd")
        dst=st.selectbox("DESTINO*", [l for l in LOCAIS if l!=ori], key="dst_grd")
        os_g=st.text_input("OS/FORNO*", key="os_grd")
        if st.button("GERAR GRD", type="primary", key="btn_grd"):
            if not lote: st.error("LOTE obrigatorio")
            else:
                qb=safe_float(cat.get('QTD_PALETE',1250)) if cat else 1250
                tot=qtd*qb
                num=f"GRD-{datetime.now(fuso).strftime('%Y%m%d%H%M%S')}"
                st.session_state.grd.append({"NUM_GRD":num,"ID":id_g,"DESCRICAO":desc,"LOTE":lote.upper(),"MARCA":marca.upper(),"QTD_PALETES":qtd,"TOTAL_QTD":tot,"ORIGEM":ori,"DESTINO":dst,"OS":os_g,"DATA":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False)
                st.session_state.mov.append({"ID":id_g,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":ori,"DATA":date.today().strftime("%d/%m/%Y")})
                st.session_state.mov.append({"ID":id_g,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":qtd,"TOTAL_QTD":tot,"LOCAL_MOV":dst,"DATA":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success(f"GRD {num}")
                st.rerun()
    if st.session_state.grd:
        st.dataframe(pd.DataFrame(st.session_state.grd), use_container_width=True)

with tab_graf:
    st.header("8 - GRAFICOS")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOCAL':v['LOCAL'],'MARCA':v['MARCA'],'LOTE':v['LOTE'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if df.empty:
        st.info("Sem estoque")
    else:
        df_local=df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        df_local['TEXTO']=df_local['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_local, x='LOCAL', y='SALDO', text='TEXTO', color='LOCAL', title="POR LOCAL")
        fig.update_traces(textposition='inside', textfont=dict(size=32, color='white', family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    st.header("9 - HISTORICO")
    if not st.session_state.mov:
        st.warning("Sem movimentacoes")
    else:
        df_mov=pd.DataFrame(st.session_state.mov)
        def parse_data(d):
            try: return dt.strptime(str(d), "%d/%m/%Y")
            except: return dt.now()
        df_mov['DATA_DT']=df_mov['DATA'].apply(parse_data)
        df_mov['QTD']=df_mov['TOTAL_QTD'].apply(lambda x: safe_float(x))
        df_g=df_mov.groupby('DATA', as_index=False)['QTD'].sum()
        df_g['TEXTO']=df_g['QTD'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_g, x='DATA', y='QTD', text='TEXTO', title="HISTORICO POR DIA")
        fig.update_traces(textposition='inside', textfont=dict(size=20, color='white', family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_mov.sort_values(by='DATA_DT', ascending=False), use_container_width=True)

st.caption(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M')}")
