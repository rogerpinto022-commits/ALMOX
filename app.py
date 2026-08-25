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
.main-header { background: radial-gradient(circle at top, #222, #000); padding:30px; border-radius:20px; text-align:center; border:3px solid #ff4e00; box-shadow:0 0 15px #ff4e00; }
.main-header h1 { color:#fff; font-size:40px; font-weight:900; margin:0; text-shadow:0 0 10px #ff4e00, 3px 3px 0 #000; }
.main-header h2 { color:#00ff88; font-family:monospace; background:#000; padding:6px 18px; border-radius:20px; border:1px solid #00ff88; }
.metric-box { background:#111; padding:18px; border-radius:14px; text-align:center; border:2px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- PERSISTÊNCIA BLINDADA - NÃO APAGA SOZINHO ---
def carregar():
    c,m=[],[]
    if os.path.exists(ARQ_CAD):
        try: c=pd.read_csv(ARQ_CAD).to_dict('records')
        except: c=[]
    if os.path.exists(ARQ_MOV):
        try: m=pd.read_csv(ARQ_MOV).to_dict('records')
        except: m=[]
    return c,m

def salvar_cad():
    if st.session_state.cadastro: # SÓ SALVA SE TIVER DADO, NUNCA SALVA VAZIO POR CIMA
        pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)

def salvar_mov():
    if st.session_state.mov:
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)

if 'iniciado' not in st.session_state:
    c,m=carregar()
    st.session_state.cadastro=c
    st.session_state.mov=m
    st.session_state.iniciado=True

st.markdown("""
<div class="main-header">
    <h1>🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS 🔥</h1>
    <h2>✅ DADOS GRAVADOS - NÃO APAGA SOZINHO | BOTÃO EXCLUIR POR REGISTRO</h2>
</div>
""", unsafe_allow_html=True)

tab1,tab2,tab3,tab4 = st.tabs(["📝 CADASTRO","🔄 MOVIMENTAÇÃO","📦 SALDO","📈 DASHBOARD 4 GRÁFICOS"])

with tab1:
    st.markdown(f"**📁 Arquivo gravado:** {ARQ_CAD} | **{len(st.session_state.cadastro)} registros salvos - NÃO SERÁ APAGADO**")

    with st.form("form_cad",clear_on_submit=True):
        c1,c2,c3,c4=st.columns(4)
        with c1:
            id_p=st.text_input("ID *","01"); desc=st.text_input("DESCRIÇÃO *","BLOCO"); marca=st.text_input("MARCA *","ESTRELA"); lote=st.text_input("LOTE *","L001")
        with c2:
            unidade=st.selectbox("UNIDADE *",["peças","kg","m²","ton"]); emp=st.selectbox("EMP *",[1,2,3]); qtd=st.number_input("QTD/Pal",value=500.0)
        with c3:
            fab=st.date_input("FAB",value=date.today()); dias=st.number_input("DIAS VAL",value=365); val=fab+timedelta(days=int(dias)); val_m=st.date_input("Validade",value=val)
        with c4:
            if st.form_submit_button("💾 SALVAR NOVO REGISTRO",type="primary",use_container_width=True):
                novo={"ID":id_p.upper(),"Descrição":desc.upper(),"Marca":marca.upper(),"LOTE":lote.upper(),"Unidade":unidade,"Empilhamento":int(emp),"Fabricação":str(fab),"Validade":str(val_m),"Dias_Validade":int(dias),"QTD_por_palete":qtd}
                st.session_state.cadastro.append(novo)
                salvar_cad()
                st.success(f"✅ Registro {id_p} - {marca} - Lote {lote} GRAVADO e não será apagado!")
                st.rerun()

    if st.session_state.cadastro:
        st.divider()
        st.markdown("### 📋 SEUS REGISTROS SALVOS - Botão EXCLUIR em cada linha")
        st.caption("⚠️ Só apaga se você clicar no 🗑️ EXCLUIR REGISTRO daquela linha")

        df_cad = pd.DataFrame(st.session_state.cadastro)
        for idx in range(len(df_cad)-1, -1, -1): # de trás pra frente pra não bugar índice
            row = df_cad.iloc[idx]
            col1,col2,col3,col4,col5 = st.columns([1.5,3,2,1])
            with col1: st.write(f"**{row['ID']}**")
            with col2: st.write(f"{row['Descrição']} | **{row['Marca']}** | Lote: **{row['LOTE']}**")
            with col3: st.write(f"Emp: {row['Empilhamento']} | {row['Unidade']} | Fab: {row['Fabricação']}")
            with col4: st.write(f"Val: **{row['Validade']}** | {row['QTD_por_palete']}/pal")
            with col5:
                if st.button(f"🗑️ EXCLUIR", key=f"del_cad_{idx}_{row['LOTE']}", type="primary"):
                    # EXCLUI SÓ ESSE REGISTRO
                    st.session_state.cadastro.pop(idx)
                    if len(st.session_state.cadastro)==0:
                        if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
                    else:
                        pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
                    st.warning(f"Registro {row['ID']} {row['LOTE']} excluído!")
                    st.rerun()
        st.divider()
        st.dataframe(df_cad, use_container_width=True)

with tab2:
    if not st.session_state.cadastro:
        st.warning("Cadastre primeiro")
    else:
        df_cad=pd.DataFrame(st.session_state.cadastro)
        ca,cb=st.columns([1,1.5])
        with ca:
            tipo=st.radio("TIPO",["ENTRADA","SAÍDA"],horizontal=True)
            id_s=st.selectbox("ID",sorted(df_cad["ID"].unique()))
            marca_s=st.selectbox("MARCA",df_cad[df_cad["ID"]==id_s]["Marca"].unique())
            df_f=df_cad[(df_cad["ID"]==id_s)&(df_cad["Marca"]==marca_s)]
            lote_s=st.selectbox("LOTE",df_f["LOTE"].unique()); prod=df_f[df_f["LOTE"]==lote_s].iloc[-1]
        with cb:
            qp=st.number_input("QTD PALETES",value=20,min_value=1); qu=st.number_input("QTD UNIDADE",value=float(prod['QTD_por_palete']*qp))
            pos=qp/int(prod['Empilhamento']); st.metric("POSIÇÕES CHÃO",f"{pos:.1f}")
            if st.button("➕ LANÇAR MOVIMENTAÇÃO",type="primary",use_container_width=True):
                st.session_state.mov.append({"Data":str(date.today()),"Tipo":tipo,"ID":id_s,"Descrição":prod['Descrição'],"Marca":marca_s,"LOTE":lote_s,"Unidade":prod['Unidade'],"Empilhamento":int(prod['Empilhamento']),"Fabricação":prod['Fabricação'],"Validade":prod['Validade'],"QTD_Paletes":qp if tipo=="ENTRADA" else -qp,"QTD_Unidade":qu if tipo=="ENTRADA" else -qu,"Posições":pos if tipo=="ENTRADA" else -pos})
                salvar_mov(); st.success("Movimentação gravada!"); st.rerun()

    if st.session_state.mov:
        st.markdown("### 📋 Movimentações - Botão EXCLUIR por registro")
        df_mov=pd.DataFrame(st.session_state.mov)
        for idx in range(len(df_mov)-1, -1, -1):
            row=df_mov.iloc[idx]
            c1,c2,c3,c4,c5=st.columns([1,2.5,1.5,1.5,1])
            c1.write(f"{row['Data']} {row['Tipo']}")
            c2.write(f"{row['ID']} {row['Marca']} L:{row['LOTE']}")
            c3.write(f"{row['QTD_Paletes']} pal | {row['Posições']:.1f} pos")
            c4.write(f"{row['QTD_Unidade']} {row['Unidade']}")
            if c5.button(f"🗑️ EXCLUIR", key=f"del_mov_{idx}_{row['LOTE']}_{row['Data']}"):
                st.session_state.mov.pop(idx)
                if len(st.session_state.mov)==0:
                    if os.path.exists(ARQ_MOV): os.remove(ARQ_MOV)
                else:
                    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.rerun()

with tab3:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"]); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Posições=("Posições","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]; saldo["Pos_Ocup"]=saldo["QTD_Paletes"]/saldo["Empilhamento"]
        total=saldo["Pos_Ocup"].sum(); st.metric("OCUPAÇÃO CHÃO",f"{total:.1f} / 1000 posições ({total/10:.1f}%)"); st.progress(min(total/1000,1.0))
        st.dataframe(saldo,use_container_width=True)

with tab4:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"]); df["Fabricação_dt"]=pd.to_datetime(df["Fabricação"]); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade","Fabricação_dt","Validade_dt"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]; saldo["Pos_Ocup"]=saldo["QTD_Paletes"]/saldo["Empilhamento"]; saldo["Total_ID"]=saldo.groupby("ID")["QTD_Unidade"].transform("sum"); saldo["%_ID"]=(saldo["QTD_Unidade"]/saldo["Total_ID"]*100).round(1)
        id_sel=st.selectbox("ID MATERIAL",sorted(saldo["ID"].unique())); df_f=saldo[saldo["ID"]==id_sel]
        g1,g2=st.columns(2)
        with g1:
            st.markdown("#### 1️⃣ QTD ESTOQUE POR ID %")
            st.plotly_chart(px.pie(df_f,values="QTD_Unidade",names="Marca",color="LOTE",hole=0.45,title=f"% por Marca - {id_sel}"),use_container_width=True)
        with g2:
            st.markdown("#### 2️⃣ QTD POR MARCA")
            st.plotly_chart(px.bar(df_f,x="Marca",y="QTD_Unidade",color="LOTE",barmode="stack",text="QTD_Paletes",title="QTD por Marca"),use_container_width=True)
        st.markdown("#### 3️⃣ FABRICAÇÃO -> VALIDADE")
        fig3=px.scatter(df_f,x="Validade_dt",y="Marca",size="QTD_Paletes",color="LOTE",hover_data=["Fabricação","Dias"])
        fig3.add_vline(x=pd.to_datetime(date.today()),line_dash="dash",line_color="red",annotation_text="HOJE")
        st.plotly_chart(fig3,use_container_width=True)
        g3,g4=st.columns(2)
        with g3: st.plotly_chart(px.bar(df_f.sort_values("Dias"),x="LOTE",y="Dias",color="Marca",title="Dias para vencer - FIFO"),use_container_width=True)
        with g4:
            total_pos=saldo["Pos_Ocup"].sum()
            df_occ=pd.DataFrame({"Status":["OCUPADO","LIVRE"],"Pos":[total_pos,1000-total_pos]})
            st.plotly_chart(px.pie(df_occ,values="Pos",names="Status",hole=0.6,title=f"Ocupação {total_pos:.0f}/1000"),use_container_width=True)
