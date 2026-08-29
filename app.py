import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
import plotly.express as px
from datetime import datetime as dt

st.set_page_config(page_title="REFORMA DE FORNOS - ENTRADA/SAIDA + APAGAR + GUARDA 100%", layout="wide")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_GRD = "grd.csv"
ARQ_EMAILS = "emails.csv"

LOCAL_GALPAO = "GALPAO DE MATERIAIS REFRATARIOS"
LOCAL_SALA = "SALA ANEXA"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"
LOCAIS = [LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]
LOCAIS_ACESSO = ["AMBOS", LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]
TIPOS_EMBALAGEM = ["PALETE", "CAIXA", "SACO", "FARDO", "BAG", "TAMBOR", "UNIDADE"]

def safe_float(v, d=0.0):
    try: return float(str(v).replace(",", "."))
    except: return float(d)
def parse_data_hora(valor):
    try:
        s=str(valor).strip()
        if " " in s and ":" in s:
            try: return dt.strptime(s, "%d/%m/%Y %H:%M:%S")
            except: return dt.strptime(s, "%d/%m/%Y %H:%M")
    except: pass
    try: return dt.strptime(str(valor).split(" ")[0], "%d/%m/%Y")
    except: return dt.now(fuso).replace(tzinfo=None)

def carregar(caminho):
    if not os.path.exists(caminho): return []
    try: df=pd.read_csv(caminho, dtype=str, encoding='utf-8').fillna("")
    except:
        try: df=pd.read_csv(caminho, dtype=str, encoding='latin-1').fillna("")
        except: return []
    df.columns=[str(c).upper().strip() for c in df.columns]
    return df.to_dict('records')

def salvar_tudo():
    try:
        pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD, index=False, encoding='utf-8') if st.session_state.cad else pd.DataFrame([]).to_csv(ARQ_CAD, index=False)
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False, encoding='utf-8') if st.session_state.mov else pd.DataFrame([]).to_csv(ARQ_MOV, index=False)
        pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD, index=False, encoding='utf-8') if st.session_state.grd else pd.DataFrame([]).to_csv(ARQ_GRD, index=False)
        return True
    except Exception as e:
        st.error(f"Erro salvar: {e}")
        return False

def df_safe_sort(df, asc=False):
    try: return df.sort_values(by="DATA_HORA", ascending=asc) if "DATA_HORA" in df.columns else df
    except: return df

def get_saldos():
    saldos={}; carac={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper().strip(); desc=str(r.get('DESCRICAO','')).upper().strip()
        if not idp or not desc: continue
        chave=f"{idp}__{desc}__{str(r.get('MARCA','')).upper()}"
        if chave not in carac: carac[chave]={'ID':idp,'DESCRICAO':desc,'TIPO_EMBALAGEM':str(r.get('TIPO_EMBALAGEM','PALETE')).upper(),'QTD_POR_EMBALAGEM':safe_float(r.get('QTD_POR_EMBALAGEM',1250),1250),'MARCA':str(r.get('MARCA','')).upper()}
    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip(); lote=str(m.get('LOTE','')).upper().strip()
            if not idp or not lote: continue
            local=str(m.get('LOCAL_MOV',LOCAL_GALPAO)).upper()
            if "SALA" in local: local=LOCAL_SALA
            elif "OFIC" in local: local=LOCAL_OFICINA
            else: local=LOCAL_GALPAO
            desc=str(m.get('DESCRICAO','')).upper()
            c=None
            for k,v in carac.items():
                if v['ID']==idp and v['DESCRICAO']==desc: c=v; break
            if not c:
                for k,v in carac.items():
                    if v['ID']==idp: c=v; break
            if not c: continue
            chave=f"{idp}__{desc}__{local}__{str(m.get('MARCA','')).upper()}__{lote}"
            if chave not in saldos and m.get('TIPO')=="ENTRADA":
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'TIPO_EMBALAGEM':c['TIPO_EMBALAGEM'],'QTD_POR_EMBALAGEM':c['QTD_POR_EMBALAGEM'],'LOCAL':local,'MARCA':c['MARCA'],'LOTE':lote,'SALDO':0,'EMBALAGENS':0,'ULT_ATUAL':'','CALCULO':''}
            if chave not in saldos: continue
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0)); saldos[chave]['EMBALAGENS']+=safe_float(m.get('PALETES',0)); saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
            else: saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0)); saldos[chave]['EMBALAGENS']-=safe_float(m.get('PALETES',0)); saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
        except: continue
    return saldos, carac

