import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="Almox V4 Final", layout="wide")
FUSO = ZoneInfo("America/Sao_Paulo")
ARQ_DADOS = "dados.csv"
ARQ_MOV = "mov.csv"
ARQ_EMAILS = "emails.csv"

st.markdown("""
<style>
.vencido {background:#ff0000; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold}
.a30 {background:#ff9800; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold}
.a90 {background:#ffcc00; color:black; padding:12px; border-radius:10px; text-align:center; font-weight:bold}
.ok {background:#00c853; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold}
</style>
""", unsafe_allow_html=True)

# PRESERVA TUDO - NAO APAGA
if not os.path.exists(ARQ_DADOS):
    pd.DataFrame([{"ID":1,"NOME":"CIMENTO","UNIDADE":"SC","MARCA":"VOTORAN","LOCAL":"BARRACAO","SALDO":0,"VALIDADE_PADRAO":90,"FORNECEDOR":"LEROY"}]).to_csv(ARQ_DADOS,index=False)
if not os.path.exists(ARQ_MOV):
    pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","MARCA","FORNECEDOR","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin"}]).to_csv(ARQ_EMAILS,index=False)

if "logado" not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.title("Login")
    e=st.text_input("Email").lower().strip()
    s=st.text_input("Senha",type="password")
    if st.button("Entrar"):
        df_e=pd.read_csv(ARQ_EMAILS)
        if not df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"]==s)].empty:
            st.session_state.logado=True; st.session_state.usuario=e
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records') if not pd.read_csv(ARQ_MOV).empty else []
            st.rerun()
    st.stop()

agora=datetime.now(FUSO); hoje=date.today()
if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()
for d in st.session_state.dados:
    try: d["SALDO"]=float(d["SALDO"])
    except: d["SALDO"]=0.0

tab1, tab2, tab3, tab4 = st.tabs(["📦 ESTOQUE", "📝 LANÇAR", "🔍 ANALISE POR MATERIAL", "✏️ EDITAR/EXCLUIR"])

