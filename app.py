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
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA DE FORNOS - CONTROLE DE REFRATARIOS</h1>", unsafe_allow_html=True)
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
auto = st.sidebar.toggle("AUTO 10s TV", value=True)
if auto:
    components.html("<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>", height=0)

def get_saldos():
    saldos={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper().strip()
        lote=str(r.get('LOTE','')).upper().strip()
        if not idp or not lote:
            continue
        local=str(r.get('LOCAL',LOCAL_GALPAO)).upper()
        if "SALA" in local:
            local=LOCAL_SALA
        elif "OFIC" in local:
            local=LOCAL_OFICINA
        else:
            local=LOCAL_GALPAO
        marca=str(r.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{local}__{marca}__{lote}"
        q=safe_float(r.get('TOTAL',0))
        if q==0:
            q=safe_float(r.get('QTD_PALETE',0))*safe_float(r.get('ENTRADA',0))
        if chave not in saldos:
            saldos[chave]={'ID':idp,'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':q,'PAL':safe_float(r.get('ENTRADA',0))}
        else:
            saldos[chave]['SALDO']+=q
            saldos[chave]['PAL']+=safe_float(r.get('ENTRADA',0))
    for m in st.session_state.mov:
        idp=str(m.get('ID','')).upper().strip()
        lote=str(m.get('LOTE','')).upper().strip()
        if not idp or not lote:
            continue
        local=str(m.get('LOCAL_MOV',LOCAL_GALPAO)).upper()
        if "SALA" in local:
            local=LOCAL_SALA
        elif "OFIC" in local:
            local=LOCAL_OFICINA
        else:
            local=LOCAL_GALPAO
        marca=str(m.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{local}__{marca}__{lote}"
        if chave not in saldos and m.get('TIPO')=="ENTRADA":
            saldos[chave]={'ID':idp,'DESCRICAO':str(m.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':0,'PAL':0}
        if chave not in saldos:
            continue
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

if is_admin:
    tab_names = ["ADMIN","DASHBOARD","CADASTRO","MOVIMENTACAO","ESTOQUE","BUSCA ID","GRD","GRAFICOS","HISTORICO"]
    tabs = st.tabs(tab_names)
    tab_admin = tabs[0]
    tab_dash = tabs[1]
    tab_cad = tabs[2]
    tab_mov = tabs[3]
    tab_est = tabs[4]
    tab_busca = tabs[5]
    tab_grd = tabs[6]
    tab_graf = tabs[7]
    tab_hist = tabs[8]
else:
    tab_names = ["DASHBOARD","CADASTRO","MOVIMENTACAO","ESTOQUE","BUSCA ID","GRD","GRAFICOS","HISTORICO"]
    tabs = st.tabs(tab_names)
    tab_admin = None
    tab_dash = tabs[0]
    tab_cad = tabs[1]
    tab_mov = tabs[2]
    tab_est = tabs[3]
    tab_busca = tabs[4]
    tab_grd = tabs[5]
    tab_graf = tabs[6]
    tab_hist = tabs[7]

if tab_admin is not None:
    with tab_admin:
        st.header("1 - ADMINISTRACAO")
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
        total=df['SALDO'].sum()
        galpao=df[df['LOCAL']==LOCAL_GALPAO]['SALDO'].sum()
        sala=df[df['LOCAL']==LOCAL_SALA]['SALDO'].sum()
        oficina=df[df['LOCAL']==LOCAL_OFICINA]['SALDO'].sum()
        with c1: st.metric("GERAL", f"{total:,.0f}")
        with c2: st.metric("GALPAO", f"{galpao:,.0f}")
        with c3: st.metric("SALA ANEXA", f"{sala:,.0f}")
        with c4: st.metric("OFICINA", f"{oficina:,.0f}")
        df_g=df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        df_g['TEXTO']=df_g['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_g, x='LOCAL', y='SALDO', text='TEXTO', color='LOCAL', title="ESTOQUE POR LOCAL - NUMEROS GRANDES DENTRO")
        fig.update_traces(textposition='inside', textfont=dict(size=30, color='white', family='Arial Black'))
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

with tab_cad:
    st.header("3 - CADASTRO DE MATERIAIS - SELECIONE LOCAIS")
    id_busca=st.text_input("DIGITE ID PARA RECONHECER MATERIAL", key="id_busca_cad")
    desc_d=""; marca_d=""
    for r in st.session_state.cad:
        if str(r.get('ID','')).upper()==id_busca.upper():
            desc_d=r.get('DESCRICAO',''); marca_d=r.get('MARCA',''); break
    with st.form("form_cadastro_mat"):
        id_in=st.text_input("ID DO MATERIAL*", value=id_busca.upper() if id_busca else "", key="id_cad")
        desc_in=st.text_input("DESCRICAO DO REFRATARIO* EX: TIJOLO ISOLANTE 230x114", value=desc_d, key="desc_cad")
        marca_in=st.text_input("MARCA / FABRICANTE*", value=marca_d, key="marca_cad")
        lote_in=st.text_input("LOTE INICIAL OPCIONAL", key="lote_cad")
        locais_sel=st.multiselect("SELECIONE EM QUAIS LOCAIS CADASTRAR* (PODE MARCAR VARIOS)", LOCAIS, default=[LOCAL_GALPAO], key="locais_cad")
        qtd_in=st.number_input("QTD UNIDADES POR PALETE", value=1250.0, key="qtd_cad")
        ent_in=st.number_input("PALETES POR LOCAL - 0=SO CADASTRO", value=0.0, key="ent_cad")
        if st.form_submit_button("CADASTRAR NOS LOCAIS SELECIONADOS", type="primary"):
            if not id_in or not desc_in or not marca_in:
                st.error("Preencha ID, DESCRICAO e MARCA")
            elif not locais_sel:
                st.error("Selecione pelo menos 1 LOCAL")
            else:
                for local_cad in locais_sel:
                    total=qtd_in*ent_in
                    st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_cad,"FABRICACAO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.success(f"Material {id_in} cadastrado em {len(locais_sel)} local(is)")
                st.rerun()
    st.divider()
    for i,r in enumerate(st.session_state.cad):
        if id_busca and id_busca.upper() not in str(r.get('ID','')).upper(): continue
        c1,c2=st.columns([4,1])
        with c1: st.write(f"LOCAL: {r.get('LOCAL')} | ID {r.get('ID')} - {r.get('DESCRICAO')} - {r.get('MARCA')} - LOTE {r.get('LOTE')}")
        with c2:
            if st.button("Excluir", key=f"del_cad_{i}"):
                st.session_state.cad.pop(i)
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.rerun()

with tab_mov:
    st.header("4 - MOVIMENTACAO COM FLUXO AUTOMATICO")
    st.info("FLUXO: ENTRADA GALPAO=SOMA GERAL | SAIDA GALPAO=OFICINA AUTO | ENTRADA SALA=DESCONTA GALPAO AUTO | SAIDA SALA=OFICINA AUTO | SAIDA OFICINA=CONSUMO FINAL")
    # CORRECAO DO ERRO AQUI
    ids_raw = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
    ids = sorted(list(set(ids_raw)))
    if not ids:
        st.warning("Cadastre material primeiro na aba CADASTRO")
    else:
        id_sel=st.selectbox("ID DO MATERIAL*", options=ids, key="id_mov")
        cat=None
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==id_sel: cat=r; break
        desc=cat.get('DESCRICAO','') if cat else ""
        st.text_input("Descricao", value=desc, disabled=True, key="desc_mov")
        lote=st.text_input("LOTE* OBRIGATORIO NASCE AQUI", key="lote_mov")
        marca=st.text_input("MARCA*", value=cat.get('MARCA','') if cat else "", key="marca_mov")
        local_sel=st.selectbox("LOCAL MOVIMENTACAO*", LOCAIS, key="local_mov")
        tipo=st.selectbox("TIPO*", ["ENTRADA","SAIDA"], key="tipo_mov")
        pal=st.number_input("QTD PALETES*", value=1.0, min_value=0.1, key="pal_mov")
        if lote:
            qb=safe_float(cat.get('QTD_PALETE',1250)) if cat else 1250
            tot=pal*qb
            if local_sel==LOCAL_GALPAO and tipo=="ENTRADA": st.success(f"ENTRADA GALPAO +{tot:,.0f} GERAL")
            elif local_sel==LOCAL_GALPAO and tipo=="SAIDA": st.warning(f"SAIDA GALPAO -{tot:,.0f} + OFICINA +{tot:,.0f} AUTO")
            elif local_sel==LOCAL_SALA and tipo=="ENTRADA": st.info(f"ENTRADA SALA: GALPAO -{tot:,.0f} + SALA +{tot:,.0f} AUTO")
            elif local_sel==LOCAL_SALA and tipo=="SAIDA": st.warning(f"SAIDA SALA -{tot:,.0f} + OFICINA +{tot:,.0f} AUTO")
            elif local_sel==LOCAL_OFICINA and tipo=="ENTRADA": st.success(f"ENTRADA OFICINA +{tot:,.0f}")
            else: st.error(f"SAIDA OFICINA -{tot:,.0f} CONSUMO FINAL")
        if st.button("CONFIRMAR FLUXO AUTOMATICO", type="primary", use_container_width=True, key="btn_mov"):
            if not lote: st.error("LOTE obrigatorio")
            else:
                qb=safe_float(cat.get('QTD_PALETE',1250)) if cat else 1250
                tot=pal*qb
                hoje=date.today().strftime("%d/%m/%Y")
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
                st.success("Movimentado com fluxo automatico")
                st.rerun()
    if st.session_state.mov:
        st.divider()
        st.dataframe(pd.DataFrame(st.session_state.mov).tail(20), use_container_width=True)

with tab_est:
    st.header("5 - ESTOQUE COM BOTAO EXCLUIR")
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
        filtro=st.text_input("FILTRAR ID DESCRICAO LOTE", key="filtro_est")
        if filtro: lista=[x for x in lista if filtro.upper() in x['ID'] or filtro.upper() in x['DESCRICAO'] or filtro.upper() in x['LOTE']]
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
        st.dataframe(pd.DataFrame(lista), use_container_width=True)

with tab_busca:
    st.header("6 - BUSCA POR ID")
    id_b=st.text_input("DIGITE ID PARA BUSCAR", key="id_busca")
    if id_b:
        saldos=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper() and v['SALDO']>0]
        if lista:
            df=pd.DataFrame([{'LOCAL':v['LOCAL'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in lista])
            df['TEXTO']=df['SALDO'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df, use_container_width=True)
            fig=px.bar(df, x='LOCAL', y='SALDO', text='TEXTO', color='LOCAL', title=f"ESTOQUE ID {id_b} - NUMEROS GRANDES DENTRO")
            fig.update_traces(textposition='inside', textfont=dict(size=28, color='white', family='Arial Black'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"ID {id_b} sem saldo")

with tab_grd:
    st.header("7 - GRD GUIA REMESSA")
    ids_raw2 = [str(r.get('ID','')).strip().upper() for r in st.session_state.cad if str(r.get('ID','')).strip()!='']
    ids2 = sorted(list(set(ids_raw2)))
    if ids2:
        id_g=st.selectbox("ID PARA GRD", options=ids2, key="id_grd")
        cat=None
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==id_g: cat=r; break
        desc=cat.get('DESCRICAO','') if cat else ""
        st.text_input("Descricao", value=desc, disabled=True, key="desc_grd")
        lote=st.text_input("LOTE GRD*", key="lote_grd")
        marca=st.text_input("MARCA GRD*", value=cat.get('MARCA','') if cat else "", key="marca_grd")
        qtd=st.number_input("QTD PALETES GRD*", value=1.0, key="qtd_grd")
        ori=st.selectbox("ORIGEM GRD*", LOCAIS, key="ori_grd")
        dst=st.selectbox("DESTINO GRD*", [l for l in LOCAIS if l!=ori], key="dst_grd")
        os_g=st.text_input("OS / FORNO DESTINO*", key="os_grd")
        if st.button("GERAR GRD COM FLUXO", type="primary", key="btn_grd"):
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
                st.success(f"GRD {num} gerada")
                st.rerun()
    if st.session_state.grd:
        st.dataframe(pd.DataFrame(st.session_state.grd), use_container_width=True)

with tab_graf:
    st.header("8 - GRAFICOS DETALHADOS - NUMEROS GRANDES DENTRO")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOCAL':v['LOCAL'],'MARCA':v['MARCA'],'LOTE':v['LOTE'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if df.empty:
        st.info("Sem estoque para graficos")
    else:
        df_local=df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        df_local['TEXTO']=df_local['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_local, x='LOCAL', y='SALDO', text='TEXTO', color='LOCAL', title="POR LOCAL FISICO - QTD REAL - NUMEROS GIGANTES DENTRO")
        fig.update_traces(textposition='inside', textfont=dict(size=32, color='white', family='Arial Black'))
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

        df_top=df.groupby(['ID','DESCRICAO'], as_index=False)['SALDO'].sum().sort_values(by='SALDO', ascending=False).head(15)
        df_top['LABEL']=df_top['ID']+" - "+df_top['DESCRICAO'].str[:20]
        df_top['TEXTO']=df_top['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig2=px.bar(df_top, x='LABEL', y='SALDO', text='TEXTO', color='SALDO', title="TOP 15 MATERIAIS - ID + DESCRICAO REAL - NUMEROS GRANDES")
        fig2.update_traces(textposition='inside', textfont=dict(size=14, color='white', family='Arial Black'))
        fig2.update_layout(height=600, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

        df_marca=df.groupby('MARCA', as_index=False)['SALDO'].sum().sort_values(by='SALDO', ascending=False).head(10)
        df_marca['TEXTO']=df_marca['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig3=px.bar(df_marca, x='MARCA', y='SALDO', text='TEXTO', color='MARCA', title="POR MARCA FABRICANTE - NUMEROS GRANDES DENTRO")
        fig3.update_traces(textposition='inside', textfont=dict(size=20, color='white', family='Arial Black'))
        st.plotly_chart(fig3, use_container_width=True)

with tab_hist:
    st.header("9 - HISTORICO DIA / SEMANA / MES / ANO")
    if not st.session_state.mov:
        st.warning("Sem movimentacoes")
    else:
        df_mov=pd.DataFrame(st.session_state.mov)
        def parse_data(d):
            try: return dt.strptime(str(d), "%d/%m/%Y")
            except: return dt.now()
        df_mov['DATA_DT']=df_mov['DATA'].apply(parse_data)
        df_mov['DIA']=df_mov['DATA_DT'].dt.strftime("%d/%m/%Y")
        df_mov['SEMANA']=df_mov['DATA_DT'].dt.strftime("%Y-W%W")
        df_mov['MES']=df_mov['DATA_DT'].dt.strftime("%m/%Y")
        df_mov['ANO']=df_mov['DATA_DT'].dt.strftime("%Y")
        df_mov['QTD']=df_mov['TOTAL_QTD'].apply(lambda x: safe_float(x))
        c1,c2=st.columns(2)
        with c1: tipo_hist=st.selectbox("VISUALIZAR POR", ["DIA","SEMANA","MES","ANO"], key="tipo_hist_final")
        with c2: filtro_tipo=st.selectbox("TIPO MOVIMENTACAO", ["TODOS","ENTRADA","SAIDA"], key="filtro_tipo_final")
        df_f=df_mov.copy()
        if filtro_tipo!="TODOS": df_f=df_f[df_f['TIPO']==filtro_tipo]
        if tipo_hist=="DIA": df_g=df_f.groupby('DIA', as_index=False)['QTD'].sum()
        elif tipo_hist=="SEMANA": df_g=df_f.groupby('SEMANA', as_index=False)['QTD'].sum()
        elif tipo_hist=="MES": df_g=df_f.groupby('MES', as_index=False)['QTD'].sum()
        else: df_g=df_f.groupby('ANO', as_index=False)['QTD'].sum()
        df_g['TEXTO']=df_g['QTD'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_g, x=df_g.columns[0], y='QTD', text='TEXTO', title=f"HISTORICO POR {tipo_hist} - {filtro_tipo} - NUMEROS GRANDES", color='QTD')
        fig.update_traces(textposition='inside', textfont=dict(size=24, color='white', family='Arial Black'))
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_g, use_container_width=True)
        st.dataframe(df_mov.sort_values(by='DATA_DT', ascending=False), use_container_width=True, height=300)

st.caption(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M')}")
