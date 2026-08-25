import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao_refratario.csv"
CAPACIDADE = 1000

# ===== MARCA D'ÁGUA EM DESTAQUE =====
st.markdown("""
<style>
.watermark-container {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 0; pointer-events: none;
    display: flex; flex-wrap: wrap; justify-content: center; align-content: center;
    gap: 120px; opacity: 0.18;
}
.watermark-item {
    font-size: 34px; font-weight: 900; color: #ff4e00;
    transform: rotate(-35deg);
    text-shadow: 2px 2px 0 #000, 0 0 10px rgba(255,78,0,0.8);
    border: 4px solid #ff4e00; padding: 10px 20px; border-radius: 12px;
    background: rgba(0,0,0,0.05); white-space: nowrap;
}
.watermark-top {
    position: fixed; top: 10px; right: 20px; font-size: 14px; font-weight: 900;
    color: #fff; z-index: 9999; pointer-events: none;
    background: linear-gradient(90deg, #ff4e00, #ff0000);
    padding: 8px 18px; border-radius: 25px; border: 2px solid #000;
    box-shadow: 0 0 15px #ff4e00; text-shadow: 1px 1px 0 #000;
}
.watermark-bottom {
    position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%);
    font-size: 13px; font-weight: 900; color: #ff4e00; z-index: 9999; pointer-events: none;
    background: #000; padding: 6px 18px; border-radius: 20px; border: 2px solid #ff4e00;
}
.block-container { position:relative; z-index:1; }
.main-header { background: linear-gradient(90deg, #000, #ff4e00); padding:26px; border-radius:16px; text-align:center; border:2px solid #ff4e00; position:relative; z-index:1; }
.main-header h1 { color:#fff; font-size:32px; font-weight:900; margin:0; }
.card-calc { background: linear-gradient(135deg, #fff, #ffe0b2); border-left:8px solid #ff4e00; padding:12px; border-radius:12px; position:relative; z-index:1; }
.big-number { font-size:30px; font-weight:900; color:#ff4e00; }
</style>
<div class="watermark-container">
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
</div>
<div class="watermark-top">🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</div>
<div class="watermark-bottom">⚠️ PROTEGIDO - REFORMA DE FORNOS - MATERIAIS REFRATARIOS ⚠️</div>
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

if 'iniciado' not in st.session_state:
    c,m=carregar()
    st.session_state.cadastro=c
    st.session_state.mov=m
    st.session_state.iniciado=True

st.markdown("""
<div class="main-header">
    <h1>🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</h1>
</div>
""", unsafe_allow_html=True)

tab1,tab2,tab3,tab4 = st.tabs(["📝 CADASTRO","🔄 MOV","📦 SALDO","📈 DASHBOARD LINHA"])

with tab1:
    st.info(f"📁 {len(st.session_state.cadastro)} registros")
    with st.form("cad",clear_on_submit=True):
        c1,c2,c3,c4=st.columns(4)
        with c1: id_p=st.text_input("ID *","01"); desc=st.text_input("DESC *","BLOCO"); marca=st.text_input("MARCA *","ESTRELA"); lote=st.text_input("LOTE *","L001")
        with c2: unidade=st.selectbox("UNIDADE",["peças","kg","m²","ton"]); emp=st.selectbox("EMP *",[1,2,3]); qtd=st.number_input("QTD/Pal",value=500.0)
        with c3: fab=st.date_input("FAB",value=date.today()); dias=st.number_input("DIAS VAL",value=365); val=fab+timedelta(days=int(dias)); val_m=st.date_input("VALIDADE",value=val)
        with c4:
            if st.form_submit_button("💾 SALVAR",type="primary",use_container_width=True):
                st.session_state.cadastro.append({"ID":str(id_p).upper(),"Descrição":str(desc).upper(),"Marca":str(marca).upper(),"LOTE":str(lote).upper(),"Unidade":unidade,"Empilhamento":int(emp),"Fabricação":str(fab),"Validade":str(val_m),"QTD_por_palete":float(qtd)})
                pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.rerun()
    if st.session_state.cadastro:
        st.dataframe(pd.DataFrame(st.session_state.cadastro),use_container_width=True)
        for idx in range(len(st.session_state.cadastro)-1,-1,-1):
            row=pd.DataFrame(st.session_state.cadastro).iloc[idx]
            a,b,c,d,e=st.columns([1,3,2,2,1])
            a.write(f"**{row['ID']}**"); b.write(f"{row['Descrição']} L:{row['LOTE']}"); c.write(f"{row['Marca']}"); d.write(f"{row['Validade']}")
            if e.button("🗑️",key=f"del_cad_{idx}"):
                st.session_state.cadastro.pop(idx)
                if st.session_state.cadastro: pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
                else: os.remove(ARQ_CAD) if os.path.exists(ARQ_CAD) else None
                st.rerun()

with tab2:
    if st.session_state.cadastro:
        df_cad=pd.DataFrame(st.session_state.cadastro)
        lista_ids=sorted([str(x) for x in df_cad["ID"].dropna().unique().tolist()])
        colA,colB=st.columns([1,1.6])
        with colA:
            tipo=st.radio("TIPO",["ENTRADA","SAÍDA"],horizontal=True)
            id_s=st.selectbox("ID",lista_ids)
            df_id=df_cad[df_cad["ID"]==id_s]; lista_marcas=sorted([str(x) for x in df_id["Marca"].dropna().unique().tolist()])
            marca_s=st.selectbox("MARCA",lista_marcas); df_marca=df_id[df_id["Marca"]==marca_s]
            lista_lotes=sorted([str(x) for x in df_marca["LOTE"].dropna().unique().tolist()])
            lote_s=st.selectbox("LOTE",lista_lotes); prod=df_marca[df_marca["LOTE"]==lote_s].iloc[0]
        with colB:
            qtd_pal=st.number_input("QTD PALETES",value=20,min_value=1); qtd_unid=qtd_pal*float(prod['QTD_por_palete'])
            st.markdown(f"<div class='card-calc'><b class='big-number'>{qtd_pal} pal = {qtd_unid:,.1f} {prod['Unidade']}</b><br>{qtd_pal/int(prod['Empilhamento']):.2f} posições</div>",unsafe_allow_html=True)
            if st.button("➕ LANÇAR",type="primary",use_container_width=True):
                pos=qtd_pal/int(prod['Empilhamento'])
                st.session_state.mov.append({"Data":str(date.today()),"Tipo":tipo,"ID":str(id_s),"Descrição":prod['Descrição'],"Marca":str(marca_s),"LOTE":str(lote_s),"Unidade":prod['Unidade'],"Empilhamento":int(prod['Empilhamento']),"Fabricação":prod['Fabricação'],"Validade":prod['Validade'],"QTD_Paletes":int(qtd_pal) if tipo=="ENTRADA" else -int(qtd_pal),"QTD_Unidade":float(qtd_unid) if tipo=="ENTRADA" else -float(qtd_unid),"Posições":float(pos) if tipo=="ENTRADA" else -float(pos)})
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False); st.rerun()
    if st.session_state.mov: st.dataframe(pd.DataFrame(st.session_state.mov),use_container_width=True)

with tab3:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"]); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Posições=("Posições","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]; st.metric("OCUPAÇÃO",f"{saldo['Posições'].sum():.1f}/1000"); st.dataframe(saldo,use_container_width=True)

with tab4:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"]); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade","Validade_dt"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]
        id_sel=st.selectbox("ID PARA VALIDADE",sorted([str(x) for x in saldo["ID"].dropna().unique().tolist()])); df_f=saldo[saldo["ID"]==id_sel].sort_values("Validade_dt")
        fig=go.Figure()
        for marca in df_f["Marca"].unique():
            df_m=df_f[df_f["Marca"]==marca]
            fig.add_trace(go.Scatter(x=df_m["Validade_dt"],y=df_m["Dias"],mode='lines+markers+text',name=str(marca),text=df_m["LOTE"]+"<br>"+df_m["QTD_Paletes"].astype(str)+" pal",line=dict(width=5),marker=dict(size=16,symbol='diamond')))
        fig.add_hline(y=0,line_color="red"); fig.add_vline(x=pd.to_datetime(date.today()),line_color="black")
        fig.update_layout(title=f"VALIDADE EM LINHA - ID {id_sel} - REFORMA DE FORNOS - MATERIAIS REFRATARIOS", height=550)
        st.plotly_chart(fig,use_container_width=True)