with tab1:
    st.subheader("🔒 Backup - Seus lançamentos já feitos")
    b1,b2=st.columns(2)
    with b1:
        if os.path.exists(ARQ_DADOS):
            with open(ARQ_DADOS,"rb") as f: st.download_button("⬇️ BAIXAR dados.csv", f, "backup_dados.csv")
    with b2:
        if os.path.exists(ARQ_MOV):
            with open(ARQ_MOV,"rb") as f: st.download_button("⬇️ BAIXAR mov.csv", f, "backup_mov.csv")
    st.divider()
    df_est=pd.DataFrame(st.session_state.dados)
    pivot=df_est.pivot_table(index=["ID","NOME","UNIDADE"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index() if not df_est.empty else pd.DataFrame()
    if not pivot.empty:
        for c in ["BARRACAO","OFICINA"]:
            if c not in pivot.columns: pivot[c]=0
        pivot["TOTAL"]=pivot["BARRACAO"]+pivot["OFICINA"]
        st.metric("TOTAL GERAL", f"{pivot['TOTAL'].sum():.0f}")
        st.dataframe(pivot.sort_values("ID"), use_container_width=True)
        tipo_graf=st.selectbox("Tipo Grafico", ["Barra","Pizza","Linha"])
        if tipo_graf=="Barra": st.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACAO","OFICINA"], barmode="group", text_auto=True), use_container_width=True)
        elif tipo_graf=="Pizza": st.plotly_chart(px.pie(pivot, names="NOME", values="TOTAL", hole=0.3), use_container_width=True)
        else: st.plotly_chart(px.line(pivot, x="NOME", y="TOTAL", markers=True), use_container_width=True)

with tab2:
    st.header("Lançamento - Todos os campos")
    ids=sorted(list(set([int(d["ID"]) for d in st.session_state.dados]))) if st.session_state.dados else [1]
    mapa={int(d["ID"]):(d["NOME"],d["UNIDADE"],int(d.get("VALIDADE_PADRAO",90)),d.get("MARCA",""),d.get("FORNECEDOR","")) for d in st.session_state.dados}
    id_sel=st.selectbox("MATERIAL", ids, format_func=lambda x: f"{x} - {mapa.get(x,('NOVO','SC',90,'',''))[0]}")
    cA,cB,cC,cD,cE=st.columns(5)
    marca=cA.text_input("MARCA", value=mapa.get(id_sel,("","",""))[3])
    fornecedor=cB.text_input("FORNECEDOR *", value=mapa.get(id_sel,("","","","",""))[4])
    lote=cC.text_input("LOTE *")
    unidade=cD.text_input("UNIDADE *", value=mapa.get(id_sel,("","SC",90,"",""))[1])
    obs=cE.text_input("OBS/NF")
    c1,c2,c3,c4,c5,c6=st.columns(6)
    local_sel=c1.selectbox("LOCAL *", ["BARRACAO","OFICINA"])
    data_fab=c2.date_input("FAB *", value=hoje)
    validade=c3.date_input("VAL *", value=data_fab+timedelta(days=mapa.get(id_sel,("","SC",90,"",""))[2]))
    qtd_palete=c4.number_input("QTD POR PALETE", value=1.0)
    entrada=c5.number_input("QTD ENTR/SAIDA", value=1.0)
    tipo=c6.selectbox("TIPO", ["Entrada","Saida"])
    total=qtd_palete*entrada
    dias_rest=(validade-hoje).days
    status="VENCIDO" if dias_rest<0 else "A VENCER 30d" if dias_rest<=30 else "A VENCER 90d" if dias_rest<=90 else "OK"
    if status=="VENCIDO": st.markdown(f'<div class="vencido">⛔ VENCIDO {dias_rest} dias - {total} {unidade}</div>', unsafe_allow_html=True)
    elif status=="A VENCER 30d": st.markdown(f'<div class="a30">⚠️ {dias_rest} dias - 30d</div>', unsafe_allow_html=True)
    elif status=="A VENCER 90d": st.markdown(f'<div class="a90">⚠️ {dias_rest} dias - 90d</div>', unsafe_allow_html=True)
    else: st.markdown(f'<div class="ok">✅ {dias_rest} dias - OK</div>', unsafe_allow_html=True)
    if st.button("SALVAR", type="primary", use_container_width=True):
        idx_ba=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==id_sel and d["LOCAL"]=="BARRACAO"),None)
        idx_of=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==id_sel and d["LOCAL"]=="OFICINA"),None)
        if idx_ba is None:
            st.session_state.dados.append({"ID":id_sel,"NOME":mapa.get(id_sel,(f"MAT {id_sel}",unidade,90,marca,fornecedor))[0],"UNIDADE":unidade.upper(),"MARCA":marca.upper(),"LOCAL":"BARRACAO","SALDO":0.0,"VALIDADE_PADRAO":(validade-data_fab).days,"FORNECEDOR":fornecedor.upper()})
            idx_ba=len(st.session_state.dados)-1
        if idx_of is None:
            st.session_state.dados.append({"ID":id_sel,"NOME":mapa.get(id_sel,(f"MAT {id_sel}",unidade,90,marca,fornecedor))[0],"UNIDADE":unidade.upper(),"MARCA":marca.upper(),"LOCAL":"OFICINA","SALDO":0.0,"VALIDADE_PADRAO":(validade-data_fab).days,"FORNECEDOR":fornecedor.upper()})
            idx_of=len(st.session_state.dados)-1
        if tipo=="Entrada":
            if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]+=total
            else: st.session_state.dados[idx_of]["SALDO"]+=total
        else:
            if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]-=total
            else: st.session_state.dados[idx_of]["SALDO"]-=total
        novo_id=max([int(m.get("IDX",0)) for m in st.session_state.mov])+1 if st.session_state.mov else 1
        st.session_state.mov.append({"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M:%S"),"DATA_FAB":data_fab.strftime("%d/%m/%Y"),"VALIDADE":validade.strftime("%d/%m/%Y"),"DIAS_VALIDADE":(validade-data_fab).days,"STATUS_VAL":status,"LOTE":lote.upper(),"MARCA":marca.upper(),"FORNECEDOR":fornecedor.upper(),"QTD_PALETE":qtd_palete,"ENTRADA":entrada,"TOTAL":total,"UNIDADE":unidade.upper(),"LOCAL":local_sel,"TIPO":tipo,"ID_MAT":id_sel,"NOME_MAT":mapa.get(id_sel,(f"MAT {id_sel}",unidade,90,marca,fornecedor))[0],"RESPONSAVEL":st.session_state.usuario,"OBS":obs.upper()})
        pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
        st.success("Salvo!"); st.rerun()

