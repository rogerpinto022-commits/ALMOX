import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta, date
import plotly.express as px
from datetime import datetime as dt

st.set_page_config(page_title="REFORMA - SIMPLES + VALIDADE", layout="wide")
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
        if chave not in carac:
            carac[chave]={
                'ID':idp,'DESCRICAO':desc,
                'TIPO_EMBALAGEM':str(r.get('TIPO_EMBALAGEM','PALETE')).upper(),
                'QTD_POR_EMBALAGEM':safe_float(r.get('QTD_POR_EMBALAGEM',1250),1250),
                'MARCA':str(r.get('MARCA','')).upper(),
                'FABRICACAO':str(r.get('FABRICACAO','')),
                'VALIDADE_HORAS':safe_float(r.get('VALIDADE_HORAS',48),48),
                'DATA_FABRICACAO':str(r.get('DATA_FABRICACAO','')),
                'DATA_VALIDADE':str(r.get('DATA_VALIDADE',''))
            }
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
                saldos[chave]={
                    'ID':idp,'DESCRICAO':desc,'TIPO_EMBALAGEM':c['TIPO_EMBALAGEM'],'QTD_POR_EMBALAGEM':c['QTD_POR_EMBALAGEM'],
                    'LOCAL':local,'MARCA':c['MARCA'],'LOTE':lote,'SALDO':0,'EMBALAGENS':0,'ULT_ATUAL':'',
                    'FABRICACAO':c.get('FABRICACAO',''),'VALIDADE_HORAS':c.get('VALIDADE_HORAS',48),
                    'DATA_FABRICACAO':str(m.get('DATA_FABRICACAO','') or c.get('DATA_FABRICACAO','')),
                    'DATA_VALIDADE':str(m.get('DATA_VALIDADE','') or c.get('DATA_VALIDADE','')),
                    'DATA_FABRICACAO_MOV':str(m.get('DATA_FABRICACAO','')),
                    'DATA_VALIDADE_MOV':str(m.get('DATA_VALIDADE',''))
                }
            if chave not in saldos: continue
            if m.get('TIPO')=="ENTRADA":
                saldos[chave]['SALDO']+=safe_float(m.get('TOTAL_QTD',0))
                saldos[chave]['EMBALAGENS']+=safe_float(m.get('PALETES',0))
                saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
                # Atualiza fabricação/validade da movimentação
                if m.get('DATA_FABRICACAO'): saldos[chave]['DATA_FABRICACAO']=str(m.get('DATA_FABRICACAO'))
                if m.get('DATA_VALIDADE'): saldos[chave]['DATA_VALIDADE']=str(m.get('DATA_VALIDADE'))
                if m.get('VALIDADE_HORAS'): saldos[chave]['VALIDADE_HORAS']=safe_float(m.get('VALIDADE_HORAS'),48)
            else:
                saldos[chave]['SALDO']-=safe_float(m.get('TOTAL_QTD',0))
                saldos[chave]['EMBALAGENS']-=safe_float(m.get('PALETES',0))
                saldos[chave]['ULT_ATUAL']=str(m.get('DATA_HORA',''))
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
            # Usa validade da movimentação ou tempo que você decide
            validade_horas=safe_float(m.get('VALIDADE_HORAS',tempo_horas),tempo_horas)
            data_mov=parse_data_hora(m.get('DATA_HORA',''))
            diff=(agora_dt-data_mov).total_seconds()/3600
            if diff < validade_horas:
                q=safe_float(m.get('TOTAL_QTD',0))
                if chave not in pend: pend[chave]={'ID':idp,'DESCRICAO':desc,'LOTE':lote,'QTD_PENDENTE':q,'DATA_ENTRADA':str(m.get('DATA_HORA','')),'HORAS_RESTANTES':validade_horas-diff,'VALIDADE_HORAS':validade_horas,'DATA_LIBERACAO':data_mov+timedelta(hours=validade_horas)}
                else: pend[chave]['QTD_PENDENTE']+=q
                if chave in disp:
                    disp[chave]['SALDO']-=q
                    if disp[chave]['SALDO']<0: disp[chave]['SALDO']=0
        except: continue
    disp={k:v for k,v in disp.items() if v['SALDO']>0}
    return total,pend,disp

