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

# ===== MARCA D'ÁGUA EM DESTAQUE - CORRIGIDA =====
st.markdown("""
<style>
.watermark-container {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 0; pointer-events: none;
    display: flex; flex-wrap: wrap; justify-content: center; align-content: center;
    gap: 100px; opacity: 0.16;
}
.watermark-item {
    font-size: 32px; font-weight: 900; color: #ff4e00;
    transform: rotate(-32deg);
    text-shadow: 2px 2px 0 #000;
    border: 3px solid #ff4e00; padding: 8px 18px; border-radius: 10px;
    white-space: nowrap;
}
.watermark-top {
    position: fixed; top: 8px; right: 18px; font-size: 13px; font-weight: 900;
    color: #fff; z-index: 9999; pointer-events: none;
    background: linear-gradient(90deg, #ff4e00, #ff0000);
    padding: 7px 16px; border-radius: 22px; border: 2px solid #000;
    box-shadow: 0 0 12px #ff4e00;
}
.block-container { position:relative; z-index:1; }
.main-header { background: linear-gradient(90deg, #000, #ff4e00); padding:24px; border-radius:14px; text-align:center; border:2px solid #ff4e00; position:relative; z-index:1; }
.card-calc { background: #fff7e6; border-left:8px solid #ff4e00; padding:10px; border-radius:10px; position:relative; z-index:1; }
.big-number { font-size:28px; font-weight:900; color:#ff4e00; }
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
""", unsafe_allow_html=True)

def carregar():
    c,m=[],[]
    try:
        if os.path.exists(ARQ_CAD):
            df=pd.read_csv(ARQ_CAD)
            if not df.empty: c=df.to_dict('records')
    except: pass
    try:
        if os.path.exists(ARQ_MOV):
            df=pd.read_csv(ARQ_MOV)
            if not df.empty: m=df.to_dict('records')
    except: pass
    return c,m

if 'iniciado' not in st.session_state:
    c,m=carregar()
    st.session_state.cadastro=c
    st.session_state.mov=m
    st.session_state.iniciado=True

st.markdown('<div class="main-header"><h1 style="color:white;margin:0">🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</h1></div>', unsafe_allow_html=True)

tab1,tab2,tab3,tab4 = st.tabs(["📝 CADASTRO","🔄 MOV","📦 SALDO","📈 LINHA VALIDADE"])

with tab1:
    st.info(f"📁 {len(st.session_state.cadastro)} cadastrados")
    with st.form("cad", clear_on_submit=True):
        c1,c2,c3,c4=st.columns(4)
        with c1: id_p=st.text_input("ID *","01"); desc=st.text_input("DESC *","BLOCO"); marca=st.text_input("MARCA *","ESTRELA"); lote=st.text_input("LOTE *","L001")
        with c2: unidade=st.selectbox("UNIDADE",["peças","kg","m²","ton"]); emp=st.selectbox("EMP *",[1,2,3]); qtd=st.number_input("QTD/Pal",value=500.0)
        with c3: fab=st.date_input("FAB",value=date.today()); dias=st.number_input("DIAS VAL",value=365); val=fab+timedelta(days=int(dias)); val_m=st.date_input("VALIDADE",value=val)
        with c4:
            if st.form_submit_button("💾 SALVAR",type="primary",use_container_width=True):
                if id_p and desc and marca and lote:
                    st.session_state.cadastro.append({"ID":str(id_p).strip().upper(),"Descrição":str(desc).strip().upper(),"Marca":str(marca).strip().upper(),"LOTE":str(lote).strip().upper(),"Unidade":unidade,"Empilhamento":int(emp),"Fabricação":str(fab),"Validade":str(val_m),"QTD_por_palete":float(qtd)})
                    pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.rerun()
                else: st.error("Preencha todos *")
    if st.session_state.cadastro:
        df_cad_show=pd.DataFrame(st.session_state.cadastro)
        st.dataframe(df_cad_show,use_container_width=True)
        st.write("🗑️ Excluir individual:")
        for idx in range(len(df_cad_show)-1,-1,-1):
            try:
                row=df_cad_show.iloc[idx]
                a,b,c,d,e=st.columns([1,3,2,2,1])
                a.write(f"**{row['ID']}**"); b.write(f"{row['Descrição']} L:{row['LOTE']}"); c.write(f"{row['Marca']}"); d.write(f"{row['Validade']}")
                if e.button("🗑️",key=f"del_cad_{idx}_{row['LOTE']}"):
                    st.session_state.cadastro.pop(idx)
                    if st.session_state.cadastro: pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
                    else:
                        if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
                    st.rerun()
            except: continue

