import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

st.set_page_config(page_title="REFORMA DE FORNOS - MATERIAIS REFRATARIOS", layout="wide", page_icon="🔥")

FUSO = ZoneInfo("America/Sao_Paulo")
ARQ_DADOS, ARQ_MOV, ARQ_EMAILS = "dados.csv","mov.csv","emails.csv"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@700;800;900&display=swap');
* {font-family: 'Inter', sans-serif}
.main-title {text-align:center; font-size:34px; font-weight:900; color:#ff4500; letter-spacing:1px}
.sub-title {text-align:center; font-size:13px; color:#888; margin-top:-8px; margin-bottom:12px}
.card {background:white; border-radius:18px; padding:20px; box-shadow:0 6px 18px rgba(0,0,0,0.12); border:1px solid #eee; text-align:center}
.card-red {background: linear-gradient(135deg,#ff4d4d,#b71c1c); color:white; border-radius:18px; padding:22px; text-align:center; box-shadow:0 6px 18px rgba(183,28,28,0.4)}
.card-orange {background: linear-gradient(135deg,#ff9800,#e65100); color:white; border-radius:18px; padding:22px; text-align:center; box-shadow:0 6px 18px rgba(230,81,0,0.4)}
.card-yellow {background: linear-gradient(135deg,#ffeb3b,#f9a825); color:#212121; border-radius:18px; padding:22px; text-align:center; box-shadow:0 6px 18px rgba(249,168,37,0.4)}
.card-green {background: linear-gradient(135deg,#00e676,#1b5e20); color:white; border-radius:18px; padding:22px; text-align:center; box-shadow:0 6px 18px rgba(27,94,32,0.4)}
.card-dark {background: linear-gradient(135deg,#37474f,#111); color:white; border-radius:18px; padding:22px; text-align:center; box-shadow:0 6px 18px rgba(0,0,0,0.5)}
.metric-big {font-size:38px; font-weight:900; line-height:1}
.metric-label {font-size:12px; font-weight:700; opacity:0.95; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:6px}
.big-number {font-size:22px; font-weight:800}
</style>
""", unsafe_allow_html=True)

# SAFE - NAO APAGA SEUS DADOS
if not os.path.exists(ARQ_DADOS):
    pd.DataFrame([{"ID":1,"NOME":"PASTA FRIA","UNIDADE":"KG","MARCA":"MORGAN","LOCAL":"BARRACAO","SALDO":0,"VALIDADE_PADRAO":180,"FORNECEDOR":"REFRATARIOS"}]).to_csv(ARQ_DADOS,index=False)
if not os.path.exists(ARQ_MOV):
    pd.DataFrame(columns=["IDX","DATA_HORA","DATA_FAB","VALIDADE","DIAS_VALIDADE","STATUS_VAL","LOTE","MARCA","FORNECEDOR","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","LOCAL","TIPO","ID_MAT","NOME_MAT","RESPONSAVEL","OBS"]).to_csv(ARQ_MOV,index=False)
if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","NIVEL":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)

if "logado" not in st.session_state: st.session_state.logado=False
if not st.session_state.logado:
    st.markdown('<div class="main-title">🔥 REFORMA DE FORNOS</div><div class="sub-title">MATERIAIS REFRATÁRIOS</div>', unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        e=st.text_input("Email").lower().strip()
        s=st.text_input("Senha", type="password")
        if st.button("ENTRAR", type="primary", use_container_width=True):
            df_e=pd.read_csv(ARQ_EMAILS); df_e["EMAIL"]=df_e["EMAIL"].astype(str).str.lower().str.strip()
            if not df_e[(df_e["EMAIL"]==e)&(df_e["SENHA"].astype(str)==s)].empty:
                st.session_state.logado=True; st.session_state.usuario=e
                st.session_state.dados=pd.read_csv(ARQ_DADOS).to_dict('records')
                st.session_state.mov=pd.read_csv(ARQ_MOV).to_dict('records') if not pd.read_csv(ARQ_MOV).empty else []
                st.rerun()
            else: st.error("Acesso negado")
    st.stop()

agora=datetime.now(FUSO); hoje=date.today()
st.markdown('<div class="main-title">🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS 🔥</div><div class="sub-title">Visual Profissional • Números Grandes • Total sem Marca</div>', unsafe_allow_html=True)
st.sidebar.caption(f"{st.session_state.usuario}")
if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()
for d in st.session_state.dados:
    try: d["SALDO"]=float(d["SALDO"])
    except: d["SALDO"]=0.0

menu=st.sidebar.radio("MENU", ["📊 Dashboard","📦 Estoque","📝 Lançar","🔍 Materiais","🔑 Permissões"], label_visibility="collapsed")

df_est=pd.DataFrame(st.session_state.dados) if st.session_state.dados else pd.DataFrame()
df_mov=pd.DataFrame(st.session_state.mov) if st.session_state.mov else pd.DataFrame()
if not df_mov.empty:
    df_mov["VAL_DT"]=pd.to_datetime(df_mov["VALIDADE"], format="%d/%m/%Y", errors='coerce')
    df_mov["DIAS_REST"]=(df_mov["VAL_DT"]-pd.Timestamp(hoje)).dt.days
    df_mov["STATUS_ATUAL"]=df_mov["DIAS_REST"].apply(lambda d: "VENCIDO" if d<0 else "A VENCER 30d" if d<=30 else "A VENCER 90d" if d<=90 else "OK")

if menu=="📊 Dashboard":
    total_geral = df_est.groupby("NOME")["SALDO"].sum().sum() if not df_est.empty else 0
    venc_total = df_mov[df_mov["STATUS_ATUAL"]=="VENCIDO"]["TOTAL"].sum() if not df_mov.empty else 0
    a30_total = df_mov[df_mov["STATUS_ATUAL"]=="A VENCER 30d"]["TOTAL"].sum() if not df_mov.empty else 0
    itens = df_est["NOME"].nunique() if not df_est.empty else 0
    c1,c2,c3,c4=st.columns(4)
    c1.markdown(f'<div class="card-dark"><div class="metric-label">Total Geral</div><div class="metric-big">{total_geral:.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-red"><div class="metric-label">Vencido</div><div class="metric-big">{venc_total:.0f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-orange"><div class="metric-label">Vence 30 dias</div><div class="metric-big">{a30_total:.0f}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card"><div class="metric-label">Tipos</div><div class="metric-big" style="color:#111; font-size:38px">{itens}</div></div>', unsafe_allow_html=True)
    st.write("")
    if not df_mov.empty:
        df_total_mat = df_mov.groupby("NOME_MAT")["TOTAL"].sum().reset_index().sort_values("TOTAL", ascending=False)
        st.markdown("### 📦 TOTAL POR MATERIAL - SEM MARCA")
        st.dataframe(df_total_mat, use_container_width=True, hide_index=True)
        col1,col2=st.columns([2,1])
        with col1:
            df_g=df_mov.groupby("STATUS_ATUAL")["TOTAL"].sum().reset_index()
            fig=px.bar(df_g, x="STATUS_ATUAL", y="TOTAL", color="STATUS_ATUAL", text="TOTAL", color_discrete_map={"VENCIDO":"#d50000","A VENCER 30d":"#ff6d00","A VENCER 90d":"#ffd600","OK":"#00c853"})
            fig.update_traces(texttemplate='<b>%{text:.0f}</b>', textposition='outside', textfont=dict(size=20, color='black'))
            fig.update_layout(showlegend=False, height=380, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(size=14))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2=px.pie(df_g, names="STATUS_ATUAL", values="TOTAL", hole=0.55, color="STATUS_ATUAL", color_discrete_map={"VENCIDO":"#d50000","A VENCER 30d":"#ff6d00","A VENCER 90d":"#ffd600","OK":"#00c853"})
            fig2.update_traces(textinfo='percent+label', textfont_size=13, textposition='inside')
            fig2.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

elif menu=="📦 Estoque":
    st.subheader("Estoque - Total sem Marca")
    if df_est.empty: st.info("Sem estoque")
    else:
        pivot_local = df_est.groupby(["NOME","LOCAL"])["SALDO"].sum().unstack(fill_value=0).reset_index()
        for c in ["BARRACAO","OFICINA"]:
            if c not in pivot_local.columns: pivot_local[c]=0
        pivot_local["TOTAL"] = pivot_local["BARRACAO"]+pivot_local["OFICINA"]
        sel=st.selectbox("Filtrar", ["TODOS"]+sorted(pivot_local["NOME"].unique().tolist()))
        df_show=pivot_local if sel=="TODOS" else pivot_local[pivot_local["NOME"]==sel]
        st.dataframe(df_show.sort_values("TOTAL", ascending=False), use_container_width=True, hide_index=True)

elif menu=="📝 Lançar":
    st.subheader("Novo Lançamento")
    ids=sorted(list(set([int(d["ID"]) for d in st.session_state.dados]))) if st.session_state.dados else [1]
    mapa={int(d["ID"]):(d["NOME"],d["UNIDADE"],int(d.get("VALIDADE_PADRAO",90)),d.get("MARCA",""),d.get("FORNECEDOR","")) for d in st.session_state.dados}
    id_sel=st.selectbox("Material", ids, format_func=lambda x: f"{x} - {mapa.get(x,('NOVO','',90,'',''))[0]}")
    with st.container(border=True):
        cA,cB,cC=st.columns(3)
        marca=cA.text_input("Marca (não conta no total)", value=mapa.get(id_sel,("","",""))[3])
        fornecedor=cB.text_input("Fornecedor *", value=mapa.get(id_sel,("","","","",""))[4])
        lote=cC.text_input("Lote *")
        c1,c2,c3,c4,c5=st.columns(5)
        local_sel=c1.selectbox("Local", ["BARRACAO","OFICINA"])
        data_fab=c2.date_input("Fab", value=hoje)
        validade=c3.date_input("Val", value=data_fab+timedelta(days=mapa.get(id_sel,("","",90,"",""))[2]))
        qtd=c4.number_input("Qtd palete", value=1.0)
        entrada=c5.number_input("Entrada/Saída", value=1.0)
        tipo=st.segmented_control("Tipo", ["Entrada","Saida"], default="Entrada")
        total=qtd*entrada; dias=(validade-hoje).days
        st.markdown(f"### 📦 Total: **{total:.0f}** | Vence em **{dias} dias**")
        if st.button("SALVAR", type="primary", use_container_width=True):
            idx_ba=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==id_sel and d["LOCAL"]=="BARRACAO"),None)
            idx_of=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==id_sel and d["LOCAL"]=="OFICINA"),None)
            if idx_ba is None:
                st.session_state.dados.append({"ID":id_sel,"NOME":mapa.get(id_sel,(f"MAT {id_sel}","",90,marca,fornecedor))[0],"UNIDADE":"KG","MARCA":marca.upper(),"LOCAL":"BARRACAO","SALDO":0.0,"VALIDADE_PADRAO":(validade-data_fab).days,"FORNECEDOR":fornecedor.upper()}); idx_ba=len(st.session_state.dados)-1
            if idx_of is None:
                st.session_state.dados.append({"ID":id_sel,"NOME":mapa.get(id_sel,(f"MAT {id_sel}","",90,marca,fornecedor))[0],"UNIDADE":"KG","MARCA":marca.upper(),"LOCAL":"OFICINA","SALDO":0.0,"VALIDADE_PADRAO":(validade-data_fab).days,"FORNECEDOR":fornecedor.upper()}); idx_of=len(st.session_state.dados)-1
            if tipo=="Entrada":
                if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]+=total
                else: st.session_state.dados[idx_of]["SALDO"]+=total
            else:
                if local_sel=="BARRACAO": st.session_state.dados[idx_ba]["SALDO"]-=total
                else: st.session_state.dados[idx_of]["SALDO"]-=total
            status="VENCIDO" if dias<0 else "A VENCER 30d" if dias<=30 else "A VENCER 90d" if dias<=90 else "OK"
            novo_id=max([int(m.get("IDX",0)) for m in st.session_state.mov])+1 if st.session_state.mov else 1
            st.session_state.mov.append({"IDX":novo_id,"DATA_HORA":agora.strftime("%d/%m/%Y %H:%M"),"DATA_FAB":data_fab.strftime("%d/%m/%Y"),"VALIDADE":validade.strftime("%d/%m/%Y"),"DIAS_VALIDADE":(validade-data_fab).days,"STATUS_VAL":status,"LOTE":lote.upper(),"MARCA":marca.upper(),"FORNECEDOR":fornecedor.upper(),"QTD_PALETE":qtd,"ENTRADA":entrada,"TOTAL":total,"UNIDADE":"KG","LOCAL":local_sel,"TIPO":tipo,"ID_MAT":id_sel,"NOME_MAT":mapa.get(id_sel,(f"MAT {id_sel}","",90,marca,fornecedor))[0],"RESPONSAVEL":st.session_state.usuario,"OBS":""})
            pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False); pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
            st.success("Salvo!"); st.rerun()

elif menu=="🔍 Materiais":
    st.subheader("Materiais - Clique em 1")
    if df_mov.empty: st.info("Sem dados")
    else:
        lista=sorted(df_mov["NOME_MAT"].unique())
        if "mat_sel" not in st.session_state: st.session_state.mat_sel=lista[0]
        cols=st.columns(3)
        for i,nome in enumerate(lista):
            tot=df_mov[df_mov["NOME_MAT"]==nome]["TOTAL"].sum()
            venc=df_mov[(df_mov["NOME_MAT"]==nome)&(df_mov["STATUS_ATUAL"]=="VENCIDO")]["TOTAL"].sum()
            label=f"{'🔴' if venc>0 else '🟢'} {nome} ({tot:.0f})"
            if cols[i%3].button(label, key=f"m_{nome}", use_container_width=True):
                st.session_state.mat_sel=nome
        st.divider()
        mat=st.session_state.mat_sel
        df_m=df_mov[df_mov["NOME_MAT"]==mat].copy()
        is_pasta_fria = "PASTA FRIA" in mat.upper()
        v=df_m[df_m["STATUS_ATUAL"]=="VENCIDO"]["TOTAL"].sum()
        a30=df_m[df_m["STATUS_ATUAL"]=="A VENCER 30d"]["TOTAL"].sum()
        a90=df_m[df_m["STATUS_ATUAL"]=="A VENCER 90d"]["TOTAL"].sum()
        ok=df_m[df_m["STATUS_ATUAL"]=="OK"]["TOTAL"].sum()
        c1,c2,c3,c4=st.columns(4)
        c1.markdown(f'<div class="card-red"><div class="metric-label">Vencido</div><div class="metric-big">{v:.0f}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="card-orange"><div class="metric-label">30 dias</div><div class="metric-big">{a30:.0f}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="card-yellow"><div class="metric-label">90 dias</div><div class="metric-big">{a90:.0f}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="card-green"><div class="metric-label">OK</div><div class="metric-big">{ok:.0f}</div></div>', unsafe_allow_html=True)
        st.write("")
        df_s=df_m.groupby("STATUS_ATUAL")["TOTAL"].sum().reset_index()
        fig=px.bar(df_s, x="STATUS_ATUAL", y="TOTAL", color="STATUS_ATUAL", text="TOTAL", color_discrete_map={"VENCIDO":"#d50000","A VENCER 30d":"#ff6d00","A VENCER 90d":"#ffd600","OK":"#00c853"})
        fig.update_traces(texttemplate='<b>%{text:.0f}</b>', textposition='outside', textfont=dict(size=22, color='black'))
        fig.update_layout(showlegend=False, height=350, title=dict(text=f"{mat} - Total sem marca", font=dict(size=20)))
        st.plotly_chart(fig, use_container_width=True)
        if is_pasta_fria:
            st.markdown("### 🔥 PASTA FRIA - Todas as pastas e lotes")
            df_show = df_m.sort_values("VAL_DT")[["IDX","LOTE","MARCA","FORNECEDOR","DATA_FAB","VALIDADE","DIAS_REST","STATUS_ATUAL","TOTAL","LOCAL"]]
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            c1,c2=st.columns(2)
            with c1:
                st.markdown("**Por Marca (informativo)**")
                st.dataframe(df_m.groupby("MARCA")["TOTAL"].sum().reset_index(), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("**Por Lote**")
                st.dataframe(df_m.groupby(["LOTE","STATUS_ATUAL","VALIDADE"])["TOTAL"].sum().reset_index().sort_values("VALIDADE"), use_container_width=True, hide_index=True)
        else:
            with st.expander(f"Ver {len(df_m)} lotes de {mat}"):
                st.dataframe(df_m.sort_values("VAL_DT")[["IDX","LOTE","MARCA","VALIDADE","DIAS_REST","STATUS_ATUAL","TOTAL","LOCAL"]], use_container_width=True, hide_index=True)
        st.divider()
        idx_del=st.number_input("IDX para excluir", min_value=1, step=1, key="idx_mat")
        if st.button("🗑️ Excluir lote", type="primary"):
            reg=next((m for m in st.session_state.mov if int(m["IDX"])==idx_del), None)
            if reg:
                idm=int(reg["ID_MAT"]); tot=float(reg["TOTAL"]); loc=reg["LOCAL"]; tip=reg["TIPO"]
                idx_ba=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==idm and d["LOCAL"]=="BARRACAO"),None)
                idx_of=next((i for i,d in enumerate(st.session_state.dados) if int(d["ID"])==idm and d["LOCAL"]=="OFICINA"),None)
                if tip=="Entrada":
                    if loc=="BARRACAO" and idx_ba is not None: st.session_state.dados[idx_ba]["SALDO"]-=tot
                    if loc=="OFICINA" and idx_of is not None: st.session_state.dados[idx_of]["SALDO"]-=tot
                else:
                    if loc=="BARRACAO" and idx_ba is not None: st.session_state.dados[idx_ba]["SALDO"]+=tot
                    if loc=="OFICINA" and idx_of is not None: st.session_state.dados[idx_of]["SALDO"]+=tot
                st.session_state.mov=[m for m in st.session_state.mov if int(m["IDX"])!=idx_del]
                pd.DataFrame(st.session_state.dados).to_csv(ARQ_DADOS,index=False); pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
                st.success("Excluído"); st.rerun()

elif menu=="🔑 Permissões":
    st.subheader("Permissões")
    df_e=pd.read_csv(ARQ_EMAILS)
    st.dataframe(df_e, use_container_width=True, hide_index=True)
    with st.container(border=True):
        c1,c2,c3=st.columns(3)
        ne=c1.text_input("Novo email").lower().strip()
        ns=c2.text_input("Senha")
        ni=c3.selectbox("Nível", ["ADMIN","USUARIO","VISUALIZACAO"])
        if st.button("Gerar Acesso", type="primary", use_container_width=True):
            if ne and ns and ne not in df_e["EMAIL"].astype(str).str.lower().values:
                pd.concat([df_e, pd.DataFrame([{"EMAIL":ne,"SENHA":ns,"NIVEL":ni}])], ignore_index=True).to_csv(ARQ_EMAILS,index=False)
                st.success("Criado"); st.rerun()
