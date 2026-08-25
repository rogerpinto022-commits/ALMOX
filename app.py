import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao_refratario.csv"
CAPACIDADE = 1000

st.markdown("""
<style>
.main-header { background: linear-gradient(90deg, #000 0%, #1a1a1a 50%, #ff4e00 100%); padding:32px; border-radius:18px; text-align:center; border:2px solid #ff4e00; box-shadow:0 0 20px rgba(255,78,0,0.5); }
.main-header h1 { color:#fff; font-size:38px; font-weight:900; margin:0; text-shadow: 2px 2px 0 #000, 0 0 15px #ff4e00; }
.main-header h2 { color:#00ff88; font-family:monospace; background:#000; padding:6px 16px; border-radius:20px; border:1px solid #00ff88; display:inline-block; margin-top:10px; }
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

def salvar_cad():
    if st.session_state.cadastro: pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
def salvar_mov():
    if st.session_state.mov: pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)

if 'iniciado' not in st.session_state:
    c,m=carregar()
    st.session_state.cadastro=c
    st.session_state.mov=m
    st.session_state.iniciado=True

st.markdown("""
<div class="main-header">
    <h1>🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS 🔥</h1>
    <h2>1000 POSIÇÕES | EMP 1-2-3 | LOTE | VALIDADE | DASHBOARD COMPLETO COM LINHA</h2>
</div>
""", unsafe_allow_html=True)

tab1,tab2,tab3,tab4 = st.tabs(["📝 CADASTRO","🔄 MOVIMENTAÇÃO","📦 SALDO","📈 DASHBOARD - VÁRIOS GRÁFICOS"])

with tab1:
    st.success(f"📁 {len(st.session_state.cadastro)} registros gravados - NÃO APAGA SOZINHO")
    with st.form("form_cad",clear_on_submit=True):
        c1,c2,c3,c4=st.columns(4)
        with c1:
            id_p=st.text_input("ID *","01"); desc=st.text_input("DESCRIÇÃO *","BLOCO ESTRELA"); marca=st.text_input("MARCA *","ESTRELA"); lote=st.text_input("LOTE *","L001")
        with c2:
            unidade=st.selectbox("UNIDADE *",["peças","kg","m²","ton","rolos","caixas"]); emp=st.selectbox("EMPILHAMENTO *",[1,2,3]); qtd=st.number_input("QTD/Palete",value=500.0)
        with c3:
            fab=st.date_input("FABRICAÇÃO",value=date.today()); dias=st.number_input("DIAS VALIDADE",value=365); val=fab+timedelta(days=int(dias)); val_m=st.date_input("VALIDADE FINAL",value=val)
            st.info(f"Validade calculada: {val_m.strftime('%d/%m/%Y')}")
        with c4:
            st.metric(f"EMP {emp}", f"{emp} PAL = 1 POS", f"{20*emp} pal em 20 pos")
            if st.form_submit_button("💾 SALVAR E GRAVAR",type="primary",use_container_width=True):
                st.session_state.cadastro.append({"ID":id_p.upper(),"Descrição":desc.upper(),"Marca":marca.upper(),"LOTE":lote.upper(),"Unidade":unidade,"Empilhamento":int(emp),"Fabricação":str(fab),"Validade":str(val_m),"Dias_Validade":int(dias),"QTD_por_palete":qtd})
                salvar_cad(); st.success("Gravado!"); st.rerun()

    if st.session_state.cadastro:
        st.divider()
        st.markdown("#### 📋 Registros - Clique 🗑️ para EXCLUIR só aquele")
        df_cad=pd.DataFrame(st.session_state.cadastro)
        for idx in range(len(df_cad)-1,-1,-1):
            row=df_cad.iloc[idx]
            col1,col2,col3,col4,col5=st.columns([1,3,2,2,1])
            with col1: st.write(f"**{row['ID']}**")
            with col2: st.write(f"{row['Descrição']} | {row['Marca']} | L:{row['LOTE']}")
            with col3: st.write(f"Fab:{row['Fabricação']}")
            with col4: st.write(f"Val:{row['Validade']}")
            with col5:
                if st.button("🗑️",key=f"del_cad_{idx}_{row['LOTE']}_{idx}"):
                    st.session_state.cadastro.pop(idx)
                    if len(st.session_state.cadastro)==0:
                        if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
                    else: pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
                    st.rerun()

with tab2:
    if not st.session_state.cadastro: st.warning("Cadastre primeiro")
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
            if st.button("➕ LANÇAR",type="primary",use_container_width=True):
                st.session_state.mov.append({"Data":str(date.today()),"Tipo":tipo,"ID":id_s,"Descrição":prod['Descrição'],"Marca":marca_s,"LOTE":lote_s,"Unidade":prod['Unidade'],"Empilhamento":int(prod['Empilhamento']),"Fabricação":prod['Fabricação'],"Validade":prod['Validade'],"QTD_Paletes":qp if tipo=="ENTRADA" else -qp,"QTD_Unidade":qu if tipo=="ENTRADA" else -qu,"Posições":pos if tipo=="ENTRADA" else -pos})
                salvar_mov(); st.rerun()
    if st.session_state.mov:
        df_mov=pd.DataFrame(st.session_state.mov)
        for idx in range(len(df_mov)-1,-1,-1):
            row=df_mov.iloc[idx]
            c1,c2,c3,c4,c5=st.columns([1,2.5,1.5,1.5,1])
            c1.write(f"{row['Tipo']}")
            c2.write(f"{row['ID']} {row['Marca']} L:{row['LOTE']}")
            c3.write(f"{row['QTD_Paletes']} pal")
            c4.write(f"{row['QTD_Unidade']} {row['Unidade']}")
            if c5.button("🗑️",key=f"del_mov_{idx}"):
                st.session_state.mov.pop(idx)
                if len(st.session_state.mov)==0:
                    if os.path.exists(ARQ_MOV): os.remove(ARQ_MOV)
                else: pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.rerun()

with tab3:
    if st.session_state.mov:
        df=pd.DataFrame(st.session_state.mov); df["Validade_dt"]=pd.to_datetime(df["Validade"]); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Posições=("Posições","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]; saldo["Pos_Ocup"]=saldo["QTD_Paletes"]/saldo["Empilhamento"]
        total=saldo["Pos_Ocup"].sum(); taxa=total/CAPACIDADE*100
        m1,m2,m3,m4=st.columns(4)
        m1.metric("PALETES",int(saldo["QTD_Paletes"].sum())); m2.metric("OCUPADAS",f"{total:.1f}/1000",f"{taxa:.1f}%"); m3.metric("LIVRES",f"{CAPACIDADE-total:.1f}"); m4.metric("VENCIDOS",len(saldo[saldo["Dias"]<0]))
        st.progress(min(taxa/100,1.0)); st.dataframe(saldo.sort_values("Dias"),use_container_width=True)

with tab4:
    st.markdown("## 📊 DASHBOARD COMPLETO - 6 TIPOS DE GRÁFICOS")
    if not st.session_state.mov: st.warning("Faça movimentações")
    else:
        df=pd.DataFrame(st.session_state.mov)
        df["Validade_dt"]=pd.to_datetime(df["Validade"]); df["Fabricação_dt"]=pd.to_datetime(df["Fabricação"]); df["Dias"]=(df["Validade_dt"]-pd.to_datetime(date.today())).dt.days
        saldo=df.groupby(["ID","Descrição","Marca","LOTE","Unidade","Empilhamento","Fabricação","Validade","Fabricação_dt","Validade_dt"],as_index=False).agg(QTD_Paletes=("QTD_Paletes","sum"),QTD_Unidade=("QTD_Unidade","sum"),Dias=("Dias","min"))
        saldo=saldo[saldo["QTD_Paletes"]>0]; saldo["Pos_Ocup"]=saldo["QTD_Paletes"]/saldo["Empilhamento"]; saldo["Total_ID"]=saldo.groupby("ID")["QTD_Unidade"].transform("sum"); saldo["%_ID"]=(saldo["QTD_Unidade"]/saldo["Total_ID"]*100).round(1)
        id_sel=st.selectbox("SELECIONE ID",sorted(saldo["ID"].unique())); df_f=saldo[saldo["ID"]==id_sel].sort_values("Validade_dt")

        # LINHA 1 - 2 GRAFICOS
        c1,c2=st.columns(2)
        with c1:
            st.markdown("#### 1️⃣ ESTOQUE POR ID - % PIZZA")
            fig1=px.pie(df_f,values="QTD_Unidade",names="Marca",color="LOTE",hole=0.5,title=f"% por Marca - ID {id_sel}",hover_data=["LOTE","%_ID","Dias"])
            st.plotly_chart(fig1,use_container_width=True)
        with c2:
            st.markdown("#### 2️⃣ QTD POR MARCA - BARRA")
            fig2=px.bar(df_f,x="Marca",y="QTD_Unidade",color="LOTE",barmode="stack",text="QTD_Paletes",title="QTD por Marca e Lote")
            st.plotly_chart(fig2,use_container_width=True)

        st.divider()

        # GRAFICO PRINCIPAL DE VALIDADE EM LINHA
        st.markdown("#### 3️⃣ 🔥 PRINCIPAL - VALIDADE EM LINHA (FABRICAÇÃO -> VALIDADE)")
        fig_linha = go.Figure()
        for marca in df_f["Marca"].unique():
            df_m = df_f[df_f["Marca"]==marca].sort_values("Validade_dt")
            fig_linha.add_trace(go.Scatter(
                x=df_m["Validade_dt"], y=df_m["Dias"],
                mode='lines+markers+text',
                name=f"{marca}",
                text=df_m["LOTE"],
                textposition="top center",
                line=dict(width=4),
                marker=dict(size=12, symbol='diamond'),
                hovertemplate="<b>LOTE %{text}</b><br>Marca: "+marca+"<br>Validade: %{x}<br>Dias p/ vencer: %{y}<br>Paletes: %{customdata}<extra></extra>",
                customdata=df_m["QTD_Paletes"]
            ))
        fig_linha.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="VENCIDO")
        fig_linha.add_hline(y=30, line_dash="dot", line_color="orange", annotation_text="30 DIAS")
        fig_linha.add_vline(x=pd.to_datetime(date.today()), line_dash="dash", line_color="black", annotation_text="HOJE")
        fig_linha.update_layout(title=f"LINHA DE VALIDADE - ID {id_sel} - Quanto menor, vence antes (FIFO)", xaxis_title="Data Validade", yaxis_title="Dias para Vencer", height=500)
        st.plotly_chart(fig_linha,use_container_width=True)

        # SEGUNDO GRAFICO DE LINHA - TIMELINE FAB -> VAL
        st.markdown("#### 3B️⃣ TIMELINE FAB -> VAL - LINHA DO TEMPO")
        fig_timeline = px.line(df_f, x="Validade_dt", y="QTD_Paletes", color="Marca", markers=True, line_shape="spline", title="Evolução Paletes por Validade")
        fig_timeline.add_vline(x=pd.to_datetime(date.today()), line_color="red", annotation_text="HOJE")
        st.plotly_chart(fig_timeline,use_container_width=True)

        c3,c4=st.columns(2)
        with c3:
            st.markdown("#### 4️⃣ SCATTER FAB x VAL")
            fig_sc=px.scatter(df_f, x="Fabricação_dt", y="Validade_dt", size="QTD_Paletes", color="LOTE", hover_data=["Marca","Dias"], title="Fabricação vs Validade")
            st.plotly_chart(fig_sc,use_container_width=True)
        with c4:
            st.markdown("#### 5️⃣ OCUPAÇÃO CHÃO - PIZZA")
            total_pos=saldo["Pos_Ocup"].sum()
            df_occ=pd.DataFrame({"Status":["OCUPADO","LIVRE"],"Pos":[total_pos,CAPACIDADE-total_pos]})
            fig_occ=px.pie(df_occ,values="Pos",names="Status",hole=0.6,title=f"Ocupação {total_pos:.0f}/1000 ({total_pos/10:.1f}%)",color_discrete_map={"OCUPADO":"#ff4e00","LIVRE":"#00e676"})
            st.plotly_chart(fig_occ,use_container_width=True)

        st.markdown("#### 6️⃣ BARRA POSIÇÕES POR ID")
        df_pos=saldo.groupby("ID",as_index=False).agg(Pos_Ocup=("Pos_Ocup","sum"),QTD_Paletes=("QTD_Paletes","sum"))
        fig_bar_pos=px.bar(df_pos,x="ID",y="Pos_Ocup",color="ID",text="QTD_Paletes",title="Posições ocupadas por ID")
        st.plotly_chart(fig_bar_pos,use_container_width=True)

        st.markdown("#### 7️⃣ AREA - ESTOQUE ACUMULADO POR VALIDADE")
        df_area=df_f.sort_values("Validade_dt")
        fig_area=px.area(df_area,x="Validade_dt",y="QTD_Unidade",color="Marca",title="Área - QTD por Validade")
        st.plotly_chart(fig_area,use_container_width=True)