def get_saldo_sala_com_quarentena(tempo_horas=None):
    if tempo_horas is None: tempo_horas=st.session_state.get('tempo_quarentena',48)
    agora_dt=datetime.now(fuso).replace(tzinfo=None)
    saldos,_=get_saldos(); total={}; pend={}; disp={}
    for k,v in saldos.items():
        if v['LOCAL']==LOCAL_SALA and v['SALDO']>0: total[k]=v.copy(); disp[k]=v.copy()
    for m in st.session_state.mov:
        try:
            if str(m.get('LOCAL_MOV','')).upper()!=LOCAL_SALA.upper(): continue
            if m.get('TIPO')!="ENTRADA": continue
            idp=str(m.get('ID','')).upper(); lote=str(m.get('LOTE','')).upper()
            desc=str(m.get('DESCRICAO','')).upper()
            chave=f"{idp}__{desc}__{LOCAL_SALA}__{str(m.get('MARCA','')).upper()}__{lote}"
            data_mov=parse_data_hora(m.get('DATA_HORA',''))
            diff=(agora_dt-data_mov).total_seconds()/3600
            if diff < tempo_horas:
                q=safe_float(m.get('TOTAL_QTD',0))
                if chave not in pend: pend[chave]={'ID':idp,'LOTE':lote,'QTD_PENDENTE':q,'DATA_ENTRADA':str(m.get('DATA_HORA','')),'HORAS_RESTANTES':tempo_horas-diff}
                else: pend[chave]['QTD_PENDENTE']+=q
                if chave in disp:
                    disp[chave]['SALDO']-=q
                    if disp[chave]['SALDO']<0: disp[chave]['SALDO']=0
        except: continue
    disp={k:v for k,v in disp.items() if v['SALDO']>0}
    return total,pend,disp

# ========== PERSISTENCIA 100% - GUARDA MESMO SE DESLIGAR ==========
if 'inicializado' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD)
    st.session_state.mov=carregar(ARQ_MOV)
    st.session_state.grd=carregar(ARQ_GRD)
    st.session_state.inicializado=True
if 'tempo_quarentena' not in st.session_state: st.session_state.tempo_quarentena=48
if not os.path.exists(ARQ_EMAILS): pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'logado' not in st.session_state: st.session_state.logado=False
if 'usuario' not in st.session_state: st.session_state.usuario=None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA DE FORNOS - ENTRADA/SAIDA + APAGAR + GUARDA 100%</h1>", unsafe_allow_html=True)
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS,dtype=str).fillna(""); df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
        u=df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
        if not u.empty: st.session_state.logado=True; st.session_state.usuario=u.iloc[0].to_dict(); st.rerun()
        else: st.error("Invalido")
    st.stop()

user=st.session_state.usuario
is_admin=str(user.get('EMAIL','')).lower()=="admin@admin.com"
import streamlit.components.v1 as components
components.html("<p style='color:green;'>✅ ENTRADA/SAIDA AUTO ESTOQUE/GRAFICO + APAGAR + GUARDA 100% MESMO SE DESLIGAR</p>",height=30)
st.sidebar.write(f"Logado: {user.get('NOME')}")
st.sidebar.metric("⏰ VOCE DECIDE", f"{st.session_state.tempo_quarentena}H")
st.sidebar.write(f"📦 CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)} GRD:{len(st.session_state.grd)}")
st.sidebar.divider()
st.sidebar.write("💾 BACKUP - GUARDA 100% MESMO SE DESLIGAR")
if st.session_state.cad: st.sidebar.download_button("BAIXAR CAD - BACKUP", pd.DataFrame(st.session_state.cad).to_csv(index=False), "cadastro_backup.csv")
if st.session_state.mov: st.sidebar.download_button("BAIXAR MOV - BACKUP", pd.DataFrame(st.session_state.mov).to_csv(index=False), "movimentacao_backup.csv")
if st.session_state.grd: st.sidebar.download_button("BAIXAR GRD - BACKUP", pd.DataFrame(st.session_state.grd).to_csv(index=False), "grd_backup.csv")
st.sidebar.divider()
st.sidebar.write("📤 RESTAURAR SE DESLIGAR")
up_cad=st.sidebar.file_uploader("Restaurar CAD", type="csv", key="up_cad")
if up_cad:
    try: df=pd.read_csv(up_cad,dtype=str).fillna(""); st.session_state.cad=df.to_dict('records'); salvar_tudo(); st.sidebar.success(f"CAD restaurado {len(st.session_state.cad)}"); st.rerun()
    except: pass
up_mov=st.sidebar.file_uploader("Restaurar MOV", type="csv", key="up_mov")
if up_mov:
    try: df=pd.read_csv(up_mov,dtype=str).fillna(""); st.session_state.mov=df.to_dict('records'); salvar_tudo(); st.sidebar.success(f"MOV restaurado {len(st.session_state.mov)}"); st.rerun()
    except: pass
