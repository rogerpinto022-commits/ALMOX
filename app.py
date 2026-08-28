import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
import plotly.express as px
import urllib.parse

st.set_page_config(page_title="REFORMA FORNOS V12 OK", layout="wide")
fuso = timezone(timedelta(hours=-3))

ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_GRD = "grd.csv"
ARQ_EMAILS = "emails.csv"

LOCAL_GALPAO = "GALPÃO DE MATERIAIS REFRATARIOS"
LOCAL_SALA = "SALA ANEXA"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"
LOCAIS = [LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]

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
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO"}]).to_csv(ARQ_EMAILS,index=False)

if 'logado' not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.title("Login Reforma Fornos")
    e = st.text_input("Email", key="login_email_v12")
    s = st.text_input("Senha", type="password", key="login_senha_v12")
    if st.button("Entrar", key="btn_entrar_v12"):
        df_e = pd.read_csv(ARQ_EMAILS)
        u = df_e[(df_e["EMAIL"]==e.lower()) & (df_e["SENHA"]==s)]
        if not u.empty:
            st.session_state.logado=True
            st.rerun()
        else: st.error("Invalido")
    st.stop()

def get_saldos():
    saldos={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper()
        lote=str(r.get('LOTE','')).upper()
        if not idp or not lote: continue
        local=r.get('LOCAL',LOCAL_GALPAO)
        if "SALA" in local: local=LOCAL_SALA
        elif "OFIC" in local: local=LOCAL_OFICINA
        else: local=LOCAL_GALPAO
        marca=str(r.get('MARCA','SEM MARCA')).upper()
        chave=f"{idp}__{local}__{marca}__{lote}"
        q=safe_float(r.get('TOTAL',0)) or safe_float(r.get('QTD_PALETE',0))*safe_float(r.get('ENTRADA',0))
        if chave not in saldos:
            saldos[chave]={'ID':idp,'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'LOCAL':local,'MARCA':marca,'LOTE':lote,'SALDO':q,'PAL':safe_float(r.get('ENTRADA',0))}
        else:
            saldos[chave]['SALDO']+=q
            saldos[chave]['PAL']+=safe_float(r.get('ENTRADA',0))
    for m in st.session_state.mov:
        idp=str(m.get('ID','')).upper()
        lote=str(m.get('LOTE','')).upper()
        if not idp or not lote: continue
        local=str(m.get('LOCAL_MOV',LOCAL_GALPAO))
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

agora=datetime.now(fuso)
st.title(f"REFORMA FORNOS V12 - {agora.strftime('%d/%m/%Y %H:%M')}")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["DASHBOARD","CADASTRO","ENTRADA/SAIDA","ESTOQUE","BUSCA ID","GRD","GRAFICOS"])

with tab1:
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOCAL':v['LOCAL'],'MARCA':v['MARCA'],'LOTE':v['LOTE'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if df.empty: st.warning("Sem estoque")
    else:
        c1,c2,c3=st.columns(3)
        with c1: st.metric("TOTAL QTD", f"{df['SALDO'].sum():,.0f}")
        with c2: st.metric("TOTAL PAL", f"{df['PAL'].sum():.1f}")
        with c3: st.metric("LOTES", len(df))
        if not df.empty:
            df_g = df.groupby('LOCAL', as_index=False)['SALDO'].sum()
            fig = px.pie(df_g, values='SALDO', names='LOCAL', title="POR LOCAL")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("CADASTRO")
    id_b = st.text_input("DIGITE ID PARA RECONHECER", key="cad_id_busca_v12")
    desc_def=""; marca_def=""
    for r in st.session_state.cad:
        if str(r.get('ID','')).upper()==id_b.upper():
            desc_def=r.get('DESCRICAO',''); marca_def=r.get('MARCA','')
    with st.form("form_cad_v12"):
        id_in=st.text_input("ID*", value=id_b.upper() if id_b else "1", key="cad_id_v12")
        desc_in=st.text_input("DESCRICAO*", value=desc_def, key="cad_desc_v12")
        marca_in=st.text_input("MARCA*", value=marca_def, key="cad_marca_v12")
        lote_in=st.text_input("LOTE OPCIONAL", key="cad_lote_v12")
        local_in=st.selectbox("LOCAL", LOCAIS, key="cad_local_v12")
        qtd_in=st.number_input("QTD/PALETE", value=1250.0, key="cad_qtd_v12")
        ent_in=st.number_input("QTD PALETES", value=0.0, key="cad_ent_v12")
        if st.form_submit_button("CADASTRAR", type="primary"):
            if not id_in or not desc_in or not marca_in: st.error("Preencha")
            else:
                total=qtd_in*ent_in
                st.session_state.cad.append({"ID":id_in.upper(),"DESCRICAO":desc_in.upper(),"MARCA":marca_in.upper(),"LOTE":lote_in.upper(),"QTD_PALETE":qtd_in,"ENTRADA":ent_in,"TOTAL":total,"LOCAL":local_in,"FABRICACAO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                st.success("Cadastrado"); st.rerun()
    if st.session_state.cad:
        for i,r in enumerate(st.session_state.cad):
            if id_b and id_b.upper() not in r.get('ID',''): continue
            c1,c2,c3=st.columns([4,2,1])
            with c1: st.write(f"ID {r.get('ID')} - {r.get('DESCRICAO')} - {r.get('MARCA')} - {r.get('LOCAL')}")
            with c2: st.write(f"Lote {r.get('LOTE')} - {r.get('QTD_PALETE')}")
            with c3:
                if st.button("Excluir", key=f"del_cad_v12_{i}"):
                    st.session_state.cad.pop(i)
                    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
                    st.rerun()

with tab3:
    st.subheader("ENTRADA/SAIDA - LOTE NASCE AQUI")
    ids=list(set([r.get('ID','') for r in st.session_state.cad if r.get('ID')]))
    if not ids: st.warning("Cadastre ID primeiro")
    else:
        id_sel=st.selectbox("ID*", options=sorted(ids), key="mov_id_v12")
        cat=None
        for r in st.session_state.cad:
            if r.get('ID')==id_sel: cat=r
        desc=cat.get('DESCRICAO','') if cat else ""
        st.text_input("Descricao", value=desc, disabled=True, key="mov_desc_v12")
        lote=st.text_input("LOTE* OBRIGATORIO", key="mov_lote_v12")
        marca=st.text_input("MARCA*", value=cat.get('MARCA','') if cat else "", key="mov_marca_v12")
        local_o=st.selectbox("ORIGEM", LOCAIS, key="mov_orig_v12")
        tipo=st.selectbox("TIPO", ["ENTRADA","SAIDA","TRANSFERENCIA"], key="mov_tipo_v12")
        pal=st.number_input("QTD PALETES", value=1.0, key="mov_pal_v12")
        dest=st.selectbox("DESTINO TRANSFER", LOCAIS, index=1, key="mov_dest_v12")
        if st.button("CONFIRMAR", type="primary", key="mov_btn_v12"):
            if not lote: st.error("LOTE obrigatorio")
            else:
                qtd_base=safe_float(cat.get('QTD_PALETE',1250)) if cat else 1250
                tot=pal*qtd_base
                if tipo=="ENTRADA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":local_o,"DATA":date.today().strftime("%d/%m/%Y")})
                elif tipo=="SAIDA":
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":local_o,"DATA":date.today().strftime("%d/%m/%Y")})
                else:
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"SAIDA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":local_o,"DATA":date.today().strftime("%d/%m/%Y")})
                    st.session_state.mov.append({"ID":id_sel,"LOTE":lote.upper(),"MARCA":marca.upper(),"DESCRICAO":desc,"TIPO":"ENTRADA","PALETES":pal,"TOTAL_QTD":tot,"LOCAL_MOV":dest,"DATA":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success("OK"); st.rerun()

with tab4:
    st.subheader("ESTOQUE")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'LOCAL':v['LOCAL'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if not df.empty: st.dataframe(df, use_container_width=True, height=600)
    else: st.info("Sem estoque")

with tab5:
    st.subheader("BUSCA POR ID")
    id_b=st.text_input("DIGITE ID", key="busca_id_v12")
    if id_b:
        saldos=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper() and v['SALDO']>0]
        if lista:
            df=pd.DataFrame([{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'LOCAL':v['LOCAL'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in lista])
            tot=df['SALDO'].sum()
            st.success(f"ID {id_b} TOTAL {tot:,.0f} - {len(df)} lotes")
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                fig=px.bar(df, x='LOCAL', y='SALDO', color='MARCA', barmode='group', title=f"ID {id_b}")
                st.plotly_chart(fig, use_container_width=True)
                msg=f"ID {id_b} TOTAL {tot:,.0f}"
                st.link_button("ZAP", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        else: st.warning("Sem saldo")

with tab6:
    st.subheader("GRD + ZAP")
    ids=list(set([r.get('ID','') for r in st.session_state.cad if r.get('ID')]))
    if ids:
        id_g=st.selectbox("ID GRD*", options=sorted(ids), key="grd_id_v12")
        cat=None
        for r in st.session_state.cad:
            if r.get('ID')==id_g: cat=r
        desc=cat.get('DESCRICAO','') if cat else ""
        st.text_input("Descricao GRD", value=desc, disabled=True, key="grd_desc_v12")
        lote=st.text_input("LOTE GRD*", key="grd_lote_v12")
        marca=st.text_input("MARCA GRD*", value=cat.get('MARCA','') if cat else "", key="grd_marca_v12")
        qtd=st.number_input("QTD PALETES GRD*", value=1.0, key="grd_qtd_v12")
        ori=st.selectbox("ORIGEM GRD*", LOCAIS, key="grd_ori_v12")
        dst=st.selectbox("DESTINO GRD*", [l for l in LOCAIS if l!=ori], key="grd_dst_v12")
        os_g=st.text_input("OS/FORNO*", key="grd_os_v12")
        if st.button("GERAR GRD", type="primary", key="grd_btn_v12"):
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
        df=pd.DataFrame(st.session_state.grd)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            ult=df.iloc[-1]
            msg=f"GRD {ult.get('NUM_GRD')} ID {ult.get('ID')} {ult.get('QTD_PALETES')} PAL {ult.get('ORIGEM')}->{ult.get('DESTINO')}"
            st.link_button("ZAP GRD", f"https://wa.me/?text={urllib.parse.quote(msg)}")

with tab7:
    st.subheader("GRAFICOS")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOCAL':v['LOCAL'],'MARCA':v['MARCA'],'SALDO':v['SALDO']} for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if df.empty: st.info("Sem estoque")
    else:
        df_top = df.groupby('ID', as_index=False)['SALDO'].sum().sort_values(by='SALDO', ascending=False).head(20)
        fig = px.bar(df_top, x='ID', y='SALDO', title="TOP 20 IDs")
        st.plotly_chart(fig, use_container_width=True)

        df_local = df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        fig2 = px.bar(df_local, x='LOCAL', y='SALDO', title="POR LOCAL", color='LOCAL')
        st.plotly_chart(fig2, use_container_width=True)

        df_marca = df.groupby('MARCA', as_index=False)['SALDO'].sum().sort_values(by='SALDO', ascending=False).head(10)
        fig3 = px.bar(df_marca, x='MARCA', y='SALDO', title="TOP MARCAS", color='MARCA')
        st.plotly_chart(fig3, use_container_width=True)

        fig_pie = px.pie(df_local, values='SALDO', names='LOCAL', title="DISTRIBUICAO")
        st.plotly_chart(fig_pie, use_container_width=True)

st.caption(f"V12 FINAL SEM ERRO - {agora.strftime('%d/%m/%Y %H:%M')}")
