import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
import plotly.express as px
from datetime import datetime as dt

st.set_page_config(page_title="REFORMA - ENTRADA SAIDA SIMPLES", layout="wide")
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
    except: return False
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
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'TIPO_EMBALAGEM':c['TIPO_EMBALAGEM'],'QTD_POR_EMBALAGEM':c['QTD_POR_EMBALAGEM'],'LOCAL':local,'MARCA':c['MARCA'],'LOTE':lote,'SALDO':0,'EMBALAGENS':0,'ULT_ATUAL':''}
            if chave not in saldos: continue
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0)); saldos[chave]['EMBALAGENS']+=safe_float(m.get('PALETES',0)); saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
            else: saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0)); saldos[chave]['EMBALAGENS']-=safe_float(m.get('PALETES',0)); saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
        except: continue
    return saldos, carac

if 'inicializado' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD); st.session_state.mov=carregar(ARQ_MOV); st.session_state.grd=carregar(ARQ_GRD); st.session_state.inicializado=True
if 'tempo_quarentena' not in st.session_state: st.session_state.tempo_quarentena=48
if not os.path.exists(ARQ_EMAILS): pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'logado' not in st.session_state: st.session_state.logado=False
if 'usuario' not in st.session_state: st.session_state.usuario=None
if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA DE FORNOS - SIMPLES - QUALQUER PESSOA ENTENDE</h1>", unsafe_allow_html=True)
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS,dtype=str).fillna(""); df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
        u=df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
        if not u.empty: st.session_state.logado=True; st.session_state.usuario=u.iloc[0].to_dict(); st.rerun()
        else: st.error("Invalido")
    st.stop()