with tab2:
    st.markdown("### Movimentação - Cálculo Palete + Unidade")
    if not st.session_state.cadastro:
        st.warning("Cadastre na aba 1 primeiro")
    else:
        try:
            df_cad=pd.DataFrame(st.session_state.cadastro)
            if df_cad.empty:
                st.warning("Cadastro vazio")
            else:
                lista_ids=sorted([str(x) for x in df_cad["ID"].dropna().astype(str).unique().tolist() if str(x).strip()!=""])
                if not lista_ids:
                    st.warning("Nenhum ID cadastrado")
                else:
                    colA,colB=st.columns([1,1.6])
                    with colA:
                        tipo=st.radio("TIPO",["ENTRADA","SAÍDA"],horizontal=True)
                        id_s=st.selectbox("ID",lista_ids, key="sel_id")
                        # FILTRO SEGURO
                        df_id=df_cad[df_cad["ID"].astype(str)==str(id_s)] if id_s else pd.DataFrame()
                        if df_id.empty:
                            st.error("ID sem dados"); marca_s=None; lote_s=None; prod=None
                        else:
                            lista_marcas=sorted([str(x) for x in df_id["Marca"].dropna().astype(str).unique().tolist() if str(x).strip()!=""])
                            marca_s=st.selectbox("MARCA",lista_marcas if lista_marcas else ["SEM MARCA"], key="sel_marca")
                            df_marca=df_id[df_id["Marca"].astype(str)==str(marca_s)] if marca_s else pd.DataFrame()
                            if df_marca.empty:
                                lote_s=None; prod=None
                            else:
                                lista_lotes=sorted([str(x) for x in df_marca["LOTE"].dropna().astype(str).unique().tolist() if str(x).strip()!=""])
                                lote_s=st.selectbox("LOTE",lista_lotes if lista_lotes else ["SEM LOTE"], key="sel_lote")
                                df_lote=df_marca[df_marca["LOTE"].astype(str)==str(lote_s)] if lote_s else df_marca
                                prod = df_lote.iloc[0] if not df_lote.empty else df_marca.iloc[0] if not df_marca.empty else None

                    with colB:
                        if 'prod' in locals() and prod is not None:
                            try:
                                qtd_por_pal=float(prod.get('QTD_por_palete',500))
                                emp_int=int(prod.get('Empilhamento',1))
                                unidade_str=str(prod.get('Unidade','peças'))
                                st.markdown(f"<div class='card-calc'><b>{prod.get('Descrição','')}</b> | Marca <b>{prod.get('Marca','')}</b> | Lote <b>{prod.get('LOTE','')}</b><br>1 palete = <b>{qtd_por_pal} {unidade_str}</b> | Emp: <b>{emp_int}</b></div>",unsafe_allow_html=True)
                                qtd_pal=st.number_input("QTD PALETES",value=20,min_value=1,step=1,key="qtd_pal")
                                qtd_unid=qtd_pal*qtd_por_pal
                                st.markdown(f"<div class='card-calc'><span class='big-number'>{qtd_pal} pal = {qtd_unid:,.1f} {unidade_str}</span><br>{qtd_pal/emp_int:.2f} posições chão</div>",unsafe_allow_html=True)
                                if st.button(f"➕ LANÇAR {tipo}",type="primary",use_container_width=True,key="btn_lancar"):
                                    pos_calc=qtd_pal/emp_int if emp_int>0 else qtd_pal
                                    st.session_state.mov.append({
                                        "Data":str(date.today()),"Tipo":tipo,"ID":str(id_s),"Descrição":str(prod.get('Descrição','')),"Marca":str(marca_s),"LOTE":str(lote_s),
                                        "Unidade":unidade_str,"Empilhamento":emp_int,"Fabricação":str(prod.get('Fabricação','')),"Validade":str(prod.get('Validade','')),
                                        "QTD_Paletes":int(qtd_pal) if tipo=="ENTRADA" else -int(qtd_pal),
                                        "QTD_Unidade":float(qtd_unid) if tipo=="ENTRADA" else -float(qtd_unid),
                                        "Posições":float(pos_calc) if tipo=="ENTRADA" else -float(pos_calc)
                                    })
                                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False); st.success("Lançado!"); st.rerun()
                            except Exception as e:
                                st.error(f"Erro no cálculo: {e}")
                        else:
                            st.info("Selecione ID/MARCA/LOTE válidos")
        except Exception as e:
            st.error(f"Erro aba MOV: {e}")

    if st.session_state.mov:
        try: st.dataframe(pd.DataFrame(st.session_state.mov),use_container_width=True)
        except: st.write(st.session_state.mov)

