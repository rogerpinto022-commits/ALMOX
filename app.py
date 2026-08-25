import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import os

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao_refratario.csv"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap');

/* TOPO COM LED */
.main-header {
    background: radial-gradient(circle at top, #2a2a2a 0%, #000000 100%);
    padding: 35px;
    border-radius: 20px;
    text-align: center;
    border: 3px solid #ff4e00;
    box-shadow: 0 0 15px #ff4e00, 0 0 30px #ff8a00, 0 0 45px rgba(255,78,0,0.5), inset 0 0 20px rgba(255,78,0,0.2);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -2px; left: -2px; right: -2px; bottom: -2px;
    background: linear-gradient(45deg, #ff4e00, #ffe600, #ff4e00, #ec0000);
    border-radius: 20px;
    z-index: -1;
    animation: ledBorder 2s linear infinite;
}
@keyframes ledBorder {
    0% { filter: hue-rotate(0deg); }
    100% { filter: hue-rotate(360deg); }
}
.main-header h1 {
    font-family: 'Montserrat', sans-serif;
    color: #fff;
    font-size: 44px;
    font-weight: 900;
    margin: 0;
    text-shadow: 0 0 10px #ff4e00, 0 0 20px #ff4e00, 0 0 30px #ff0000, 3px 3px 0px #000;
    animation: ledFlicker 1.5s infinite alternate;
}
@keyframes ledFlicker {
    0% { text-shadow: 0 0 10px #ff4e00, 0 0 20px #ff4e00, 3px 3px 0px #000; }
    100% { text-shadow: 0 0 20px #ffe600, 0 0 40px #ff4e00, 0 0 60px #ff0000, 3px 3px 0px #000; }
}
.main-header h2 {
    color: #00ff88;
    font-size: 16px;
    font-weight: 700;
    margin-top: 12px;
    background: rgba(0,0,0,0.8);
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    border: 1px solid #00ff88;
    box-shadow: 0 0 10px #00ff88, inset 0 0 10px rgba(0,255,136,0.2);
    font-family: monospace;
    letter-spacing: 1px;
}

/* CARDS COM SOMBREADO E LED */
.metric-box {
    background: linear-gradient(145deg, #1a1a1a, #0a0a0a);
    color: white;
    padding: 22px;
    border-radius: 16px;
    text-align: center;
    border: 2px solid #333;
    box-shadow: 0 8px 20px rgba(0,0,0,0.8), 0 0 15px rgba(255,78,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
    transition: all 0.3s;
    position: relative;
}
.metric-box:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.9), 0 0 25px #ff4e00, inset 0 1px 0 rgba(255,255,255,0.2);
    border-color: #ff4e00;
}
.metric-box h3 { color: #888; margin:0; font-size: 12px; letter-spacing:2px; }
.metric-box h2 { color: #ffe600; margin:8px 0; font-size: 32px; text-shadow: 0 0 10px #ffe600; }

.card-prod {
    background: linear-gradient(145deg, #1e1e1e, #000);
    border-left: 6px solid #ff4e00;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.7), 0 0 12px rgba(255,78,0,0.4);
    color: white;
    border-top: 1px solid #333;
    border-right: 1px solid #333;
    border-bottom: 1px solid #333;
}

/* LED INDICADORES */
.led {
    width: 14px; height: 14px; border-radius: 50%; display: inline-block; margin-right: 6px;
    box-shadow: 0 0 8px currentColor, 0 0 15px currentColor;
    animation: ledPulse 1s infinite alternate;
}
.led-green { background: #00ff88; color: #00ff88; }
.led-red { background: #ff1744; color: #ff1744; }
.led-yellow { background: #ffe600; color: #ffe600; }
@keyframes ledPulse {
    0% { opacity: 0.7; box-shadow: 0 0 5px currentColor; }
    100% { opacity: 1; box-shadow: 0 0 15px currentColor, 0 0 25px currentColor; }
}

/* ABAS LED */
.stTabs [data-baseweb="tab"] {
    background: #111 !important;
    color: #888 !important;
    border: 2px solid #333 !important;
    border-radius: 12px !important;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.8) !important;
    font-weight: 800 !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #ff4e00, #ff0000) !important;
    color: white !important;
    border-color: #ffe600 !important;
    box-shadow: 0 0 15px #ff4e00, 0 0 25px rgba(255,78,0,0.6) !important;
    text-shadow: 0 0 8px white !important;
}

/* BOTÃO LED */
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #ff4e00, #cc0000) !important;
    border: 2px solid #000 !important;
    font-weight: 900 !important;
    box-shadow: 0 0 0 2px #ff4e00, 0 6px 0 #000, 0 0 20px rgba(255,78,0,0.6) !important;
    border-radius: 14px !important;
    text-shadow: 0 1px 0 #000 !important;
    transition: all 0.1s !important;
}
.stButton>button[kind="primary"]:active {
    transform: translateY(4px);
    box-shadow: 0 0 0 2px #ff4e00, 0 2px 0 #000, 0 0 10px rgba(255,78,0,0.6) !important;
}
</style>
""", unsafe_allow_html=True)

def carregar():
    c,m=[],[] 
    if os.path.exists(ARQ_CAD):
        try: c=pd.read_csv(ARQ_CAD).to_dict('records')
        except: pass
    if os.path.exists(ARQ_MOV):
        try: m=pd.read_csv(ARQ_MOV).to_dict('records')
        except: pass
    return c,m
def salvar_cad(): pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
def salvar_mov(): pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)

if 'cadastro' not in st.session_state:
    c,m=carregar()
    st.session_state.cadastro=c
    st.session_state.mov=m

st.markdown("""
<div class="main-header">
    <h1>🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS 🔥</h1>
    <h2><span class="led led-green"></span>SISTEMA ONLINE <span class="led led-yellow"></span>1000 POSIÇÕES <span class="led led-red"></span>LED ATIVO - CHÃO CONTROL</h2>
</div>
""", unsafe_allow_html=True)

tab1,tab2,tab3,tab4 = st.tabs(["📝 CADASTRO LED","🔄 MOVIMENTAÇÃO","📦 SALDO","📈 DASHBOARD LED"])

with tab1:
    with st.form("form",clear_on_submit=True):
        c1,c2,c3,c4=st.columns(4)
        with c1:
            id_p=st.text_input("ID *","01")
            desc=st.text_input("DESCRIÇÃO *","BLOCO ESTRELA")
            marca=st.text_input("MARCA *","ESTRELA")
            lote=st.text_input("LOTE *","L2024-001")
        with c2:
            unidade=st.selectbox("UNIDADE *",["peças","kg","m²","ton","rolos"])
            emp=st.selectbox("EMPILHAMENTO *",[1,2,3])
            qtd=st.number_input("QTD por Palete",value=500.0)
        with c3:
            fab=st.date_input("FABRICAÇÃO",value=date.today())
            dias=st.number_input("DIAS VALIDADE",value=365)
            val=fab+timedelta(days=int(dias))
            st.markdown(f"<div style='background:#000;color:#00ff88;border:2px solid #00ff88;box-shadow:0 0 15px #00ff88;padding:10px;border-radius:10px;font-weight:900;text-align:center;font-family:monospace;'>⏰ VALIDADE: {val.strftime('%d/%m/%Y')}</div>",unsafe_allow_html=True)
            val_m=st.date_input("Ajuste Validade",value=val)
        with c4:
            st.markdown(f"<div class='metric-box'><h3><span class='led led-yellow'></span>EMPILHAMENTO</h3><h2>{emp} = 1 POS</h2><div style='color:#888;font-size:12px;'>20 POS = {20*emp} PALETES<br><span class='led led-green'></span>SOMBREADO ATIVO</div></div>",unsafe_allow_html=True)
            if st.form_submit_button("💾 SALVAR COM LED",type="primary",use_container_width=True):
                st.session_state.cadastro.append({"ID":id_p.upper(),"Descrição":desc.upper(),"Marca":marca.upper(),"LOTE":lote.upper(),"Unidade":unidade,"Empilhamento":int(emp),"Fabricação":str(fab),"Validade":str(val_m),"Dias_Validade":int(dias),"QTD_por_palete":qtd})
                salvar_cad()
                st.success("LED VERDE - Gravado!")

    if st.session_state.cadastro:
        df=pd.DataFrame(st.session_state.cadastro)
        edited=st.data_editor(df,use_container_width=True,num_rows="dynamic")
        if st.button("💾 GRAVAR EDIÇÃO LED",type="primary",use_container_width=True):
            st.session_state.cadastro=edited.to_dict('records')
            salvar_cad()
            st.rerun()

with tab2:
    if st.session_state.cadastro:
        df_cad=pd.DataFrame(st.session_state.cadastro)
        ca,cb=st.columns([1,1.6])
        with ca:
            tipo=st.radio("TIPO", ["ENTRADA","SAÍDA"], horizontal=True)
            id_s=st.selectbox("ID", sorted(df_cad["ID"].unique()))
            marca_s=st.selectbox("MARCA", df_cad[df_cad["ID"]==id_s]["Marca"].unique())
            df_f=df_cad[(df_cad["ID"]==id_s)&(df_cad["Marca"]==marca_s)]
            lote_s=st.selectbox("LOTE", df_f["LOTE"].unique())
            prod=df_f[df_f["LOTE"]==lote_s].iloc[-1]
        with cb:
            st.markdown(f"<div class='card-prod'><span class='led led-green'></span><b style='font-size:20px;color:#ffe600;'>{prod['Descrição']}</b><br><span class='led led-yellow'></span>Marca: {prod['Marca']} | Lote: <span style='background:#ff4e00;color:white;padding:3px 10px;border-radius:6px;box-shadow:0 0 10px #ff4e00;'>{prod['LOTE']}</span><br><span class='led led-red'></span>Fab: {prod['Fabricação']} | Val: {prod['Validade']}</div>",unsafe_allow_html=True)
            c1,c2,c3=st.columns(3)
            with c1: qp=st.number_input("QTD PALETES", value=20, min_value=1)
            with c2: qu=st.number_input("QTD UNIDADE", value=float(prod['QTD_por_palete']*qp))
            with c3:
                pos=qp/int(prod['Empilhamento'])
                st.markdown(f"<div class='metric-box'><h3>POS CHÃO</h3><h2 style='color:#00ff88;text-shadow:0 0 15px #00ff88;'>{pos:.1f}</h2></div>", unsafe_allow_html=True)
            if st.button("➕ LANÇAR COM LED", type="primary", use_container_width=True):
                st.session_state.mov.append({"Data":str(date.today()),"Tipo":tipo,"ID":id_s,"Descrição":prod['Descrição'],"Marca":marca_s,"LOTE":lote_s,"Unidade":prod['Unidade'],"Empilhamento":int(prod['Empilhamento']),"Fabricação":prod['Fabricação'],"Validade":prod['Validade'],"QTD_Paletes":qp if tipo=="ENTRADA" else -qp,"QTD_Unidade":qu if tipo=="ENTRADA" else -qu,"Posições":pos if tipo=="ENTRADA" else -pos})
                salvar_mov()
                st.success("LED PISCANDO - Lançado!")
        if st.session_state.mov:
            st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

with tab3:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov)
        df["Validade_dt"]=pd.to_datetime(df["Validade"])
        df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Posições=("Posições","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]
        saldo["Pos_Ocup"]=saldo["QTD_Paletes"]/saldo["Empilhamento"]
        total=saldo["Pos_Ocup"].sum()
        taxa=total/1000*100
        m1,m2,m3,m4=st.columns(4)
        with m1: st.markdown(f"<div class='metric-box'><h3><span class='led led-green'></span>PALETES</h3><h2>{int(saldo['QTD_Paletes'].sum())}</h2></div>",unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-box'><h3><span class='led led-yellow'></span>OCUPADAS</h3><h2>{total:.0f}/1000</h2></div>",unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-box'><h3><span class='led led-green'></span>LIVRES</h3><h2>{1000-total:.0f}</h2></div>",unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='metric-box'><h3><span class='led led-red'></span>TAXA</h3><h2>{taxa:.1f}%</h2></div>",unsafe_allow_html=True)
        st.progress(min(taxa/100,1.0))
        st.dataframe(saldo.sort_values("Dias"),use_container_width=True)

with tab4:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov)
        df["Validade_dt"]=pd.to_datetime(df["Validade"])
        df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]
        saldo["Pos_Ocup"]=saldo["QTD_Paletes"]/2
        st.plotly_chart(px.pie(pd.DataFrame({"Status":["OCUPADO","LIVRE"],"Pos":[saldo["Pos_Ocup"].sum(),1000-saldo["Pos_Ocup"].sum()]}),values="Pos",names="Status",hole=0.6,title="OCUPAÇÃO COM LED",color_discrete_sequence=["#ff4e00","#00ff88"]),use_container_width=True)