user=st.session_state.usuario
is_admin=str(user.get('EMAIL','')).lower()=="admin@admin.com"
st.sidebar.write(f"Logado: {user.get('NOME')}")
st.sidebar.metric("ESTOQUE TOTAL", f"{sum([v['SALDO'] for v in get_saldos()[0].values() if v['SALDO']>0]):,.0f}")
st.sidebar.write(f"📦 CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
if st.session_state.cad: st.sidebar.download_button("BAIXAR BACKUP CAD", pd.DataFrame(st.session_state.cad).to_csv(index=False), "cad.csv")
if st.session_state.mov: st.sidebar.download_button("BAIXAR BACKUP MOV", pd.DataFrame(st.session_state.mov).to_csv(index=False), "mov.csv")
up_cad=st.sidebar.file_uploader("Restaurar CAD se desligar", type="csv", key="up_cad")
if up_cad:
    try: df=pd.read_csv(up_cad,dtype=str).fillna(""); st.session_state.cad=df.to_dict('records'); salvar_tudo(); st.sidebar.success("Restaurado"); st.rerun()
    except: pass
if st.sidebar.button("Sair"): salvar_tudo(); st.session_state.logado=False; st.rerun()

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - SIMPLES - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
tabs=st.tabs(["ADMIN","DASHBOARD","3 - CADASTRO","4 - ENTRADA / SAIDA - SIMPLES - QUALQUER PESSOA ENTENDE","ESTOQUE","BUSCA","GRD","GRAFICO","HISTORICO"])
tab_admin, tab_dash, tab_cad, tab_mov, tab_est, tab_busca, tab_grd, tab_graf, tab_hist = tabs

with tab_admin:
    st.header("ADMIN")
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
    st.header("DASHBOARD")
    saldos,_=get_saldos()
    df_total=pd.DataFrame([v for v in saldos.values() if v['SALDO']>0]) if saldos else pd.DataFrame()
    if not df_total.empty: st.dataframe(df_total[['ID','DESCRICAO','LOTE','SALDO','ULT_ATUAL']], use_container_width=True)

# ========== ABA CADASTRO - SIMPLES ==========
with tab_cad:
    st.header("3 - ABA CADASTRO - CARACTERISTICAS - SIMPLES")
    st.success("✅ CADASTRE AQUI: ID + DESCRIÇÃO + TIPO EMBALAGEM + QTD POR EMBALAGEM")
    id_in = st.text_input("ID* - Ex: 15 - DIGITE E ENTER", key="cad_id_simples")
    if id_in:
        mats=[r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_in.upper()]
        if mats: st.dataframe(pd.DataFrame(mats)[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM']].drop_duplicates(), use_container_width=True)
    with st.form("form_cad_simples"):
        c1,c2=st.columns([1,2])
        with c1: id_form=st.text_input("ID*", value=id_in.upper() if id_in else "", key="id_form_simples")
        with c2: desc=st.text_input("DESCRIÇÃO* - Ex: TIJOLO 65%", key="desc_simples")
        c3,c4,c5=st.columns(3)
        with c3: tipo_emb=st.selectbox("TIPO EMBALAGEM*", TIPOS_EMBALAGEM, key="tipo_simples")
        with c4: qtd_emb=st.number_input("QTD POR EMBALAGEM*", min_value=0.1, value=1250.0, key="qtd_simples")
        with c5: marca=st.text_input("MARCA", key="marca_simples")
        if st.form_submit_button("✅ CADASTRAR - GUARDA 100%", type="primary", use_container_width=True):
            if not id_form or not desc: st.error("ID e DESCRIÇÃO obrigatórios")
            else:
                st.session_state.cad.append({"ID":id_form.upper().strip(),"DESCRICAO":desc.upper(),"TIPO_EMBALAGEM":tipo_emb.upper(),"QTD_POR_EMBALAGEM":qtd_emb,"MARCA":marca.upper() if marca else "SEM MARCA","FABRICACAO":agora.strftime("%d/%m/%Y %H:%M:%S")})
                salvar_tudo(); st.success(f"✅ ID {id_form.upper()} GUARDADO - NÃO PERDE"); st.rerun()
    if st.session_state.cad:
        df_all=pd.DataFrame(st.session_state.cad)
        df_all=df_all[df_all['DESCRICAO'].astype(str).str.strip()!=""]
        if not df_all.empty:
            st.dataframe(df_all[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','MARCA']].sort_values(by=['ID']).drop_duplicates(), use_container_width=True)
            # APAGAR CADASTRO
            opcoes=[f"{r['ID']} - {r['DESCRICAO']}" for _,r in df_all[['ID','DESCRICAO']].drop_duplicates().iterrows()]
            sel=st.selectbox("APAGAR CADASTRO - Selecione", [""]+opcoes, key="apagar_cad_simples")
            if sel and st.button("🗑️ APAGAR CADASTRO", key="btn_apagar_cad_simples"):
                id_ap=sel.split(" - ")[0]
                desc_ap=sel.split(" - ")[1]
                st.session_state.cad=[r for r in st.session_state.cad if not (str(r.get('ID','')).upper()==id_ap and str(r.get('DESCRICAO','')).upper()==desc_ap)]
                salvar_tudo(); st.rerun()

# ========== ABA 4 - ENTRADA / SAIDA - SUPER SIMPLES - QUALQUER PESSOA ENTENDE ==========
with tab_mov:
    st.header("4 - ENTRADA / SAIDA - SUPER SIMPLES - QUALQUER PESSOA ENTENDE")
    st.info("👉 DIGITE ID + ENTER > DIGITE QTD EM ENTRADA OU SAIDA > MOSTRA TOTAL GERAL E ATUALIZA ESTOQUE AUTO")

    # PASSO 1 - ID
    st.markdown("### PASSO 1 - DIGITE ID E APERTE ENTER")
    id_mov = st.text_input("ID* - DIGITE ID CADASTRADO E ENTER - Ex: 15", placeholder="Digite ID e pressione ENTER", key="mov_id_simples")

    materiais_da_id=[]
    if id_mov:
        up=id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==up and str(r.get('DESCRICAO','')).strip()!="":
                chave=f"{str(r.get('DESCRICAO','')).upper()}__{str(r.get('MARCA','')).upper()}"
                if chave not in [f"{m['DESCRICAO']}__{m['MARCA']}" for m in materiais_da_id]:
                    materiais_da_id.append({'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'MARCA':str(r.get('MARCA','')).upper(),'TIPO_EMBALAGEM':str(r.get('TIPO_EMBALAGEM','PALETE')).upper(),'QTD_POR_EMBALAGEM':safe_float(r.get('QTD_POR_EMBALAGEM',1250),1250)})

    if not id_mov:
        st.markdown("""
        <div style='border:2px solid #00aa00; padding:20px; border-radius:10px; background:#eaffea;'>
        <h2>📦 COMO USAR - SUPER SIMPLES:</h2>
        <p><b>1.</b> Digite ID (Ex: 15) e ENTER</p>
        <p><b>2.</b> Sistema mostra material automaticamente</p>
        <p><b>3.</b> Digite QTD em ENTRADA (recebeu) ou SAIDA (retirou)</p>
        <p><b>4.</b> Sistema mostra TOTAL GERAL e atualiza estoque sozinho</p>
        </div>
        """, unsafe_allow_html=True)
    elif not materiais_da_id:
        st.error(f"ID {id_mov.upper()} NÃO CADASTRADO - Vá na ABA CADASTRO primeiro")
    else:
        # Se tem mais de 1 material na mesma ID
        if len(materiais_da_id)>1:
            opcoes=[f"{m['DESCRICAO']} - {m['MARCA']}" for m in materiais_da_id]
            escolha=st.selectbox(f"ID {id_mov.upper()} tem {len(materiais_da_id)} materiais - escolha", opcoes, key="escolha_mat_simples")
            mat=materiais_da_id[opcoes.index(escolha)]
        else:
            mat=materiais_da_id[0]

        # Calcula saldo atual e ultima retirada
        saldos,_=get_saldos()
        saldo_atual_id=sum([v['SALDO'] for v in saldos.values() if v['ID']==id_mov.upper()])
        ultima_retirada="SEM RETIRADA"
        for m in sorted(st.session_state.mov, key=lambda x: parse_data_hora(x.get('DATA_HORA','')), reverse=True):
            if str(m.get('ID','')).upper()==id_mov.upper() and m.get('TIPO')=="SAIDA":
                ultima_retirada=m.get('DATA_HORA','')+" BRASÍLIA"; break

        st.success(f"✅ MATERIAL ENCONTRADO: ID {id_mov.upper()} - {mat['DESCRICAO']} - {mat['TIPO_EMBALAGEM']} {mat['QTD_POR_EMBALAGEM']:,.0f} por emb - ESTOQUE ATUAL: {saldo_atual_id:,.0f}")

        st.markdown("---")
        st.markdown("### PASSO 2 - DIGITE QTD RECEBIDA OU RETIRADA - SIMPLES")

        # Lote e local simplificados
        saldos_id=[v for v in saldos.values() if v['ID']==id_mov.upper() and v['DESCRICAO']==mat['DESCRICAO'] and v['SALDO']>0]
        lotes_existentes=list(set([v['LOTE'] for v in saldos_id]))

        col_lote,col_local=st.columns(2)
        with col_lote:
            if lotes_existentes:
                lote_sel=st.selectbox("LOTE - Escolha existente ou novo", lotes_existentes+["NOVO LOTE"], key="lote_simples")
                lote_final=st.text_input("NOVO LOTE - Digite", key="lote_novo_simples") if lote_sel=="NOVO LOTE" else lote_sel
            else:
                lote_final=st.text_input("LOTE* - Digite lote", placeholder="Ex: LOTE-001", key="lote_simples2")
        with col_local:
            local_final=st.selectbox("LOCAL - Onde está", LOCAIS, key="local_simples")

        st.markdown("---")
        st.markdown("### PASSO 3 - ENTRADA E SAIDA - QUALQUER PESSOA ENTENDE")

        # FORMATO SIMPLES - ENTRADA E SAIDA LADO A LADO
        col_entrada,col_saida,col_total=st.columns(3)

        with col_entrada:
            st.markdown("""
            <div style='border:2px solid #0080ff; padding:15px; border-radius:10px; background:#e6f2ff; text-align:center;'>
            <h3 style='color:#0080ff;'>📥 ENTRADA</h3>
            <p>QTD RECEBIDA</p>
            </div>
            """, unsafe_allow_html=True)
            qtd_entrada_emb=st.number_input(f"QTD {mat['TIPO_EMBALAGEM']} RECEBIDA - Digite só QTD", min_value=0.0, value=0.0, step=1.0, key="entrada_qtd_simples")
            total_entrada=qtd_entrada_emb*mat['QTD_POR_EMBALAGEM']
            if qtd_entrada_emb>0:
                st.metric(f"ENTRADA - {qtd_entrada_emb} {mat['TIPO_EMBALAGEM']}", f"{total_entrada:,.0f}", delta="Recebido")

        with col_saida:
            st.markdown("""
            <div style='border:2px solid #ff4444; padding:15px; border-radius:10px; background:#ffe6e6; text-align:center;'>
            <h3 style='color:#ff4444;'>📤 SAIDA</h3>
            <p>QTD RETIRADA</p>
            </div>
            """, unsafe_allow_html=True)
            qtd_saida_emb=st.number_input(f"QTD {mat['TIPO_EMBALAGEM']} RETIRADA - Digite só QTD", min_value=0.0, value=0.0, step=1.0, key="saida_qtd_simples")
            total_saida=qtd_saida_emb*mat['QTD_POR_EMBALAGEM']
            if qtd_saida_emb>0:
                st.metric(f"SAIDA - {qtd_saida_emb} {mat['TIPO_EMBALAGEM']}", f"{total_saida:,.0f}", delta="- Retirado", delta_color="inverse")

        with col_total:
            st.markdown("""
            <div style='border:2px solid #00aa00; padding:15px; border-radius:10px; background:#e6ffe6; text-align:center;'>
            <h3 style='color:#00aa00;'>📊 TOTAL GERAL</h3>
            <p>ESTOQUE ATUALIZADO AUTO</p>
            </div>
            """, unsafe_allow_html=True)
            # Calcula novo total
            if qtd_entrada_emb>0 and qtd_saida_emb==0:
                novo_total=saldo_atual_id+total_entrada
                st.metric(f"TOTAL GERAL ID {id_mov.upper()} - {mat['TIPO_EMBALAGEM']}", f"{novo_total:,.0f}", delta=f"+{total_entrada:,.0f}")
                st.caption(f"Unidade: {mat['TIPO_EMBALAGEM']} - {mat['QTD_POR_EMBALAGEM']:,.0f}/emb")
                st.caption(f"Última retirada: {ultima_retirada}")
                st.caption(f"Agora Brasília: {agora.strftime('%d/%m/%Y %H:%M:%S')}")
            elif qtd_saida_emb>0 and qtd_entrada_emb==0:
                novo_total=saldo_atual_id-total_saida
                st.metric(f"TOTAL GERAL ID {id_mov.upper()} - {mat['TIPO_EMBALAGEM']}", f"{novo_total:,.0f}", delta=f"-{total_saida:,.0f}", delta_color="inverse")
                st.caption(f"Unidade: {mat['TIPO_EMBALAGEM']}")
                st.caption(f"Última retirada: {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
            else:
                st.metric(f"TOTAL GERAL ID {id_mov.upper()} - ATUAL", f"{saldo_atual_id:,.0f}")
                st.caption(f"Unidade: {mat['TIPO_EMBALAGEM']} - {mat['QTD_POR_EMBALAGEM']:,.0f} por {mat['TIPO_EMBALAGEM']}")
                st.caption(f"Última retirada: {ultima_retirada}")

        st.markdown("---")

        # BOTAO CONFIRMAR - SIMPLES
        if qtd_entrada_emb>0 or qtd_saida_emb>0:
            if not lote_final or str(lote_final).strip()=="":
                st.error("❌ Digite LOTE - Obrigatório")
            else:
                if qtd_entrada_emb>0 and qtd_saida_emb>0:
                    st.warning("⚠️ Digite só ENTRADA ou só SAIDA por vez - não os dois juntos")
                elif qtd_entrada_emb>0:
                    if st.button(f"✅ CONFIRMAR ENTRADA - {qtd_entrada_emb} {mat['TIPO_EMBALAGEM']} = {total_entrada:,.0f} - ATUALIZA ESTOQUE AUTO - GUARDA 100%", type="primary", use_container_width=True, key="btn_entrada_simples"):
                        agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                        base={"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_entrada_emb,"TOTAL_QTD":total_entrada,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO_EMBALAGEM'],"QTD_POR_EMBALAGEM":mat['QTD_POR_EMBALAGEM'],"LOCAL_MOV":local_final,"TIPO":"ENTRADA"}
                        st.session_state.mov.append(base)
                        salvar_tudo()
                        st.success(f"✅ ENTRADA GUARDADA - {total_entrada:,.0f} - TOTAL GERAL ID {id_mov.upper()} AGORA {saldo_atual_id+total_entrada:,.0f} {mat['TIPO_EMBALAGEM']} - ESTOQUE E GRAFICOS ATUALIZADOS AUTO - NÃO PERDE SE DESLIGAR")
                        st.balloons()
                        st.rerun()
                elif qtd_saida_emb>0:
                    if qtd_saida_emb>sum([v['EMBALAGENS'] for v in saldos_id]):
                        st.error(f"❌ SAIDA maior que estoque - Estoque atual {saldo_atual_id:,.0f} - Tentando retirar {total_saida:,.0f}")
                    else:
                        if st.button(f"✅ CONFIRMAR SAIDA - {qtd_saida_emb} {mat['TIPO_EMBALAGEM']} = {total_saida:,.0f} - ATUALIZA ESTOQUE AUTO - GUARDA 100%", type="primary", use_container_width=True, key="btn_saida_simples"):
                            agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                            base={"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_saida_emb,"TOTAL_QTD":total_saida,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO_EMBALAGEM'],"QTD_POR_EMBALAGEM":mat['QTD_POR_EMBALAGEM'],"LOCAL_MOV":local_final,"TIPO":"SAIDA"}
                            st.session_state.mov.append(base)
                            salvar_tudo()
                            st.success(f"✅ SAIDA GUARDADA - {total_saida:,.0f} - TOTAL GERAL ID {id_mov.upper()} AGORA {saldo_atual_id-total_saida:,.0f} {mat['TIPO_EMBALAGEM']} - DATA ULTIMA RETIRADA {agora_str} BRASÍLIA - ESTOQUE E GRAFICOS ATUALIZADOS AUTO - NÃO PERDE")
                            st.balloons()
                            st.rerun()

    st.divider()
    st.subheader("📋 ÚLTIMAS MOVIMENTAÇÕES - COM APAGAR - SIMPLES")
    if st.session_state.mov:
        df_show=pd.DataFrame(st.session_state.mov).sort_values(by="DATA_HORA", ascending=False).head(15) if "DATA_HORA" in pd.DataFrame(st.session_state.mov).columns else pd.DataFrame(st.session_state.mov).head(15)
        st.dataframe(df_show[['ID','DESCRICAO','LOTE','TIPO','PALETES','TOTAL_QTD','LOCAL_MOV','DATA_HORA']], use_container_width=True)
        st.markdown("### 🗑️ APAGAR REGISTRO - SIMPLES")
        opcoes_apagar=[f"{i} | {row.get('ID','')} - {row.get('DESCRICAO','')} - {row.get('LOTE','')} - {row.get('TIPO','')} - {row.get('TOTAL_QTD','')} - {row.get('DATA_HORA','')}" for i,row in df_show.iterrows()]
        sel=st.selectbox("Selecione para apagar - Se errou", [""]+opcoes_apagar, key="apagar_mov_simples")
        if sel:
            col1,col2=st.columns(2)
            with col1:
                if st.button("🗑️ APAGAR SELECIONADO - ATUALIZA ESTOQUE AUTO", type="primary", key="btn_apagar_simples"):
                    try:
                        idx=int(sel.split(" | ")[0])
                        # Acha e remove
                        row_del=df_show.loc[idx] if idx in df_show.index else None
                        if row_del is not None:
                            for j,m in enumerate(st.session_state.mov):
                                if str(m.get('DATA_HORA',''))==str(row_del.get('DATA_HORA','')) and str(m.get('ID','')).upper()==str(row_del.get('ID','')).upper() and str(m.get('LOTE','')).upper()==str(row_del.get('LOTE','')).upper():
                                    st.session_state.mov.pop(j); break
                            salvar_tudo(); st.success("🗑️ APAGADO - ESTOQUE ATUALIZADO AUTO - GUARDA 100%"); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
            with col2:
                if st.button("🗑️ APAGAR ÚLTIMO - RÁPIDO", key="btn_apagar_ultimo_simples"):
                    if st.session_state.mov:
                        st.session_state.mov.pop(); salvar_tudo(); st.success("🗑️ ÚLTIMO APAGADO - ATUALIZADO AUTO"); st.rerun()

with tab_est:
    st.header("ESTOQUE - ATUALIZA AUTO APÓS ENTRADA/SAIDA - SIMPLES")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista: st.info("Sem estoque - Faça ENTRADA na ABA 4 - Simples")
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
        df_est['DATA_ULTIMA_RETIRADA_BRASILIA']=df_est['ID'].apply(lambda x: ult.get(x,{}).get('data_hora','SEM RETIRADA')+" BRASÍLIA" if x in ult else "SEM RETIRADA")
        df_est['AGORA_BRASILIA']=agora.strftime("%d/%m/%Y %H:%M:%S")+" BRASÍLIA"
        st.dataframe(df_est[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','LOTE','LOCAL','SALDO','TOTAL_GERAL_ID','DATA_ULTIMA_RETIRADA_BRASILIA']].sort_values(by=['ID']), use_container_width=True)
        st.metric("TOTAL GERAL - ATUALIZA AUTO", f"{df_est['SALDO'].sum():,.0f}")

with tab_busca:
    st.header("BUSCA ID - SIMPLES")
    id_b=st.text_input("ID BUSCA", key="busca_simples")
    if id_b:
        saldos,_=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper().strip() and v['SALDO']>0]
        if lista: st.dataframe(pd.DataFrame(lista), use_container_width=True)

with tab_grd:
    st.header("GRD")
    c1,c2=st.columns([3,1])
    with c1: nova_hora=st.number_input("HORAS", min_value=1, max_value=720, value=int(st.session_state.tempo_quarentena))
    with c2:
        if st.button("SALVAR HORAS"): st.session_state.tempo_quarentena=int(nova_hora); st.rerun()
    if st.session_state.grd: st.dataframe(pd.DataFrame(st.session_state.grd), use_container_width=True)

with tab_graf:
    st.header(f"GRAFICO - ATUALIZA AUTO - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df_estoque=pd.DataFrame(lista)
        df_emp=df_estoque.groupby(['ID','DESCRICAO'],as_index=False)['SALDO'].sum()
        df_emp['TEXTO']=df_emp['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df_emp, x='ID', y='SALDO', color='DESCRICAO', text='TEXTO', barmode='stack', title=f"TOTAL GERAL POR ID - ATUALIZA AUTO - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
        fig.update_traces(textposition='inside', textfont=dict(size=14, color='white'))
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    st.header("HISTORICO")
    if st.session_state.mov: st.dataframe(pd.DataFrame(st.session_state.mov).sort_values(by="DATA_HORA", ascending=False) if "DATA_HORA" in pd.DataFrame(st.session_state.mov).columns else pd.DataFrame(st.session_state.mov), use_container_width=True)

st.caption(f"SIMPLES - QUALQUER PESSOA ENTENDE - ENTRADA/SAIDA DIGITA QTD RECEBIDA/RETIRADA - MOSTRA TOTAL GERAL E ATUALIZA ESTOQUE AUTO - GUARDA 100% - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA - CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