if st.sidebar.button("Sair"): salvar_tudo(); st.session_state.logado=False; st.rerun()

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
tabs=st.tabs(["ADMIN","DASHBOARD","3 - CADASTRO - CARACTERISTICAS","4 - ENTRADA/SAIDA - ATUALIZA ESTOQUE/GRAFICOS AUTO + APAGAR","ESTOQUE AUTO","BUSCA ID","GRD HORAS EDITAVEIS","GRAFICO AUTO + DATA/HORA BRASILIA","HISTORICO + APAGAR"])
tab_admin, tab_dash, tab_cad, tab_mov, tab_est, tab_busca, tab_grd, tab_graf, tab_hist = tabs

with tab_admin:
    st.header("1 - ADMIN")
    if is_admin:
        with st.form("form_admin"):
            email_new=st.text_input("Email"); nome_new=st.text_input("Nome"); senha_new=st.text_input("Senha")
            local_new=st.selectbox("Local",LOCAIS_ACESSO); status_new=st.selectbox("Status",["LIBERADO","BLOQUEADO"])
            if st.form_submit_button("SALVAR"):
                df=pd.read_csv(ARQ_EMAILS); df=df[df['EMAIL'].astype(str).str.lower()!=email_new.lower()]
                novo=pd.DataFrame([{"EMAIL":email_new.lower(),"SENHA":senha_new,"LOCAL":local_new,"STATUS":status_new,"NOME":nome_new.upper()}])
                pd.concat([df,novo],ignore_index=True).to_csv(ARQ_EMAILS,index=False); st.rerun()
        st.dataframe(pd.read_csv(ARQ_EMAILS), use_container_width=True)

with tab_dash:
    st.header("2 - DASHBOARD - ATUALIZA AUTO")
    total_sala,pend,disp=get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    saldos,_=get_saldos()
    if not total_sala: total_sala={k:v for k,v in saldos.items() if v['LOCAL']==LOCAL_SALA and v['SALDO']>0}
    df_total=pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    if df_total.empty: st.warning("SEM ESTOQUE SALA - Faça ENTRADA/SAIDA na aba 4")
    else: st.dataframe(df_total[['ID','DESCRICAO','LOTE','SALDO','ULT_ATUAL']], use_container_width=True)