if 'inicializado' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD); st.session_state.mov=carregar(ARQ_MOV); st.session_state.grd=carregar(ARQ_GRD); st.session_state.inicializado=True
if 'tempo_quarentena' not in st.session_state: st.session_state.tempo_quarentena=48
if not os.path.exists(ARQ_EMAILS): pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'logado' not in st.session_state: st.session_state.logado=False
if 'usuario' not in st.session_state: st.session_state.usuario=None
if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA - COM FABRICAÇÃO E VALIDADE</h1>", unsafe_allow_html=True)
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
st.sidebar.metric("⏰ VOCE DECIDE VALIDADE", f"{st.session_state.tempo_quarentena}H")
st.sidebar.write(f"📦 CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
if st.session_state.cad: st.sidebar.download_button("BACKUP CAD", pd.DataFrame(st.session_state.cad).to_csv(index=False), "cad.csv")
if st.session_state.mov: st.sidebar.download_button("BACKUP MOV", pd.DataFrame(st.session_state.mov).to_csv(index=False), "mov.csv")
if st.sidebar.button("Sair"): salvar_tudo(); st.session_state.logado=False; st.rerun()

agora=datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - SIMPLES + FABRICAÇÃO E VALIDADE - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
tabs=st.tabs(["ADMIN","DASHBOARD","3 - CADASTRO + FABRICAÇÃO E VALIDADE","4 - ENTRADA/SAIDA SIMPLES + FABRICAÇÃO E VALIDADE","ESTOQUE + VALIDADE","BUSCA","GRD HORAS EDITAVEIS + VALIDADE","GRAFICO + VALIDADE","HISTORICO"])
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
    st.header("DASHBOARD - COM VALIDADE")
    total_sala,pend,disp=get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    saldos,_=get_saldos()
    if not total_sala: total_sala={k:v for k,v in saldos.items() if v['LOCAL']==LOCAL_SALA and v['SALDO']>0}
    df_total=pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    if not df_total.empty:
        st.dataframe(df_total[['ID','DESCRICAO','LOTE','SALDO','DATA_FABRICACAO','DATA_VALIDADE','VALIDADE_HORAS','ULT_ATUAL']], use_container_width=True)
        if pend:
            st.warning(f"⏳ EM QUARENTENA - VALIDADE - {len(pend)} LOTES - AGUARDANDO LIBERAÇÃO - VOCÊ DECIDE {st.session_state.tempo_quarentena}H")
            st.dataframe(pd.DataFrame(list(pend.values())), use_container_width=True)

# ========== ABA CADASTRO - COM FABRICAÇÃO E VALIDADE - VOLTOU ==========
with tab_cad:
    st.header("3 - ABA CADASTRO - COM DATA FABRICAÇÃO E TEMPO VALIDADE - VOLTOU")
    st.success("✅ CADASTRO: ID + DESCRIÇÃO + TIPO EMB + QTD + FABRICAÇÃO + VALIDADE - GUARDA 100%")
    id_in = st.text_input("ID* - DIGITE E ENTER - Ex: 15", key="cad_id_com_validade")
    if id_in:
        mats=[r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_in.upper()]
        if mats: st.dataframe(pd.DataFrame(mats)[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','DATA_FABRICACAO','VALIDADE_HORAS']].drop_duplicates(), use_container_width=True)

    with st.form("form_cad_com_validade"):
        st.markdown("### 🖥️ CADASTRO - COM FABRICAÇÃO E VALIDADE - SIMPLES")
        c1,c2=st.columns([1,2])
        with c1: id_form=st.text_input("ID*", value=id_in.upper() if id_in else "", key="id_form_validade")
        with c2: desc=st.text_input("DESCRIÇÃO* - Ex: TIJOLO 65%", key="desc_validade")
        c3,c4,c5=st.columns(3)
        with c3: tipo_emb=st.selectbox("TIPO EMBALAGEM*", TIPOS_EMBALAGEM, key="tipo_validade")
        with c4: qtd_emb=st.number_input("QTD POR EMBALAGEM*", min_value=0.1, value=1250.0, key="qtd_validade")
        with c5: marca=st.text_input("MARCA", key="marca_validade")

        st.markdown("### 📅 DATA FABRICAÇÃO E TEMPO VALIDADE - VOLTOU - VOCÊ DECIDE")
        cf1,cf2,cf3=st.columns(3)
        with cf1:
            data_fab=st.date_input("DATA FABRICAÇÃO* - Quando foi fabricado", value=date.today(), key="data_fab_validade")
            st.caption("Data que foi fabricado")
        with cf2:
            validade_horas=st.number_input("TEMPO VALIDADE HORAS* - VOCÊ DECIDE - Ex: 48H = 2 dias, 720H = 30 dias", min_value=1, max_value=8760, value=int(st.session_state.tempo_quarentena), step=1, key="validade_horas_cad")
            st.caption(f"Você decide: {validade_horas}H = {validade_horas/24:.1f} dias")
            data_validade_calc=data_fab + timedelta(hours=validade_horas)
            st.metric("DATA VALIDADE CALCULADA", data_validade_calc.strftime("%d/%m/%Y"))
        with cf3:
            st.markdown("**VALIDADE CALCULADA AUTO**")
            st.metric("FABRICAÇÃO", data_fab.strftime("%d/%m/%Y"))
            st.metric("VALIDADE", data_validade_calc.strftime("%d/%m/%Y %H:%M"))
            st.metric("TEMPO", f"{validade_horas}H = {validade_horas/24:.0f} dias")

        if st.form_submit_button("✅ CADASTRAR COM FABRICAÇÃO E VALIDADE - GUARDA 100%", type="primary", use_container_width=True):
            if not id_form or not desc: st.error("ID e DESCRIÇÃO obrigatórios")
            else:
                st.session_state.cad.append({
                    "ID":id_form.upper().strip(),"DESCRICAO":desc.upper(),"TIPO_EMBALAGEM":tipo_emb.upper(),
                    "QTD_POR_EMBALAGEM":qtd_emb,"MARCA":marca.upper() if marca else "SEM MARCA",
                    "FABRICACAO":data_fab.strftime("%d/%m/%Y"),"DATA_FABRICACAO":data_fab.strftime("%d/%m/%Y"),
                    "VALIDADE_HORAS":validade_horas,"DATA_VALIDADE":data_validade_calc.strftime("%d/%m/%Y %H:%M:%S"),
                    "FABRICACAO_COMPLETA":f"{data_fab.strftime('%d/%m/%Y')} - VALIDADE {validade_horas}H - ATÉ {data_validade_calc.strftime('%d/%m/%Y')}"
                })
                salvar_tudo()
                st.success(f"✅ CADASTRADO ID {id_form.upper()} - FAB {data_fab.strftime('%d/%m/%Y')} - VALIDADE {validade_horas}H - ATÉ {data_validade_calc.strftime('%d/%m/%Y')} - GUARDADO")
                st.balloons()
                st.rerun()

    if st.session_state.cad:
        df_all=pd.DataFrame(st.session_state.cad)
        df_all=df_all[df_all['DESCRICAO'].astype(str).str.strip()!=""]
        if not df_all.empty:
            st.dataframe(df_all[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','DATA_FABRICACAO','VALIDADE_HORAS','DATA_VALIDADE']].sort_values(by=['ID']).drop_duplicates(), use_container_width=True, height=300)
            opcoes=[f"{r['ID']} - {r['DESCRICAO']} - FAB {r.get('DATA_FABRICACAO','')} VAL {r.get('VALIDADE_HORAS','')}H" for _,r in df_all[['ID','DESCRICAO','DATA_FABRICACAO','VALIDADE_HORAS']].drop_duplicates().iterrows()]
            sel=st.selectbox("APAGAR CADASTRO", [""]+opcoes, key="apagar_cad_validade")
            if sel and st.button("🗑️ APAGAR CADASTRO COM VALIDADE", key="btn_apagar_cad_validade"):
                id_ap=sel.split(" - ")[0]
                desc_ap=sel.split(" - ")[1]
                st.session_state.cad=[r for r in st.session_state.cad if not (str(r.get('ID','')).upper()==id_ap and str(r.get('DESCRICAO','')).upper()==desc_ap)]
                salvar_tudo(); st.rerun()

# ========== ABA ENTRADA/SAIDA - SIMPLES + FABRICAÇÃO E VALIDADE ==========
with tab_mov:
    st.header("4 - ENTRADA / SAIDA - SIMPLES + COM FABRICAÇÃO E VALIDADE - QUALQUER PESSOA ENTENDE")
    st.info("👉 ID + ENTER > Digita QTD ENTRADA ou SAIDA > Digita FABRICAÇÃO e VALIDADE > Mostra TOTAL GERAL e ATUALIZA AUTO")

    st.markdown("### PASSO 1 - ID - DIGITE E ENTER")
    id_mov = st.text_input("ID* - DIGITE ID E ENTER - Ex: 15", placeholder="Digite ID cadastrado + ENTER", key="mov_id_validade")

    materiais_da_id=[]
    if id_mov:
        up=id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper().strip()==up and str(r.get('DESCRICAO','')).strip()!="":
                chave=f"{str(r.get('DESCRICAO','')).upper()}__{str(r.get('MARCA','')).upper()}"
                if chave not in [f"{m['DESCRICAO']}__{m['MARCA']}" for m in materiais_da_id]:
                    materiais_da_id.append({
                        'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'MARCA':str(r.get('MARCA','')).upper(),
                        'TIPO_EMBALAGEM':str(r.get('TIPO_EMBALAGEM','PALETE')).upper(),
                        'QTD_POR_EMBALAGEM':safe_float(r.get('QTD_POR_EMBALAGEM',1250),1250),
                        'VALIDADE_HORAS':safe_float(r.get('VALIDADE_HORAS',48),48),
                        'DATA_FABRICACAO':str(r.get('DATA_FABRICACAO',''))
                    })

    if not id_mov:
        st.markdown("""
        <div style='border:2px solid #00aa00; padding:20px; border-radius:10px; background:#eaffea;'>
        <h2>📦 SIMPLES + FABRICAÇÃO E VALIDADE:</h2>
        <p><b>1.</b> Digite ID e ENTER - Auto preenche</p>
        <p><b>2.</b> Digite QTD ENTRADA ou SAIDA</p>
        <p><b>3.</b> Digite DATA FABRICAÇÃO e VALIDADE HORAS - Você decide</p>
        <p><b>4.</b> Mostra TOTAL GERAL + UNIDADE + DATA ULTIMA RETIRADA BRASÍLIA + VALIDADE</p>
        </div>
        """, unsafe_allow_html=True)
    elif not materiais_da_id:
        st.error(f"ID {id_mov.upper()} NÃO CADASTRADO - Vá na ABA CADASTRO primeiro com FABRICAÇÃO e VALIDADE")
    else:
        if len(materiais_da_id)>1:
            opcoes=[f"{m['DESCRICAO']} - {m['MARCA']} - FAB {m['DATA_FABRICACAO']} VAL {m['VALIDADE_HORAS']:.0f}H" for m in materiais_da_id]
            escolha=st.selectbox(f"ID {id_mov.upper()} tem {len(materiais_da_id)} - escolha", opcoes, key="escolha_mat_validade")
            mat=materiais_da_id[opcoes.index(escolha)]
        else:
            mat=materiais_da_id[0]

        saldos,_=get_saldos()
        saldo_atual_id=sum([v['SALDO'] for v in saldos.values() if v['ID']==id_mov.upper()])
        ultima_retirada="SEM RETIRADA"
        for m in sorted(st.session_state.mov, key=lambda x: parse_data_hora(x.get('DATA_HORA','')), reverse=True):
            if str(m.get('ID','')).upper()==id_mov.upper() and m.get('TIPO')=="SAIDA":
                ultima_retirada=m.get('DATA_HORA','')+" BRASÍLIA"; break

        st.success(f"✅ ID {id_mov.upper()} - {mat['DESCRICAO']} - {mat['TIPO_EMBALAGEM']} {mat['QTD_POR_EMBALAGEM']:,.0f}/emb - FAB {mat['DATA_FABRICACAO']} VAL {mat['VALIDADE_HORAS']:.0f}H - ESTOQUE ATUAL {saldo_atual_id:,.0f}")

        st.markdown("### PASSO 2 - LOTE, LOCAL, FABRICAÇÃO E VALIDADE - SIMPLES")
        saldos_id=[v for v in saldos.values() if v['ID']==id_mov.upper() and v['DESCRICAO']==mat['DESCRICAO'] and v['SALDO']>0]
        lotes_existentes=list(set([v['LOTE'] for v in saldos_id]))

        c1,c2,c3,c4=st.columns(4)
        with c1:
            if lotes_existentes:
                lote_sel=st.selectbox("LOTE - Existente ou novo", lotes_existentes+["NOVO LOTE"], key="lote_validade")
                lote_final=st.text_input("NOVO LOTE", key="lote_novo_validade") if lote_sel=="NOVO LOTE" else lote_sel
            else:
                lote_final=st.text_input("LOTE* - Ex: LOTE-001", key="lote_validade2")
        with c2:
            local_final=st.selectbox("LOCAL", LOCAIS, key="local_validade")
        with c3:
            data_fab_mov=st.date_input("DATA FABRICAÇÃO* - Desta entrada", value=date.today(), key="data_fab_mov")
            st.caption(f"Fabricação: {data_fab_mov.strftime('%d/%m/%Y')}")
        with c4:
            validade_mov=st.number_input("VALIDADE HORAS* - Você decide", min_value=1, max_value=8760, value=int(mat['VALIDADE_HORAS'] if mat['VALIDADE_HORAS']>0 else st.session_state.tempo_quarentena), step=1, key="validade_mov")
            data_val_mov=data_fab_mov + timedelta(hours=validade_mov)
            st.metric("VALIDADE ATÉ", data_val_mov.strftime("%d/%m/%Y"))
            st.caption(f"{validade_mov}H = {validade_mov/24:.1f} dias")

        st.markdown("### PASSO 3 - ENTRADA E SAIDA - QUALQUER PESSOA ENTENDE - COM VALIDADE")
        col_entrada,col_saida,col_total=st.columns(3)

        with col_entrada:
            st.markdown("<div style='border:2px solid #0080ff; padding:15px; border-radius:10px; background:#e6f2ff; text-align:center;'><h3 style='color:#0080ff;'>📥 ENTRADA</h3><p>QTD RECEBIDA</p></div>", unsafe_allow_html=True)
            qtd_entrada_emb=st.number_input(f"QTD {mat['TIPO_EMBALAGEM']} RECEBIDA", min_value=0.0, value=0.0, step=1.0, key="entrada_qtd_validade")
            total_entrada=qtd_entrada_emb*mat['QTD_POR_EMBALAGEM']
            if qtd_entrada_emb>0:
                st.metric(f"ENTRADA - {qtd_entrada_emb} {mat['TIPO_EMBALAGEM']}", f"{total_entrada:,.0f}", delta=f"FAB {data_fab_mov.strftime('%d/%m/%Y')} VAL {validade_mov}H")

        with col_saida:
            st.markdown("<div style='border:2px solid #ff4444; padding:15px; border-radius:10px; background:#ffe6e6; text-align:center;'><h3 style='color:#ff4444;'>📤 SAIDA</h3><p>QTD RETIRADA</p></div>", unsafe_allow_html=True)
            qtd_saida_emb=st.number_input(f"QTD {mat['TIPO_EMBALAGEM']} RETIRADA", min_value=0.0, value=0.0, step=1.0, key="saida_qtd_validade")
            total_saida=qtd_saida_emb*mat['QTD_POR_EMBALAGEM']
            if qtd_saida_emb>0:
                st.metric(f"SAIDA - {qtd_saida_emb} {mat['TIPO_EMBALAGEM']}", f"{total_saida:,.0f}", delta="- Retirado", delta_color="inverse")

        with col_total:
            st.markdown("<div style='border:2px solid #00aa00; padding:15px; border-radius:10px; background:#e6ffe6; text-align:center;'><h3 style='color:#00aa00;'>📊 TOTAL GERAL + VALIDADE</h3></div>", unsafe_allow_html=True)
            if qtd_entrada_emb>0 and qtd_saida_emb==0:
                novo_total=saldo_atual_id+total_entrada
                st.metric(f"TOTAL GERAL ID {id_mov.upper()}", f"{novo_total:,.0f}", delta=f"+{total_entrada:,.0f}")
                st.caption(f"Unidade: {mat['TIPO_EMBALAGEM']} - {mat['QTD_POR_EMBALAGEM']:,.0f}/emb")
                st.caption(f"FAB: {data_fab_mov.strftime('%d/%m/%Y')} - VAL: {data_val_mov.strftime('%d/%m/%Y')} - {validade_mov}H")
                st.caption(f"Última retirada: {ultima_retirada}")
            elif qtd_saida_emb>0 and qtd_entrada_emb==0:
                novo_total=saldo_atual_id-total_saida
                st.metric(f"TOTAL GERAL ID {id_mov.upper()}", f"{novo_total:,.0f}", delta=f"-{total_saida:,.0f}", delta_color="inverse")
                st.caption(f"FAB: {data_fab_mov.strftime('%d/%m/%Y')} - VAL: {data_val_mov.strftime('%d/%m/%Y')}")
                st.caption(f"Última retirada: {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
            else:
                st.metric(f"TOTAL GERAL ID {id_mov.upper()} ATUAL", f"{saldo_atual_id:,.0f}")
                st.caption(f"FAB: {mat['DATA_FABRICACAO']} VAL: {mat['VALIDADE_HORAS']:.0f}H")
                st.caption(f"Última retirada: {ultima_retirada}")

        st.markdown("---")
        if qtd_entrada_emb>0 or qtd_saida_emb>0:
            if not lote_final or str(lote_final).strip()=="": st.error("Digite LOTE")
            else:
                if qtd_entrada_emb>0 and qtd_saida_emb>0: st.warning("Digite só ENTRADA ou só SAIDA por vez")
                elif qtd_entrada_emb>0:
                    if st.button(f"✅ CONFIRMAR ENTRADA {qtd_entrada_emb} {mat['TIPO_EMBALAGEM']} = {total_entrada:,.0f} - FAB {data_fab_mov.strftime('%d/%m/%Y')} VAL {validade_mov}H - GUARDA 100%", type="primary", use_container_width=True, key="btn_entrada_validade"):
                        agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                        base={"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_entrada_emb,"TOTAL_QTD":total_entrada,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO_EMBALAGEM'],"QTD_POR_EMBALAGEM":mat['QTD_POR_EMBALAGEM'],"LOCAL_MOV":local_final,"TIPO":"ENTRADA","DATA_FABRICACAO":data_fab_mov.strftime("%d/%m/%Y"),"DATA_VALIDADE":data_val_mov.strftime("%d/%m/%Y %H:%M:%S"),"VALIDADE_HORAS":validade_mov}
                        st.session_state.mov.append(base); salvar_tudo()
                        st.success(f"✅ ENTRADA GUARDADA FAB {data_fab_mov.strftime('%d/%m/%Y')} VAL {validade_mov}H ATÉ {data_val_mov.strftime('%d/%m/%Y')} - TOTAL GERAL {saldo_atual_id+total_entrada:,.0f} - ATUALIZA AUTO - GUARDA 100%")
                        st.balloons(); st.rerun()
                elif qtd_saida_emb>0:
                    if st.button(f"✅ CONFIRMAR SAIDA {qtd_saida_emb} {mat['TIPO_EMBALAGEM']} = {total_saida:,.0f} - FAB {data_fab_mov.strftime('%d/%m/%Y')} - GUARDA 100%", type="primary", use_container_width=True, key="btn_saida_validade"):
                        agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                        base={"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_saida_emb,"TOTAL_QTD":total_saida,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO_EMBALAGEM'],"QTD_POR_EMBALAGEM":mat['QTD_POR_EMBALAGEM'],"LOCAL_MOV":local_final,"TIPO":"SAIDA","DATA_FABRICACAO":data_fab_mov.strftime("%d/%m/%Y"),"DATA_VALIDADE":data_val_mov.strftime("%d/%m/%Y %H:%M:%S"),"VALIDADE_HORAS":validade_mov}
                        st.session_state.mov.append(base); salvar_tudo()
                        st.success(f"✅ SAIDA GUARDADA - ULTIMA RETIRADA {agora_str} BRASÍLIA - FAB {data_fab_mov.strftime('%d/%m/%Y')} VAL {validade_mov}H - TOTAL GERAL {saldo_atual_id-total_saida:,.0f} - ATUALIZA AUTO")
                        st.balloons(); st.rerun()

    st.divider()
    if st.session_state.mov:
        df_show=pd.DataFrame(st.session_state.mov).sort_values(by="DATA_HORA", ascending=False).head(15) if "DATA_HORA" in pd.DataFrame(st.session_state.mov).columns else pd.DataFrame(st.session_state.mov).head(15)
        st.dataframe(df_show[['ID','DESCRICAO','LOTE','TIPO','PALETES','TOTAL_QTD','DATA_FABRICACAO','VALIDADE_HORAS','DATA_VALIDADE','LOCAL_MOV','DATA_HORA']], use_container_width=True)
        opcoes_apagar=[f"{i} | {row.get('ID','')} - {row.get('LOTE','')} - {row.get('TIPO','')} - {row.get('TOTAL_QTD','')} - FAB {row.get('DATA_FABRICACAO','')} VAL {row.get('VALIDADE_HORAS','')}H - {row.get('DATA_HORA','')}" for i,row in df_show.iterrows()]
        sel=st.selectbox("APAGAR REGISTRO - Se errou", [""]+opcoes_apagar, key="apagar_mov_validade")
        if sel and st.button("🗑️ APAGAR - ATUALIZA AUTO - GUARDA 100%", key="btn_apagar_validade"):
            try:
                idx=int(sel.split(" | ")[0])
                row_del=df_show.loc[idx] if idx in df_show.index else None
                if row_del is not None:
                    for j,m in enumerate(st.session_state.mov):
                        if str(m.get('DATA_HORA',''))==str(row_del.get('DATA_HORA','')) and str(m.get('ID','')).upper()==str(row_del.get('ID','')).upper():
                            st.session_state.mov.pop(j); break
                    salvar_tudo(); st.success("APAGADO - ATUALIZADO AUTO"); st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

with tab_est:
    st.header("ESTOQUE - COM FABRICAÇÃO E VALIDADE - ATUALIZA AUTO")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista: st.info("Sem estoque")
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
        st.dataframe(df_est[['ID','DESCRICAO','TIPO_EMBALAGEM','QTD_POR_EMBALAGEM','LOTE','LOCAL','SALDO','TOTAL_GERAL_ID','DATA_FABRICACAO','VALIDADE_HORAS','DATA_VALIDADE','DATA_ULTIMA_RETIRADA_BRASILIA','ULT_ATUAL','AGORA_BRASILIA']].sort_values(by=['ID']), use_container_width=True, height=500)
        st.metric("TOTAL GERAL", f"{df_est['SALDO'].sum():,.0f}")

with tab_busca:
    st.header("BUSCA ID")
    id_b=st.text_input("ID BUSCA", key="busca_validade")
    if id_b:
        saldos,_=get_saldos()
        lista=[v for v in saldos.values() if v['ID']==id_b.upper().strip() and v['SALDO']>0]
        if lista: st.dataframe(pd.DataFrame(lista), use_container_width=True)

with tab_grd:
    st.header(f"GRD - COM FABRICAÇÃO E VALIDADE - VOCÊ DECIDE HORAS - {st.session_state.tempo_quarentena}H - VOLTOU")
    c1,c2=st.columns([3,1])
    with c1: nova_hora=st.number_input("⏰ VOCÊ DECIDE HORAS VALIDADE - TEMPO QUARENTENA - Ex: 48H = 2 dias", min_value=1, max_value=8760, value=int(st.session_state.tempo_quarentena), step=1, key="tempo_quarentena_validade")
    with c2:
        if st.button("💾 SALVAR HORAS - VOCÊ DECIDE", type="primary"): st.session_state.tempo_quarentena=int(nova_hora); st.success(f"Você decidiu {nova_hora}H = {nova_hora/24:.1f} dias"); st.rerun()
    total_sala,pend,disp=get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    if total_sala: st.dataframe(pd.DataFrame(list(total_sala.values()))[['ID','DESCRICAO','LOTE','SALDO','DATA_FABRICACAO','VALIDADE_HORAS','DATA_VALIDADE']], use_container_width=True)
    if pend:
        st.warning(f"⏳ QUARENTENA - VALIDADE - {len(pend)} LOTES - AGUARDANDO {st.session_state.tempo_quarentena}H - VOCÊ DECIDIU")
        st.dataframe(pd.DataFrame(list(pend.values())), use_container_width=True)
    if st.session_state.grd: st.dataframe(pd.DataFrame(st.session_state.grd), use_container_width=True)

with tab_graf:
    st.header(f"GRAFICO - COM FABRICAÇÃO E VALIDADE - ATUALIZA AUTO - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df_estoque=pd.DataFrame(lista)
        df_emp=df_estoque.groupby(['ID','DESCRICAO'],as_index=False)['SALDO'].sum()
        df_emp['TEXTO']=df_emp['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_emp=df_emp.merge(df_estoque[['ID','DESCRICAO','DATA_FABRICACAO','VALIDADE_HORAS']].drop_duplicates(), on=['ID','DESCRICAO'], how='left')
        fig=px.bar(df_emp, x='ID', y='SALDO', color='DESCRICAO', text='TEXTO', barmode='stack', title=f"TOTAL GERAL ID + FABRICAÇÃO E VALIDADE - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA", hover_data=['DATA_FABRICACAO','VALIDADE_HORAS'])
        fig.update_traces(textposition='inside', textfont=dict(size=14, color='white'))
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    st.header("HISTORICO - COM FABRICAÇÃO E VALIDADE")
    if st.session_state.mov: st.dataframe(pd.DataFrame(st.session_state.mov).sort_values(by="DATA_HORA", ascending=False) if "DATA_HORA" in pd.DataFrame(st.session_state.mov).columns else pd.DataFrame(st.session_state.mov), use_container_width=True, height=500)

st.caption(f"SIMPLES + FABRICAÇÃO E VALIDADE - VOLTOU - VOCÊ DECIDE HORAS - GUARDA 100% - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASÍLIA - CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