with tab3:
    if st.session_state.mov:
        try:
            df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"],errors='coerce'); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
            saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Posições=("Posições","sum"),Dias=("Dias","min"))
            saldo=saldo[saldo["QTD_Paletes"]>0];
            if not saldo.empty:
                st.metric("OCUPAÇÃO",f"{saldo['Posições'].sum():.1f}/1000"); st.dataframe(saldo.sort_values("Dias"),use_container_width=True)
        except Exception as e: st.error(f"Erro saldo: {e}")

with tab4:
    st.markdown("## 📈 GRÁFICO DE LINHA - VALIDADE EM DESTAQUE")
    if not st.session_state.mov:
        st.warning("Sem movimentação")
    else:
        try:
            df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"],errors='coerce'); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
            saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade","Validade_dt"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Dias=("Dias","min"))
            saldo=saldo[saldo["QTD_Paletes"]>0].dropna(subset=["Validade_dt"])
            if saldo.empty: st.warning("Sem saldo")
            else:
                lista_ids_dash=sorted([str(x) for x in saldo["ID"].dropna().astype(str).unique().tolist()])
                id_sel=st.selectbox("ESCOLHA ID",lista_ids_dash,key="id_dash")
                df_f=saldo[saldo["ID"].astype(str)==str(id_sel)].sort_values("Validade_dt")
                if df_f.empty: st.warning("ID sem dados")
                else:
                    c1,c2,c3=st.columns(3)
                    c1.metric("PALETES",int(df_f["QTD_Paletes"].sum())); c2.metric(f"{df_f.iloc[0]['Unidade'].upper()}",f"{df_f['QTD_Unidade'].sum():,.0f}"); c3.metric("POSIÇÕES",f"{df_f['Posições'].sum() if 'Posições' in df_f else 0:.1f}")
                    fig=go.Figure()
                    cores=px.colors.qualitative.Bold
                    for i, marca in enumerate(df_f["Marca"].astype(str).unique()):
                        df_m=df_f[df_f["Marca"].astype(str)==str(marca)].sort_values("Validade_dt")
                        fig.add_trace(go.Scatter(
                            x=df_m["Validade_dt"], y=df_m["Dias"], mode='lines+markers+text',
                            name=f"{marca} | {int(df_m['QTD_Paletes'].sum())} pal | {df_m['QTD_Unidade'].sum():,.0f} {df_m.iloc[0]['Unidade']}",
                            text=df_m["LOTE"]+"<br>"+df_m["QTD_Paletes"].astype(int).astype(str)+" pal",
                            textposition="top center", textfont=dict(size=13, color=cores[i%len(cores)]),
                            line=dict(width=5, color=cores[i%len(cores)]), marker=dict(size=16, symbol='diamond', line=dict(width=2,color='black')),
                            hovertemplate="<b>LOTE %{text}</b><br>Dias: %{y}<br>Val: %{x|%d/%m/%Y}<extra></extra>"
                        ))
                    fig.add_hline(y=0,line_dash="dash",line_color="red",annotation_text="VENCIDO"); fig.add_vline(x=pd.to_datetime(date.today()),line_color="black",annotation_text="HOJE")
                    fig.update_layout(title=f"VALIDADE EM LINHA - ID {id_sel} - REFORMA DE FORNOS - MATERIAIS REFRATARIOS - CLIQUE NOS PONTOS", height=600, xaxis_title="VALIDADE", yaxis_title="DIAS P/ VENCER")
                    st.plotly_chart(fig,use_container_width=True)
                    st.caption("Passe o mouse nos diamantes: mostra LOTE + PALETES + VALIDADE")
        except Exception as e:
            st.error(f"Erro dashboard: {e}")