# ========== 3 ABA CADASTRO - TEM QUE TER - CARACTERISTICAS - GUARDA 100% ==========
with tab_cad:
    st.header("3 - ABA CADASTRO - TEM QUE TER - CARACTERISTICAS DO PRODUTO - GUARDA 100% MESMO SE DESLIGAR")
    st.success("✅ ABA CADASTRO - AQUI VOCE PREENCHE: ID + DESCRICAO + TIPO EMBALAGEM + QTD POR EMBALAGEM + MARCA - DEPOIS AUTO PELA ID NAS OUTRAS ABAS")
    id_in = st.text_input("JANELA 1 - ID* - DIGITE ID E ENTER - ABA CADASTRO - TEM QUE TER", placeholder="Ex: 15 + ENTER", key="cad_id_digital_final")
    if id_in:
        mats=[r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_in.upper()]
        if mats:
            st.warning(f"ID {id_in.upper()} JA TEM {len(mats)} MATERIAIS - MESMA ID VARIOS - PODE CADASTRAR MAIS")
            st.dataframe(pd.DataFrame(mats)[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','MARCA']].drop_duplicates(), use_container_width=True)

    with st.form("form_cad_final"):
        st.markdown("### 🖥️ FORMATO DIGITAL - ABA CADASTRO - JANELAS - TEM QUE TER")
        c1,c2=st.columns([1,2])
        with c1:
            st.markdown("**JANELA 1 - ID* - RASTREIO**")
            id_form=st.text_input("ID*", value=id_in.upper() if id_in else "", key="id_form_cad_final", label_visibility="collapsed")
        with c2:
            st.markdown("**JANELA 2 - DESCRIÇÃO* - CARACTERISTICA**")
            desc=st.text_input("DESCRIÇÃO*", placeholder="Ex: TIJOLO 65% ALUMINA", key="desc_cad_final", label_visibility="collapsed")
        c3,c4,c5=st.columns(3)
        with c3:
            st.markdown("**JANELA 3 - TIPO EMBALAGEM***")
            tipo_emb=st.selectbox("TIPO*", TIPOS_EMBALAGEM, key="tipo_cad_final", label_visibility="collapsed")
        with c4:
            st.markdown("**JANELA 4 - QTD POR EMBALAGEM***")
            qtd_emb=st.number_input("QTD POR EMB*", min_value=0.1, value=1250.0, key="qtd_cad_final", label_visibility="collapsed")
        with c5:
            st.markdown("**JANELA 5 - MARCA**")
            marca=st.text_input("MARCA", placeholder="Ex: IBAR", key="marca_cad_final", label_visibility="collapsed")

        st.markdown(f"**JANELA 6 - CALCULO AUTO: {tipo_emb} x {qtd_emb:,.0f} - VAI ATUALIZAR ESTOQUE E GRAFICOS AUTO**")
        st.markdown(f"**JANELA 7 - DATA/HORA BRASÍLIA AUTO: {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA**")

        if st.form_submit_button(f"✅ CADASTRAR - ABA CADASTRO - GUARDA 100% MESMO SE DESLIGAR", type="primary", use_container_width=True):
            if not id_form or not desc: st.error("ID e DESCRIÇÃO obrigatórios")
            else:
                st.session_state.cad.append({"ID":id_form.upper().strip(),"DESCRICAO":desc.upper(),"TIPO_EMBALAGEM":tipo_emb.upper(),"QTD_POR_EMBALAGEM":qtd_emb,"QTD_PALETE":qtd_emb,"MARCA":marca.upper() if marca else "SEM MARCA","LOTE":"","ENTRADA":0,"TOTAL":0,"LOCAL":"","FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                salvar_tudo(); st.success(f"✅ CADASTRADO ID {id_form.upper()} - {desc.upper()} - GUARDADO 100% - NAO PERDE SE DESLIGAR - CAD:{len(st.session_state.cad)}"); st.balloons(); st.rerun()

    st.divider()
    st.subheader("📋 CADASTRADOS - ABA CADASTRO - COM OPÇÃO APAGAR - GUARDA 100%")
    if st.session_state.cad:
        df_all=pd.DataFrame(st.session_state.cad)
        df_all=df_all[df_all['DESCRICAO'].astype(str).str.strip()!=""]
        if not df_all.empty:
            df_show=df_all[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','MARCA']].sort_values(by=['ID','DESCRICAO']).drop_duplicates()
            st.dataframe(df_show, use_container_width=True, height=300)
            st.markdown("### 🗑️ APAGAR REGISTRO - ABA CADASTRO")
            opcoes_cad=[f"{row['ID']} - {row['DESCRICAO']} - {row['MARCA']}" for _,row in df_show.iterrows()]
            sel_apagar_cad=st.selectbox("SELECIONE MATERIAL PARA APAGAR - CADASTRO", [""]+opcoes_cad, key="apagar_cad")
            if sel_apagar_cad:
                if st.button(f"🗑️ APAGAR {sel_apagar_cad} - CADASTRO - CONFIRMAR", type="primary", key="btn_apagar_cad"):
                    idx=opcoes_cad.index(sel_apagar_cad)
                    row=df_show.iloc[idx]
                    # Remove do cad
                    st.session_state.cad=[r for r in st.session_state.cad if not (str(r.get('ID','')).upper()==row['ID'] and str(r.get('DESCRICAO','')).upper()==row['DESCRICAO'])]
                    salvar_tudo(); st.success(f"🗑️ APAGADO {sel_apagar_cad} - GUARDADO 100% - NAO PERDE"); st.rerun()

# ========== 4 ABA ENTRADA/SAIDA - ATUALIZA ESTOQUE E GRAFICOS AUTO + APAGAR + GUARDA 100% ==========
with tab_mov:
    st.header("4 - ABA ENTRADA/SAIDA - REALIZAR ENTRADAS E SAIDAS - ATUALIZA ESTOQUE E GRAFICOS AUTOMATICO - COM APAGAR - GUARDA 100% MESMO SE DESLIGAR")

    st.markdown("### 🖥️ JANELA 1 - DIGITE ID E ENTER - FORMATO DIGITAL - AUTO PREENCHE OUTRAS JANELAS")
    id_mov = st.text_input("**JANELA 1 - ID* - DIGITE ID CADASTRADO NA ABA CADASTRO E DE ENTER - AUTO PREENCHE**", placeholder="Ex: 15 + ENTER", key="mov_id_final_apagar")

    materiais_da_id=[]
    if id_mov:
        up=id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==up and str(r.get('DESCRICAO','')).strip()!="":
                chave_mat=f"{str(r.get('DESCRICAO','')).upper()}__{str(r.get('MARCA','SEM MARCA')).upper()}"
                if chave_mat not in [f"{m['DESCRICAO']}__{m['MARCA']}" for m in materiais_da_id]:
                    materiais_da_id.append({'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'MARCA':str(r.get('MARCA','SEM MARCA')).upper(),'TIPO_EMBALAGEM':str(r.get('TIPO_EMBALAGEM','PALETE')).upper(),'QTD_POR_EMBALAGEM':safe_float(r.get('QTD_POR_EMBALAGEM',1250),1250)})

    if not id_mov:
        st.info("👉 JANELA 1 - DIGITE ID DA ABA CADASTRO E DE ENTER - FORMATO DIGITAL - OUTRAS JANELAS PREENCHEM SOZINHAS - ATUALIZA ESTOQUE E GRAFICOS AUTO")
    elif not materiais_da_id:
        st.error(f"ID {id_mov.upper()} NAO CADASTRADO - Vá na ABA 3 CADASTRO - TEM QUE TER")
    else:
        if len(materiais_da_id)>1:
            opcoes=[f"{m['DESCRICAO']} | {m['MARCA']} | {m['TIPO_EMBALAGEM']} {m['QTD_POR_EMBALAGEM']:,.0f}" for m in materiais_da_id]
            mat_escolhido_str=st.selectbox(f"ID {id_mov.upper()} TEM {len(materiais_da_id)} MATERIAIS - ESCOLHA - AUTO PELA ID", opcoes, key="mat_escolhido_final_apagar")
            idx=opcoes.index(mat_escolhido_str); mat=materiais_da_id[idx]
        else:
            mat=materiais_da_id[0]; st.success(f"✅ ID {id_mov.upper()} - JANELAS AUTO PREENCHIDAS - ATUALIZA ESTOQUE/GRAFICOS AUTO")

        saldos,_=get_saldos()
        saldo_id_total=sum([v['SALDO'] for v in saldos.values() if v['ID']==id_mov.upper()])
        ultima_retirada_str="SEM RETIRADA"
        for m in sorted(st.session_state.mov, key=lambda x: parse_data_hora(x.get('DATA_HORA','')), reverse=True):
            if str(m.get('ID','')).upper()==id_mov.upper() and m.get('TIPO')=="SAIDA":
                ultima_retirada_str=m.get('DATA_HORA','') + " - BRASÍLIA"; break
        lotes=list(set([v['LOTE'] for v in saldos.values() if v['ID']==id_mov.upper() and v['DESCRICAO']==mat['DESCRICAO'] and v['SALDO']>0]))

        st.markdown("---")
        st.markdown("### 🖥️ JANELAS AUTO PREENCHIDAS APÓS ENTER - ABA CADASTRO TEM QUE TER")
        col1,col2,col3,col4=st.columns(4)
        with col1:
            st.markdown("**JANELA 2 - DESCRIÇÃO - AUTO PELA ID**")
            st.text_input("DESC AUTO", value=mat['DESCRICAO'], disabled=True, key="j2_desc_final", label_visibility="collapsed")
        with col2:
            st.markdown("**JANELA 3 - TIPO EMB - AUTO**")
            st.text_input("TIPO AUTO", value=mat['TIPO_EMBALAGEM'], disabled=True, key="j3_tipo_final", label_visibility="collapsed")
        with col3:
            st.markdown("**JANELA 4 - QTD/EMB - AUTO**")
            st.text_input("QTD AUTO", value=f"{mat['QTD_POR_EMBALAGEM']:,.0f}", disabled=True, key="j4_qtd_final", label_visibility="collapsed")
        with col4:
            st.markdown("**JANELA 5 - MARCA - AUTO**")
            st.text_input("MARCA AUTO", value=mat['MARCA'], disabled=True, key="j5_marca_final", label_visibility="collapsed")

        st.markdown("### ✍️ VOCE PREENCHE APENAS - ENTRADA/SAIDA - ATUALIZA ESTOQUE/GRAFICOS AUTO")
        c_lote,c_local,c_tipo,c_qtd=st.columns(4)
        with c_lote:
            st.markdown("**JANELA 6 - LOTE - VOCE PREENCHE**")
            if lotes:
                sel=st.selectbox("LOTE", lotes+["NOVO LOTE"], key="j6_lote_sel_final", label_visibility="collapsed")
                lote_final=st.text_input("NOVO LOTE*", key="j6_lote_novo_final") if sel=="NOVO LOTE" else sel
                if sel!="NOVO LOTE": st.text_input("LOTE SEL", value=lote_final, disabled=True, key="j6_lote_show_final")
            else:
                lote_final=st.text_input("LOTE* - VOCE PREENCHE", key="j6_lote_final", label_visibility="collapsed")
        with c_local:
            st.markdown("**JANELA 7 - LOCAL - VOCE**")
            local_final=st.selectbox("LOCAL*", LOCAIS, key="j7_local_final", label_visibility="collapsed")
        with c_tipo:
            st.markdown("**JANELA 8 - ENTRADA/SAIDA - VOCE**")
            tipo_final=st.selectbox("TIPO*", ["ENTRADA","SAIDA"], key="j8_tipo_final", label_visibility="collapsed")
        with c_qtd:
            st.markdown("**JANELA 9 - QTD - VOCE - CALCULA AUTO**")
            qtd_emb_final=st.number_input(f"QTD {mat['TIPO_EMBALAGEM']}*", min_value=0.1, value=1.0, step=1.0, key="j9_qtd_final", label_visibility="collapsed")
            total_calc=qtd_emb_final*mat['QTD_POR_EMBALAGEM']
            st.metric(f"{qtd_emb_final} x {mat['QTD_POR_EMBALAGEM']:,.0f}", f"{total_calc:,.0f}")

        st.markdown("### 📊 JANELA 10 - ULTIMA - TOTAL GERAL ID + UNIDADE + DATA ULTIMA RETIRADA BRASÍLIA - ATUALIZA AUTO")
        cj1,cj2,cj3,cj4=st.columns(4)
        with cj1: st.metric(f"TOTAL GERAL ID {id_mov.upper()} - AUTO", f"{saldo_id_total:,.0f}", delta=f"+{total_calc:,.0f}" if tipo_final=="ENTRADA" else f"-{total_calc:,.0f}")
        with cj2: st.metric("UNIDADE - AUTO PELA ID", f"{mat['TIPO_EMBALAGEM']}", delta=f"{mat['QTD_POR_EMBALAGEM']:,.0f}/emb")
        with cj3: st.metric("DATA ULTIMA RETIRADA - BRASÍLIA - AUTO", f"{ultima_retirada_str}")
        with cj4: st.metric(f"ESTA MOV {tipo_final} - CALCULO AUTO", f"{total_calc:,.0f}")

        if st.button(f"✅ CONFIRMAR {tipo_final} - ID {id_mov.upper()} - {total_calc:,.0f} - ATUALIZA ESTOQUE/GRAFICOS AUTO - GUARDA 100%", type="primary", use_container_width=True, key="btn_confirm_final"):
            if not lote_final or str(lote_final).strip()=="": st.error("LOTE OBRIGATORIO")
            else:
                agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                base={"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_emb_final,"TOTAL_QTD":total_calc,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO_EMBALAGEM'],"QTD_POR_EMBALAGEM":mat['QTD_POR_EMBALAGEM']}
                if local_final==LOCAL_GALPAO and tipo_final=="ENTRADA": st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_GALPAO})
                elif local_final==LOCAL_GALPAO and tipo_final=="SAIDA":
                    st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_GALPAO}); st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                elif local_final==LOCAL_SALA and tipo_final=="ENTRADA":
                    st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_GALPAO}); st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_SALA})
                elif local_final==LOCAL_SALA and tipo_final=="SAIDA":
                    st.session_state.mov.append({**base,"TIPO":"SAIDA","LOCAL_MOV":LOCAL_SALA}); st.session_state.mov.append({**base,"TIPO":"ENTRADA","LOCAL_MOV":LOCAL_OFICINA})
                else: st.session_state.mov.append({**base,"TIPO":tipo_final,"LOCAL_MOV":local_final})
                salvar_tudo()
                st.success(f"✅ ENTRADA/SAIDA GUARDADA - ATUALIZOU ESTOQUE E GRAFICOS AUTO - TOTAL GERAL ID {id_mov.upper()} AGORA {saldo_id_total+ (total_calc if tipo_final=='ENTRADA' else -total_calc):,.0f} - GUARDA 100% MESMO SE DESLIGAR - MOV:{len(st.session_state.mov)}")
                st.balloons()
                st.rerun()

    st.divider()
    st.subheader("📋 ULTIMAS 20 ENTRADAS/SAIDAS - COM OPÇÃO APAGAR REGISTRO - ATUALIZA ESTOQUE/GRAFICOS AUTO")
    if st.session_state.mov:
        df_mov_show=df_safe_sort(pd.DataFrame(st.session_state.mov), False).head(20)
        st.dataframe(df_mov_show, use_container_width=True)

        st.markdown("### 🗑️ APAGAR REGISTRO - ENTRADA/SAIDA - ATUALIZA ESTOQUE/GRAFICOS AUTO - GUARDA 100%")
        # Cria lista para apagar
        opcoes_apagar=[]
        for idx,row in df_mov_show.iterrows():
            opcoes_apagar.append(f"{idx} | {row.get('ID','')} - {row.get('DESCRICAO','')} - {row.get('LOTE','')} - {row.get('TIPO','')} - {row.get('TOTAL_QTD','')} - {row.get('DATA_HORA','')}")

        sel_apagar=st.selectbox("SELECIONE REGISTRO PARA APAGAR - ENTRADA/SAIDA", [""]+opcoes_apagar, key="apagar_mov")

        c_apagar1,c_apagar2=st.columns(2)
        with c_apagar1:
            if sel_apagar:
                if st.button(f"🗑️ APAGAR REGISTRO SELECIONADO - CONFIRMAR - ATUALIZA AUTO", type="primary", key="btn_apagar_mov"):
                    try:
                        idx_str=sel_apagar.split(" | ")[0]
                        idx=int(idx_str)
                        # Apaga do session_state.mov pelo indice original
                        # Precisa achar no st.session_state.mov
                        # Vamos apagar pelo match de todos os campos
                        row_to_delete=df_mov_show.loc[idx] if idx in df_mov_show.index else None
                        if row_to_delete is not None:
                            # Remove uma ocorrencia igual
                            for i, m in enumerate(st.session_state.mov):
                                if str(m.get('ID','')).upper()==str(row_to_delete.get('ID','')).upper() and str(m.get('LOTE','')).upper()==str(row_to_delete.get('LOTE','')).upper() and str(m.get('DATA_HORA',''))==str(row_to_delete.get('DATA_HORA','')) and str(m.get('TIPO',''))==str(row_to_delete.get('TIPO','')):
                                    st.session_state.mov.pop(i)
                                    break
                        salvar_tudo()
                        st.success(f"🗑️ APAGADO - ESTOQUE E GRAFICOS ATUALIZADOS AUTO - GUARDADO 100% - MOV:{len(st.session_state.mov)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro apagar: {e}")
        with c_apagar2:
            if st.button("🗑️ APAGAR ULTIMO REGISTRO - ENTRADA/SAIDA - RAPIDO", key="btn_apagar_ultimo"):
                if st.session_state.mov:
                    st.session_state.mov.pop()
                    salvar_tudo()
                    st.success(f"🗑️ ULTIMO APAGADO - ESTOQUE/GRAFICOS ATUALIZADOS AUTO - GUARDA 100% - MOV:{len(st.session_state.mov)}")
                    st.rerun()

