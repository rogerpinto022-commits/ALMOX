import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
import plotly.express as px
import urllib.parse

st.set_page_config(page_title="REFORMA FORNOS V14 NUMEROS GRANDES", layout="wide")
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
    e = st.text_input("Email", key="login_email_v14")
    s = st.text_input("Senha", type="password", key="login_senha_v14")
    if st.button("Entrar", key="btn_entrar_v14"):
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

def excluir_registro_estoque(idp, local, marca, lote):
    idp=idp.upper(); lote=lote.upper(); marca=marca.upper()
    st.session_state.cad = [r for r in st.session_state.cad if not (str(r.get('ID','')).upper()==idp and str(r.get('LOTE','')).upper()==lote and str(r.get('MARCA','')).upper()==marca and str(r.get('LOCAL','')).upper().strip()==local.upper().strip())]
    st.session_state.mov = [m for m in st.session_state.mov if not (str(m.get('ID','')).upper()==idp and str(m.get('LOTE','')).upper()==lote and str(m.get('MARCA','')).upper()==marca and str(m.get('LOCAL_MOV','')).upper().strip()==local.upper().strip())]
    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)

agora=datetime.now(fuso)
st.markdown(f"<h1 style='text-align:center; background:black; color:#00ff66; padding:15px; border-radius:12px; border:4px solid orange;'>🔥 REFORMA FORNOS V14 - NUMEROS GRANDES - {agora.strftime('%d/%m/%Y %H:%M')} 🔥</h1>", unsafe_allow_html=True)

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
            df_g['TEXTO'] = df_g['SALDO'].apply(lambda x: f"{x:,.0f}")
            fig = px.bar(df_g, x='LOCAL', y='SALDO', text='TEXTO', title="SALDO POR LOCAL - NUMEROS GRANDES", color='LOCAL')
            fig.update_traces(textposition='inside', textfont=dict(size=28, color='white', family='Arial Black'))
            st.plotly_chart(fig, use_container_width=True)
            df_pie = df.groupby('LOCAL', as_index=False)['SALDO'].sum()
            fig_pie = px.pie(df_pie, values='SALDO', names='LOCAL', title="DISTRIBUICAO")
            fig_pie.update_traces(textinfo='value+percent+label', textfont_size=20)
            st.plotly_chart(fig_pie, use_container_width=True)
        st.dataframe(df, use_container_width=True)

with tab4:
    st.subheader("📦 ESTOQUE - COM BOTÃO EXCLUIR")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'LOCAL':v['LOCAL'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in saldos.values() if v['SALDO']>0]
    if not lista: st.info("Sem estoque")
    else:
        filtro=st.text_input("🔍 FILTRAR", key="filtro_estoque_v14")
        if filtro: lista=[x for x in lista if filtro.upper() in x['ID'] or filtro.upper() in x['DESCRICAO']]
        h1,h2,h3,h4,h5,h6,h7=st.columns([1,2,1,2,1,1,1])
        h1.markdown("**ID**"); h2.markdown("**DESCRICAO**"); h3.markdown("**LOTE**"); h4.markdown("**MARCA | LOCAL**"); h5.markdown("**SALDO**"); h6.markdown("**PAL**"); h7.markdown("**AÇÃO**")
        st.divider()
        for idx, v in enumerate(sorted(lista, key=lambda x: (x['ID'], x['LOTE']))):
            c1,c2,c3,c4,c5,c6,c7=st.columns([1,2,1,2,1,1,1])
            with c1: st.write(f"{v['ID']}")
            with c2: st.write(f"{v['DESCRICAO'][:20]}")
            with c3: st.write(f"{v['LOTE']}")
            with c4: st.write(f"{v['MARCA'][:10]} | {v['LOCAL'][:10]}")
            with c5: st.write(f"{v['SALDO']:,.0f}")
            with c6: st.write(f"{v['PAL']:.1f}")
            with c7:
                if st.button("🗑️ Excluir", key=f"del_est_v14_{idx}_{v['ID']}_{v['LOTE']}", type="primary", use_container_width=True):
                    excluir_registro_estoque(v['ID'], v['LOCAL'], v['MARCA'], v['LOTE'])
                    st.rerun()
        st.dataframe(pd.DataFrame(lista), use_container_width=True, height=300)

with tab5:
    st.subheader("BUSCA POR ID - NUMEROS GRANDES")
    id_b=st.text_input("DIGITE ID", key="busca_id_v14")
    if id_b:
        saldos=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper() and v['SALDO']>0]
        if lista:
            df=pd.DataFrame([{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOTE':v['LOTE'],'MARCA':v['MARCA'],'LOCAL':v['LOCAL'],'SALDO':v['SALDO'],'PAL':v['PAL']} for v in lista])
            df['TEXTO_GRANDE'] = df['SALDO'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df, use_container_width=True)
            fig=px.bar(df, x='LOCAL', y='SALDO', color='MARCA', barmode='group', text='TEXTO_GRANDE', title=f"ID {id_b} - NUMEROS GRANDES DENTRO")
            fig.update_traces(textposition='inside', textfont=dict(size=24, color='white', family='Arial Black'))
            st.plotly_chart(fig, use_container_width=True)

with tab7:
    st.subheader("📈 GRAFICOS - NUMEROS GRANDES DENTRO")
    saldos=get_saldos()
    lista=[{'ID':v['ID'],'DESCRICAO':v['DESCRICAO'],'LOCAL':v['LOCAL'],'MARCA':v['MARCA'],'SALDO':v['SALDO']} for v in saldos.values() if v['SALDO']>0]
    df=pd.DataFrame(lista)
    if df.empty: st.info("Sem estoque")
    else:
        df_top = df.groupby('ID', as_index=False)['SALDO'].sum().sort_values(by='SALDO', ascending=False).head(20)
        df_top['TEXTO'] = df_top['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig = px.bar(df_top, x='ID', y='SALDO', text='TEXTO', title="TOP 20 IDs - NUMEROS GIGANTES DENTRO", color='SALDO')
        fig.update_traces(textposition='inside', textfont=dict(size=22, color='white', family='Arial Black'))
        st.plotly_chart(fig, use_container_width=True)

        df_local = df.groupby('LOCAL', as_index=False)['SALDO'].sum()
        df_local['TEXTO'] = df_local['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig2 = px.bar(df_local, x='LOCAL', y='SALDO', text='TEXTO', title="POR LOCAL - NUMEROS GRANDES DENTRO", color='LOCAL')
        fig2.update_traces(textposition='inside', textfont=dict(size=32, color='white', family='Arial Black'))
        st.plotly_chart(fig2, use_container_width=True)

        df_marca = df.groupby('MARCA', as_index=False)['SALDO'].sum().sort_values(by='SALDO', ascending=False).head(10)
        df_marca['TEXTO'] = df_marca['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig3 = px.bar(df_marca, x='MARCA', y='SALDO', text='TEXTO', title="TOP 10 MARCAS - NUMEROS GRANDES DENTRO", color='MARCA')
        fig3.update_traces(textposition='inside', textfont=dict(size=24, color='white', family='Arial Black'))
        st.plotly_chart(fig3, use_container_width=True)

        fig_pie = px.pie(df_local, values='SALDO', names='LOCAL', title="DISTRIBUICAO - NUMEROS GRANDES")
        fig_pie.update_traces(textinfo='value+percent+label', textfont_size=24, textposition='inside')
        st.plotly_chart(fig_pie, use_container_width=True)

#... as outras abas CADASTRO, ENTRADA/SAIDA, GRD continuam iguais do V13