with tab3:
    st.header("Clique no material - mostra vencido x prazo com números")
    if not st.session_state.mov:
        st.warning("Sem movimentos")
    else:
        df_mov=pd.DataFrame(st.session_state.mov)
        df_mov["VAL_DT"]=pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
        df_mov["DIAS_REST"]=(df_mov["VAL_DT"]-pd.Timestamp(hoje)).dt.days
        df_mov["STATUS_ATUAL"]=df_mov["DIAS_REST"].apply(lambda d: "VENCIDO" if d<0 else "A VENCER 30d" if d<=30 else "A VENCER 90d" if d<=90 else "OK")
        lista=sorted(df_mov["NOME_MAT"].unique())
        mat_click=st.selectbox("SELECIONE MATERIAL", lista)
        df_mat=df_mov[df_mov["NOME_MAT"]==mat_click]
        c1,c2,c3,c4=st.columns(4)
        c1.metric("VENCIDO", f"{df_mat[df_mat['STATUS_ATUAL']=='VENCIDO']['TOTAL'].sum():.0f} {df_mat['UNIDADE'].iloc[0] if not df_mat.empty else ''}")
        c2.metric("A VENCER 30d", f"{df_mat[df_mat['STATUS_ATUAL']=='A VENCER 30d']['TOTAL'].sum():.0f}")
        c3.metric("A VENCER 90d", f"{df_mat[df_mat['STATUS_ATUAL']=='A VENCER 90d']['TOTAL'].sum():.0f}")
        c4.metric("OK PRAZO", f"{df_mat[df_mat['STATUS_ATUAL']=='OK']['TOTAL'].sum():.0f}")
        tipo_g=st.radio("Tipo grafico", ["Pizza","Barra","Linha"], horizontal=True)
        df_status=df_mat.groupby("STATUS_ATUAL")["TOTAL"].sum().reset_index()
        if tipo_g=="Pizza":
            st.plotly_chart(px.pie(df_status, names="STATUS_ATUAL", values="TOTAL", color="STATUS_ATUAL", color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}, hole=0.4, title=f"{mat_click}"), use_container_width=True)
        elif tipo_g=="Barra":
            st.plotly_chart(px.bar(df_status, x="STATUS_ATUAL", y="TOTAL", color="STATUS_ATUAL", text_auto=True, color_discrete_map={"VENCIDO":"red","A VENCER 30d":"orange","A VENCER 90d":"gold","OK":"green"}), use_container_width=True)
        else:
            st.plotly_chart(px.line(df_mat.sort_values("VAL_DT"), x="VAL_DT", y="TOTAL", color="STATUS_ATUAL", markers=True), use_container_width=True)
        st.dataframe(df_mat.sort_values("VAL_DT")[["IDX","LOTE","FORNECEDOR","MARCA","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","TOTAL","UNIDADE","LOCAL","TIPO"]], use_container_width=True)

with tab4:
    st.header("Editar / Excluir - só se quiser")
    if not st.session_state.mov:
        st.warning("Sem registros")
    else:
        df_mov=pd.DataFrame(st.session_state.mov).sort_values("IDX", ascending=False)
        st.dataframe(df_mov[["IDX","DATA_HORA","NOME_MAT","LOTE","VALIDADE","STATUS_VAL","TOTAL","UNIDADE","TIPO","LOCAL"]], use_container_width=True)
        idx_ed=st.number_input("Digite IDX", min_value=1, step=1)
        reg=next((m for m in st.session_state.mov if int(m["IDX"])==idx_ed), None)
        if reg:
            st.json(reg)
            if st.button(f"🗑️ EXCLUIR IDX {idx_ed} - reverte estoque", type="primary"):
                idm=int(reg["ID_MAT"]); tot=float(reg["TOTAL"]); loc=reg["LOCAL"]; tip=reg["TIPO"]
                idx_ba=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==idm and d["LOCAL"]=="BARRACAO"),None)
                idx_of=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==idm and d["LOCAL"]=="OFICINA"),None)
                if tip=="Entrada":
                    if loc=="BARRACAO" and idx_ba is not None: st.session_state.dados[idx_ba]["SALDO"]-=tot
                    if loc=="OFICINA" and idx_of is not None: st.session_state.dados[idx_of]["SALDO"]-=tot
                else:
                    if loc=="BARRACAO" and idx_ba is not None: st.session_state.dados[idx_ba]["SALDO"]+=tot
                    if loc=="OFICINA" and idx_of is not None: st.session_state.dados[idx_of]["SALDO"]+=tot
                st.session_state.mov=[m for m in st.session_state.mov if int(m["IDX"])!=idx_ed]
                pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False)
                pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success("Excluído e revertido"); st.rerun()