with tab_est:
    st.header("5 - ESTOQUE - ATUALIZA AUTOMATICO APÓS ENTRADA/SAIDA - FORMATO DIGITAL")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista: st.info("Sem estoque - Faça ENTRADA/SAIDA na aba 4 - Atualiza auto")
    else:
        df_est=pd.DataFrame(lista)
        totais={}; ult={}
        for v in lista: totais[v['ID']]=totais.get(v['ID'],0)+v['SALDO']
        for m in st.session_state.mov:
            if m.get('TIPO')=="SAIDA":
                idp=str(m.get('ID','')).upper()
                dh=parse_data_hora(m.get('DATA_HORA',''))
                if idp not in ult or dh>ult[idp]['dt']: ult[idp]={'dt':dh,'data_hora':m.get('DATA_HORA','')}
        df_est['TOTAL_GERAL_ID']=df_est['ID'].apply(lambda x: totais.get(x,0))
        df_est['TOTAL_GERAL_ID_FORMATADO']=df_est['TOTAL_GERAL_ID'].apply(lambda x: f"{x:,.0f}")
        df_est['UNIDADE_MEDIDA']=df_est['TIPO_EMBALAGEM']
        df_est['DATA_ULTIMA_RETIRADA_BRASILIA']=df_est['ID'].apply(lambda x: ult.get(x,{}).get('data_hora','SEM RETIRADA')+" BRASÍLIA" if x in ult else "SEM RETIRADA BRASÍLIA")
        df_est['DATA_HORA_ULTIMA_ATUALIZACAO']=df_est['ULT_ATUAL']
        df_est['AGORA_BRASILIA']=agora.strftime("%d/%m/%Y %H:%M:%S")+" BRASÍLIA"
        st.dataframe(df_est[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','UNIDADE_MEDIDA','LOTE','LOCAL','EMBALAGENS','SALDO','TOTAL_GERAL_ID','TOTAL_GERAL_ID_FORMATADO','DATA_ULTIMA_RETIRADA_BRASILIA','DATA_HORA_ULTIMA_ATUALIZACAO','AGORA_BRASILIA']].sort_values(by=['ID','DESCRICAO']), use_container_width=True, height=600)
        st.metric("SALDO TOTAL - ATUALIZA AUTO APÓS ENTRADA/SAIDA", f"{df_est['SALDO'].sum():,.0f}")

with tab_busca:
    st.header("6 - BUSCA ID - ATUALIZA AUTO")
    id_b=st.text_input("ID BUSCA", key="busca_id_final")
    if id_b:
        saldos,_=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper().strip() and v['SALDO']>0]
        if lista: st.dataframe(pd.DataFrame(lista), use_container_width=True)

with tab_grd:
    st.header(f"7 - GRD - VOCE DECIDE HORAS - {st.session_state.tempo_quarentena}H - ATUALIZA AUTO")
    c1,c2=st.columns([3,1])
    with c1: nova_hora=st.number_input("⏰ VOCE DECIDE HORAS", min_value=1, max_value=720, value=int(st.session_state.tempo_quarentena), step=1)
    with c2:
        if st.button("SALVAR HORAS"): st.session_state.tempo_quarentena=int(nova_hora); st.rerun()
    total_sala,pend,disp=get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    if total_sala: st.dataframe(pd.DataFrame(list(total_sala.values()))[['ID','DESCRICAO','LOTE','SALDO']], use_container_width=True)
    if st.session_state.grd: st.dataframe(df_safe_sort(pd.DataFrame(st.session_state.grd), False), use_container_width=True)

with tab_graf:
    st.header(f"8 - GRAFICO - ATUALIZA AUTOMATICO APÓS ENTRADA/SAIDA - BARRAS EMPILHADAS CORES + DATA/HORA BRASÍLIA + NUMEROS GRANDES - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista: st.warning("Sem estoque - Faça ENTRADA/SAIDA na aba 4 - Grafico atualiza auto")
    else:
        df_estoque=pd.DataFrame(lista)
        ultimas={}
        for m in st.session_state.mov:
            try:
                chave=f"{str(m.get('ID','')).upper()}__{str(m.get('DESCRICAO','')).upper()}"
                dh=str(m.get('DATA_HORA','')); dtm=parse_data_hora(dh)
                if chave not in ultimas or dtm>ultimas[chave]['dt']: ultimas[chave]={'dt':dtm,'data_hora':dh+" BRASÍLIA"}
            except: continue
        df_estoque['CHAVE']=df_estoque['ID']+"__"+df_estoque['DESCRICAO']
        df_estoque['DATA_HORA_ULTIMA_BRASILIA']=df_estoque['CHAVE'].apply(lambda x: ultimas.get(x,{}).get('data_hora','SEM MOV'))
        df_estoque['TOTAL_GERAL_ID']=df_estoque.groupby('ID')['SALDO'].transform('sum')
        df_emp=df_estoque.groupby(['ID','DESCRICAO','LOCAL'],as_index=False)['SALDO'].sum()
        df_emp['TEXTO']=df_emp['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_ult=df_estoque.groupby(['ID','DESCRICAO'],as_index=False).agg({'DATA_HORA_ULTIMA_BRASILIA':'first','SALDO':'sum','TIPO_EMBALAGEM':'first','TOTAL_GERAL_ID':'first'}).rename(columns={'SALDO':'TOTAL_MAT'})
        df_emp=df_emp.merge(df_ult,on=['ID','DESCRICAO'],how='left')
        fig=px.bar(df_emp, x='ID', y='SALDO', color='DESCRICAO', text='TEXTO', barmode='stack', title=f"ESTOQUE ATUALIZADO AUTO APÓS ENTRADA/SAIDA - EMPILHADO CORES DIFERENTES - TOTAL GERAL ID + DATA/HORA BRASÍLIA - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA", hover_data=['TIPO_EMBALAGEM','DATA_HORA_ULTIMA_BRASILIA','TOTAL_GERAL_ID','TOTAL_MAT'], color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_traces(textposition='inside', textfont=dict(size=16, color='white', family='Arial Black'))
        fig.update_layout(height=700)
        st.plotly_chart(fig, use_container_width=True, key=f"graf_auto_{agora.strftime('%H%M%S')}")
        st.success(f"✅ GRAFICO ATUALIZADO AUTO APÓS ENTRADA/SAIDA - TOTAL GERAL ID + UNIDADE + DATA ULTIMA RETIRADA BRASÍLIA - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")

with tab_hist:
    st.header("9 - HISTORICO - COM APAGAR REGISTRO - ATUALIZA ESTOQUE/GRAFICOS AUTO - GUARDA 100%")
    if not st.session_state.mov: st.warning("Sem mov")
    else:
        df_all=pd.DataFrame(st.session_state.mov)
        st.dataframe(df_safe_sort(df_all, False), use_container_width=True, height=400)
        st.markdown("### 🗑️ APAGAR REGISTRO - HISTORICO - ATUALIZA AUTO")
        opcoes_hist=[f"{i} | {row.get('ID','')} - {row.get('DESCRICAO','')} - {row.get('LOTE','')} - {row.get('TIPO','')} - {row.get('TOTAL_QTD','')} - {row.get('DATA_HORA','')}" for i,row in df_all.iterrows()]
        sel_hist=st.selectbox("SELECIONE PARA APAGAR - HISTORICO", [""]+opcoes_hist, key="apagar_hist")
        if sel_hist:
            if st.button("🗑️ APAGAR SELECIONADO - HISTORICO - CONFIRMAR - ATUALIZA AUTO - GUARDA 100%", type="primary", key="btn_apagar_hist"):
                try:
                    idx=int(sel_hist.split(" | ")[0])
                    # Remove do mov
                    if 0 <= idx < len(st.session_state.mov):
                        st.session_state.mov.pop(idx)
                        salvar_tudo()
                        st.success(f"🗑️ APAGADO HISTORICO - ESTOQUE E GRAFICOS ATUALIZADOS AUTO - GUARDA 100% - MOV:{len(st.session_state.mov)}")
                        st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

st.caption(f"REFORMA FORNOS - ABA CADASTRO TEM QUE TER + ABA ENTRADA/SAIDA ATUALIZA ESTOQUE/GRAFICOS AUTO + APAGAR REGISTRO + GUARDA 100% MESMO SE DESLIGAR - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA - CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)} GRD:{len(st.session_state.grd)}")
