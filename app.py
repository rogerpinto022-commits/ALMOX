import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import os

st.set_page_config(page_title="REFORMA DE FORNOS - MATERIAIS REFRATARIOS", layout="wide", page_icon="🔥")

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
h1 {color:#ff4500}
</style>
""", unsafe_allow_html=True)

if not os.path.exists(ARQ_DADOS):
    pd.DataFrame([{"ID":1,"NOME":"TIJOLO REFRATARIO","UNIDADE":"PC","MARCA":"MORGAN","LOCAL":"BARRACAO","SALDO":0,"VALIDADE_PADRAO":365,"FORNECEDOR":"REFRATARIOS BRASIL"}]).to_csv(ARQ_DADOS,index=False)
if not os.path.exists(ARQ_MOV):
    pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","MARCA","FORNECEDOR","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","NIVEL":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)

if "logado" not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center;'>🔥 REFORMA DE FORNOS<br>MATERIAIS REFRATÁRIOS 🔥</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>Controle de Almoxarifado</h3>", unsafe_allow_html=True)
    e=st.text_input("Email").lower().strip()
    s=st.text_input("Senha",type="password")
    if st.button("Entrar", type="primary", use_container_width=True):
        df_e=pd.read_csv(ARQ_EMAILS)
        df_e["EMAIL"]=df_e["EMAIL"].astype(str).str.lower().str.strip()
        if not df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"].astype(str)==s)].empty:
            st.session_state.logado=True; st.session_state.usuario=e
            st.session_state.nivel=df_e[(df_e["EMAIL"]==e)]["NIVEL"].iloc[0] if "NIVEL" in df_e.columns else "ADMIN"
            st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
            st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records') if not pd.read_csv(ARQ_MOV).empty else []
            st.rerun()
        else: st.error("Email/senha inválido")
    st.stop()

agora=datetime.now(FUSO); hoje=date.today()
st.markdown("<h1 style='text-align:center;'>🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS 🔥</h1>", unsafe_allow_html=True)

st.sidebar.write(f"Logado: {st.session_state.usuario} - {st.session_state.get('nivel','')}")
if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()
for d in st.session_state.dados:
    try: d["SALDO"]=float(d["SALDO"])
    except: d["SALDO"]=0.0

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 ESTOQUE", "📝 LANÇAR", "🔍 BOTÕES MATERIAL", "✏️ EDITAR/EXCLUIR", "🔑 PERMISSÕES"])

with tab1:
    b1,b2=st.columns(2)
    with b1:
        if os.path.exists(ARQ_DADOS):
            with open(ARQ_DADOS,"rb") as f: st.download_button("⬇️ BACKUP dados.csv", f, "backup_dados.csv")
    with b2:
        if os.path.exists(ARQ_MOV):
            with open(ARQ_MOV,"rb") as f: st.download_button("⬇️ BACKUP mov.csv", f, "backup_mov.csv")
    df_est=pd.DataFrame(st.session_state.dados)
    pivot=df_est.pivot_table(index=["ID","NOME","UNIDADE"], columns="LOCAL", values="SALDO", aggfunc="sum", fill_value=0).reset_index() if not df_est.empty else pd.DataFrame()
    if not pivot.empty:
        for c in ["BARRACAO","OFICINA"]:
            if c not in pivot.columns: pivot[c]=0
        pivot["TOTAL"]=pivot["BARRACAO"]+pivot["OFICINA"]
        st.metric("TOTAL GERAL REFRATÁRIOS", f"{pivot['TOTAL'].sum():.0f}")
        st.dataframe(pivot.sort_values("ID"), use_container_width=True)
        tipo_graf=st.selectbox("Tipo Grafico", ["Barra","Pizza","Linha"], key="graf1")
        if tipo_graf=="Barra": st.plotly_chart(px.bar(pivot, x="NOME", y=["BARRACAO","OFICINA"], barmode="group", text_auto=True), use_container_width=True)
        elif tipo_graf=="Pizza": st.plotly_chart(px.pie(pivot, names="NOME", values="TOTAL", hole=0.3), use_container_width=True)
        else: st.plotly_chart(px.line(pivot, x="NOME", y="TOTAL", markers=True), use_container_width=True)

with tab2:
    ids=sorted(list(set([int(d["ID"]) for d in st.session_state.dados]))) if st.session_state.dados else [1]
    mapa={int(d["ID"]):(d["NOME"],d["UNIDADE"],int(d.get("VALIDADE_PADRAO",90)),d.get("MARCA",""),d.get("FORNECEDOR","")) for d in st.session_state.dados}
    id_sel=st.selectbox("MATERIAL REFRATÁRIO", ids, format_func=lambda x: f"{x} - {mapa.get(x,('NOVO','SC',90,'',''))[0]}")
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
    elif status=="A VENCER 30d": st.markdown(f'<div class="a30">⚠️ {dias_rest} dias</div>', unsafe_allow_html=True)
    elif status=="A VENCER 90d": st.markdown(f'<div class="a90">⚠️ {dias_rest} dias</div>', unsafe_allow_html=True)
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
    st.header("🔍 Clique no botão")
    if not st.session_state.mov:
        st.warning("Sem movimentos")
    else:
        df_mov=pd.DataFrame(st.session_state.mov)
        df_mov["VAL_DT"]=pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
        df_mov["DIAS_REST"]=(df_mov["VAL_DT"]-pd.Timestamp(hoje)).dt.days
        df_mov["STATUS_ATUAL"]=df_mov["DIAS_REST"].apply(lambda d: "VENCIDO" if d<0 else "A VENCER 30d" if d<=30 else "A VENCER 90d" if d<=90 else "OK")
        lista=sorted(df_mov["NOME_MAT"].unique())
        if "mat_selecionado" not in st.session_state:
            st.session_state.mat_selecionado = lista[0] if lista else None
        cols = st.columns(4)
        for i, nome in enumerate(lista):
            col = cols[i % 4]
            total_nome = df_mov[df_mov["NOME_MAT"]==nome]["TOTAL"].sum()
            venc_nome = df_mov[(df_mov["NOME_MAT"]==nome) & (df_mov["STATUS_ATUAL"]=="VENCIDO")]["TOTAL"].sum()
            cor = "🔴" if venc_nome>0 else "🟢"
            if col.button(f"{cor} {nome} - {total_nome:.0f}", key=f"btn_{nome}", use_container_width=True):
                st.session_state.mat_selecionado = nome
        mat_click = st.session_state.mat_selecionado
        st.divider()
        st.subheader(f"📦 {mat_click}")
        df_mat=df_mov[df_mov["NOME_MAT"]==mat_click]
        unid=df_mat["UNIDADE"].iloc[0] if not df_mat.empty else "UN"
        venc=df_mat[df_mat["STATUS_ATUAL"]=="VENCIDO"]["TOTAL"].sum()
        a30=df_mat[df_mat["STATUS_ATUAL"]=="A VENCER 30d"]["TOTAL"].sum()
        a90=df_mat[df_mat["STATUS_ATUAL"]=="A VENCER 90d"]["TOTAL"].sum()
        ok=df_mat[df_mat["STATUS_ATUAL"]=="OK"]["TOTAL"].sum()
        total_mat=venc+a30+a90+ok
        c1,c2,c3,c4,c5=st.columns(5)
        c1.button(f"⛔ VENCIDO\n{venc:.0f} {unid}", key="card_v", use_container_width=True)
        c2.button(f"⚠️ 30d\n{a30:.0f}", key="card_30", use_container_width=True)
        c3.button(f"⚠️ 90d\n{a90:.0f}", key="card_90", use_container_width=True)
        c4.button(f"✅ OK\n{ok:.0f}", key="card_ok", use_container_width=True)
        c5.button(f"📦 TOTAL\n{total_mat:.0f}", key="card_total", use_container_width=True)
        tipo_g=st.segmented_control("Grafico", ["Pizza","Barra","Linha"], default="Barra", key="graf_mat")
        df_status=df_mat.groupby("STATUS_ATUAL")["TOTAL"].sum().reset_index()
        if tipo_g=="Pizza":
            fig=px.pie(df_status, names="STATUS_ATUAL", values="TOTAL", color="STATUS_ATUAL", color_discrete_map={"VENCIDO":"#ff0000","A VENCER 30d":"#ff9800","A VENCER 90d":"#ffcc00","OK":"#00c853"})
            fig.update_traces(textposition='inside', textinfo='value+percent+label', textfont_size=16)
            st.plotly_chart(fig, use_container_width=True)
        elif tipo_g=="Barra":
            fig=px.bar(df_status, x="STATUS_ATUAL", y="TOTAL", color="STATUS_ATUAL", text="TOTAL", color_discrete_map={"VENCIDO":"#ff0000","A VENCER 30d":"#ff9800","A VENCER 90d":"#ffcc00","OK":"#00c853"})
            fig.update_traces(texttemplate='%{text:.0f} '+unid, textposition='outside', textfont_size=18)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig=px.line(df_mat.sort_values("VAL_DT"), x="VAL_DT", y="TOTAL", color="STATUS_ATUAL", markers=True, text="TOTAL")
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    df_mov=pd.DataFrame(st.session_state.mov).sort_values("IDX", ascending=False) if st.session_state.mov else pd.DataFrame()
    if not df_mov.empty:
        st.dataframe(df_mov[["IDX","DATA_HORA","NOME_MAT","LOTE","VALIDADE","STATUS_VAL","TOTAL","UNIDADE","TIPO"]], use_container_width=True)
        idx_ed=st.number_input("IDX", min_value=1, step=1)
        reg=next((m for m in st.session_state.mov if int(m["IDX"])==idx_ed), None)
        if reg and st.button(f"🗑️ EXCLUIR IDX {idx_ed}", type="primary"):
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
            st.success("Excluído"); st.rerun()

with tab5:
    st.header("🔑 Gerar Permissões de Acesso")
    df_emails=pd.read_csv(ARQ_EMAILS)
    st.dataframe(df_emails, use_container_width=True)
    st.divider()
    c1,c2,c3=st.columns(3)
    novo_email=c1.text_input("Email novo *").lower().strip()
    nova_senha=c2.text_input("Senha *")
    novo_nivel=c3.selectbox("Nível", ["ADMIN","USUARIO","VISUALIZACAO"])
    if st.button("✅ GERAR PERMISSÃO", type="primary", use_container_width=True):
        if not novo_email or not nova_senha:
            st.error("Email e senha obrigatórios")
        elif novo_email in df_emails["EMAIL"].astype(str).str.lower().values:
            st.error("Email já existe")
        else:
            novo_reg=pd.DataFrame([{"EMAIL":novo_email,"SENHA":nova_senha,"NIVEL":novo_nivel}])
            df_emails=pd.concat([df_emails, novo_reg], ignore_index=True)
            df_emails.to_csv(ARQ_EMAILS,index=False)
            st.success(f"Criado: {novo_email}"); st.rerun()
    st.divider()
    email_del=st.selectbox("Excluir acesso", df_emails["EMAIL"].tolist())
    if st.button("🗑️ Excluir"):
        if email_del=="admin@admin.com": st.error("Não pode excluir admin")
        else:
            df_emails=df_emails[df_emails["EMAIL"]!=email_del]
            df_emails.to_csv(ARQ_EMAILS,index=False)
            st.success("Removido"); st.rerun()
