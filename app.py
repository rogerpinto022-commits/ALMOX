import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
import plotly.express as px
from datetime import datetime as dt

# ========== CONFIG ==========
st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide")
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
TEMPO_QUARENTENA_PADRAO = 48

# ========== FUNCOES BASE ==========
def safe_float(v, d=0.0):
    try:
        if v is None or str(v).strip() == "": return float(d)
        return float(str(v).replace(",", "."))
    except: return float(d)

def parse_data_hora(valor):
    try:
        if valor is None or str(valor).strip() == "": return dt.now(fuso).replace(tzinfo=None)
        s = str(valor).strip()
        if " " in s and ":" in s:
            try: return dt.strptime(s, "%d/%m/%Y %H:%M:%S")
            except: return dt.strptime(s, "%d/%m/%Y %H:%M")
    except: pass
    try: return dt.strptime(str(valor).split(" ")[0], "%d/%m/%Y")
    except: return dt.now(fuso).replace(tzinfo=None)

def carregar(caminho):
    if not os.path.exists(caminho): return []
    try: df = pd.read_csv(caminho, dtype=str, encoding='utf-8').fillna("")
    except:
        try: df = pd.read_csv(caminho, dtype=str, encoding='latin-1').fillna("")
        except: return []
    df.columns = [str(c).upper().strip() for c in df.columns]
    if "MOV" in caminho.upper():
        if "DATA_HORA" not in df.columns:
            if "DATA" in df.columns: df["DATA_HORA"] = df["DATA"].astype(str) + " 00:00:00"
            else: df["DATA_HORA"] = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
        if "DATA" not in df.columns: df["DATA"] = df["DATA_HORA"].astype(str).str.split(" ").str[0]
    return df.to_dict('records')

def salvar_tudo():
    try:
        if st.session_state.cad: pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD, index=False, encoding='utf-8')
        if st.session_state.mov: pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False, encoding='utf-8')
        if st.session_state.grd: pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD, index=False, encoding='utf-8')
        return True
    except: return False

def df_safe_sort(df, asc=False):
    try:
        if df is None or df.empty: return df
        if "DATA_HORA" in df.columns and not df["DATA_HORA"].empty:
            return df.sort_values(by="DATA_HORA", ascending=asc)
        if "DATA" in df.columns:
            df = df.copy()
            df["_dt_sort"] = df["DATA"].apply(lambda x: parse_data_hora(x))
            return df.sort_values(by="_dt_sort", ascending=asc).drop(columns=["_dt_sort"], errors='ignore')
        return df
    except: return df

def get_saldos():
    saldos = {}
    for r in st.session_state.cad:
        try:
            idp = str(r.get('ID', '')).upper().strip(); lote = str(r.get('LOTE', '')).upper().strip()
            if not idp or not lote: continue
            local = str(r.get('LOCAL', LOCAL_GALPAO)).upper()
            if "SALA" in local: local = LOCAL_SALA
            elif "OFIC" in local: local = LOCAL_OFICINA
            else: local = LOCAL_GALPAO
            marca = str(r.get('MARCA', 'SEM MARCA')).upper()
            chave = f"{idp}__{local}__{marca}__{lote}"
            q = safe_float(r.get('TOTAL', 0))
            if q == 0: q = safe_float(r.get('QTD_PALETE', 0)) * safe_float(r.get('ENTRADA', 0))
            if chave not in saldos:
                saldos[chave] = {'ID': idp, 'DESCRICAO': str(r.get('DESCRICAO', '')).upper(), 'LOCAL': local, 'MARCA': marca, 'LOTE': lote, 'SALDO': q, 'PAL': safe_float(r.get('ENTRADA', 0)), 'QTD_PAL': safe_float(r.get('QTD_PALETE', 0)), 'ULT_ATUAL': str(r.get('FABRICACAO', ''))}
            else: saldos[chave]['SALDO'] += q; saldos[chave]['PAL'] += safe_float(r.get('ENTRADA', 0))
        except: continue
    for m in st.session_state.mov:
        try:
            idp = str(m.get('ID', '')).upper().strip(); lote = str(m.get('LOTE', '')).upper().strip()
            if not idp or not lote: continue
            local = str(m.get('LOCAL_MOV', LOCAL_GALPAO)).upper()
            if "SALA" in local: local = LOCAL_SALA
            elif "OFIC" in local: local = LOCAL_OFICINA
            else: local = LOCAL_GALPAO
            marca = str(m.get('MARCA', 'SEM MARCA')).upper()
            chave = f"{idp}__{local}__{marca}__{lote}"
            if chave not in saldos and m.get('TIPO') == "ENTRADA":
                saldos[chave] = {'ID': idp, 'DESCRICAO': str(m.get('DESCRICAO', '')).upper(), 'LOCAL': local, 'MARCA': marca, 'LOTE': lote, 'SALDO': 0, 'PAL': 0, 'QTD_PAL': 0, 'ULT_ATUAL': str(m.get('DATA_HORA', m.get('DATA', '')))}
            if chave not in saldos: continue
            if m.get('TIPO') == "ENTRADA":
                saldos[chave]['SALDO'] += safe_float(m.get('TOTAL_QTD', 0)); saldos[chave]['PAL'] += safe_float(m.get('PALETES', 0)); saldos[chave]['ULT_ATUAL'] = str(m.get('DATA_HORA', m.get('DATA', '')))
            else:
                saldos[chave]['SALDO'] -= safe_float(m.get('TOTAL_QTD', 0)); saldos[chave]['PAL'] -= safe_float(m.get('PALETES', 0)); saldos[chave]['ULT_ATUAL'] = str(m.get('DATA_HORA', m.get('DATA', '')))
        except: continue
    return saldos

def get_saldo_sala_com_quarentena(tempo_horas=None):
    if tempo_horas is None: tempo_horas = st.session_state.get('tempo_quarentena', TEMPO_QUARENTENA_PADRAO)
    agora_dt = datetime.now(fuso).replace(tzinfo=None)
    saldos = get_saldos()
    total = {}; pend = {}; disp = {}
    for k, v in saldos.items():
        if v['LOCAL'] == LOCAL_SALA and v['SALDO'] > 0:
            total[k] = v.copy(); disp[k] = v.copy()
    for m in st.session_state.mov:
        try:
            if str(m.get('LOCAL_MOV', '')).upper()!= LOCAL_SALA.upper(): continue
            if m.get('TIPO')!= "ENTRADA": continue
            idp = str(m.get('ID', '')).upper().strip(); lote = str(m.get('LOTE', '')).upper().strip()
            marca = str(m.get('MARCA', 'SEM MARCA')).upper()
            chave = f"{idp}__{LOCAL_SALA}__{marca}__{lote}"
            data_mov = parse_data_hora(m.get('DATA_HORA', m.get('DATA', '')))
            diff = (agora_dt - data_mov).total_seconds() / 3600
            if diff < tempo_horas:
                q = safe_float(m.get('TOTAL_QTD', 0)); pal = safe_float(m.get('PALETES', 0))
                if chave not in pend:
                    pend[chave] = {'ID': idp, 'LOTE': lote, 'MARCA': marca, 'DESCRICAO': str(m.get('DESCRICAO', '')).upper(), 'QTD_PENDENTE': q, 'PAL_PENDENTE': pal, 'DATA_ENTRADA': str(m.get('DATA_HORA', '')), 'HORAS_RESTANTES': tempo_horas - diff, 'DATA_LIBERACAO': data_mov + timedelta(hours=tempo_horas)}
                else: pend[chave]['QTD_PENDENTE'] += q; pend[chave]['PAL_PENDENTE'] += pal
                if chave in disp:
                    disp[chave]['SALDO'] -= q; disp[chave]['PAL'] -= pal
                    if disp[chave]['SALDO'] < 0: disp[chave]['SALDO'] = 0
                    if disp[chave]['PAL'] < 0: disp[chave]['PAL'] = 0
        except: continue
    disp = {k: v for k, v in disp.items() if v['SALDO'] > 0}
    return total, pend, disp

# ========== SESSION - GUARDA 100% + HORAS EDITAVEIS ==========
if 'inicializado' not in st.session_state:
    st.session_state.cad = carregar(ARQ_CAD)
    st.session_state.mov = carregar(ARQ_MOV)
    st.session_state.grd = carregar(ARQ_GRD)
    st.session_state.inicializado = True

if 'tempo_quarentena' not in st.session_state:
    st.session_state.tempo_quarentena = TEMPO_QUARENTENA_PADRAO

if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL": "admin@admin.com", "SENHA": "admin", "LOCAL": "AMBOS", "STATUS": "LIBERADO", "NOME": "ADMIN"}]).to_csv(ARQ_EMAILS, index=False)

if 'logado' not in st.session_state: st.session_state.logado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

if not st.session_state.logado:
    st.markdown("<h1 style='text-align:center; background:black; color:#00ff66; padding:20px; border-radius:12px;'>REFORMA DE FORNOS</h1>", unsafe_allow_html=True)
    e = st.text_input("Email"); s = st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        df_e = pd.read_csv(ARQ_EMAILS, dtype=str).fillna("")
        df_e['EMAIL'] = df_e['EMAIL'].astype(str).str.lower()
        u = df_e[(df_e["EMAIL"] == e.lower().strip()) & (df_e["SENHA"].astype(str) == str(s)) & (df_e["STATUS"] == "LIBERADO")]
        if not u.empty:
            st.session_state.logado = True; st.session_state.usuario = u.iloc[0].to_dict(); st.rerun()
        else: st.error("Invalido")
    st.stop()

user = st.session_state.usuario
is_admin = str(user.get('EMAIL', '')).lower() == "admin@admin.com"

# TELA LIGADA - SEM RELOAD QUE APAGA
import streamlit.components.v1 as components
components.html("""
<script>
let wakeLock=null;
async function keepOn(){ try{ if('wakeLock' in navigator){ wakeLock=await navigator.wakeLock.request('screen'); } }catch(e){} }
keepOn();
</script>
<p style='color:green;font-size:12px;'>✅ TELA LIGADA - VOCÊ DECIDE AS HORAS</p>
""", height=30)

st.sidebar.write(f"Logado: {user.get('NOME')}")
st.sidebar.metric("⏰ VOCÊ DECIDE", f"{st.session_state.tempo_quarentena}H = {st.session_state.tempo_quarentena/24:.1f} dias")
st.sidebar.write(f"📦 CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)} GRD:{len(st.session_state.grd)}")
st.sidebar.divider()
if st.session_state.cad: st.sidebar.download_button("BAIXAR CAD", pd.DataFrame(st.session_state.cad).to_csv(index=False), "cadastro.csv")
if st.session_state.mov: st.sidebar.download_button("BAIXAR MOV", pd.DataFrame(st.session_state.mov).to_csv(index=False), "mov.csv")
if st.session_state.grd: st.sidebar.download_button("BAIXAR GRD", pd.DataFrame(st.session_state.grd).to_csv(index=False), "grd.csv")
if st.sidebar.button("Sair"):
    salvar_tudo(); st.session_state.logado = False; st.session_state.usuario = None; st.rerun()

agora = datetime.now(fuso)
st.title(f"REFORMA DE FORNOS - {agora.strftime('%d/%m/%Y %H:%M:%S')}")
tabs = st.tabs(["ADMIN", "DASHBOARD", "CADASTRO AUTO", "MOV AUTO", "ESTOQUE", "BUSCA ID", "GRD SALA - VOCE DECIDE HORAS", "GRAFICOS EMPILHADOS", "HISTORICO"])
tab_admin, tab_dash, tab_cad, tab_mov, tab_est, tab_busca, tab_grd, tab_graf, tab_hist = tabs

with tab_admin:
    st.header("1 - ADMINISTRACAO")
    if not is_admin: st.warning("Apenas admin")
    else:
        with st.form("form_admin"):
            email_new = st.text_input("Email novo"); nome_new = st.text_input("Nome"); senha_new = st.text_input("Senha")
            local_new = st.selectbox("Local", LOCAIS_ACESSO); status_new = st.selectbox("Status", ["LIBERADO", "BLOQUEADO"])
            if st.form_submit_button("SALVAR", type="primary"):
                if email_new and senha_new:
                    df = pd.read_csv(ARQ_EMAILS); df = df[df['EMAIL'].astype(str).str.lower()!= email_new.lower()]
                    novo = pd.DataFrame([{"EMAIL": email_new.lower(), "SENHA": senha_new, "LOCAL": local_new, "STATUS": status_new, "NOME": nome_new.upper()}])
                    df = pd.concat([df, novo], ignore_index=True); df.to_csv(ARQ_EMAILS, index=False); st.success("Salvo"); st.rerun()
        try: st.dataframe(pd.read_csv(ARQ_EMAILS), use_container_width=True)
        except: st.warning("Sem emails")

with tab_dash:
    st.header(f"2 - DASHBOARD - VOCE DECIDIU {st.session_state.tempo_quarentena}H")
    try:
        total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
        saldos_geral = get_saldos()
        if not total_sala:
            total_sala = {k: v for k, v in saldos_geral.items() if v['LOCAL'] == LOCAL_SALA and v['SALDO'] > 0}
            disp_sala = total_sala.copy()
        df_total = pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
        df_disp = pd.DataFrame(list(disp_sala.values())) if disp_sala else pd.DataFrame()
        if df_total.empty:
            st.error(f"SEM ESTOQUE EM {LOCAL_SALA}")
            lista_geral = [v for v in saldos_geral.values() if v['SALDO'] > 0]
            if lista_geral: st.dataframe(pd.DataFrame(lista_geral), use_container_width=True)
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("SALA TOTAL", f"{df_total['SALDO'].sum():,.0f}")
            with c2: st.metric(f"BLOQ <{st.session_state.tempo_quarentena}H (VOCE DECIDIU)", f"{sum([v['QTD_PENDENTE'] for v in pendente_sala.values()]) if pendente_sala else 0:,.0f}")
            with c3: st.metric(f"DISP GRD >{st.session_state.tempo_quarentena}H", f"{df_disp['SALDO'].sum() if not df_disp.empty else df_total['SALDO'].sum():,.0f}")
            with c4: st.metric("IDS", f"{df_total['ID'].nunique()}")
            df_show = df_total.copy()
            df_show['DATA_HORA_ATUALIZACAO'] = df_show['ULT_ATUAL']
            df_show['AGORA'] = agora.strftime("%d/%m/%Y %H:%M:%S")
            df_show['QUARENTENA_DECIDE'] = f"{st.session_state.tempo_quarentena}H"
            st.dataframe(df_show[['ID', 'DESCRICAO', 'LOTE', 'MARCA', 'SALDO', 'PAL', 'DATA_HORA_ATUALIZACAO', 'AGORA', 'QUARENTENA_DECIDE', 'LOCAL']], use_container_width=True, height=400)
            df_id = df_show.groupby(['ID', 'DESCRICAO'], as_index=False)['SALDO'].sum()
            df_id['TEXTO'] = df_id['SALDO'].apply(lambda x: f"{x:,.0f}")
            fig = px.bar(df_id, x='ID', y='SALDO', text='TEXTO', color='ID', title=f"IDS INDIVIDUAIS SALA - QUARENTENA {st.session_state.tempo_quarentena}H - {agora.strftime('%d/%m/%Y %H:%M')}")
            st.plotly_chart(fig, use_container_width=True, key=f"dash_{agora.strftime('%H%M%S')}")
            if pendente_sala:
                st.subheader(f"⏳ PENDENTE {st.session_state.tempo_quarentena}H - VOCE DECIDIU")
                df_p = pd.DataFrame([{'ID': v['ID'], 'LOTE': v['LOTE'], 'QTD': v['QTD_PENDENTE'], 'ENTRADA': v['DATA_ENTRADA'], 'LIBERACAO': v['DATA_LIBERACAO'].strftime("%d/%m/%Y %H:%M:%S"), 'RESTA': f"{v['HORAS_RESTANTES']:.1f}h"} for v in pendente_sala.values()])
                st.dataframe(df_p.sort_values(by='ID'), use_container_width=True)
    except Exception as e: st.error(f"Erro dashboard: {e}")

with tab_cad:
    st.header("3 - CADASTRO AUTO - GUARDA 100%")
    id_in = st.text_input("DIGITE ID*", key="cad_id")
    desc_auto = ""; marca_auto = ""; qtd_auto = 1250.0; lote_auto = ""; enc = False
    if id_in:
        for r in st.session_state.cad:
            if str(r.get('ID', '')).upper().strip() == id_in.upper().strip():
                desc_auto = r.get('DESCRICAO', ''); marca_auto = r.get('MARCA', ''); qtd_auto = safe_float(r.get('QTD_PALETE', 1250), 1250); lote_auto = r.get('LOTE', ''); enc = True; break
    if enc:
        st.success(f"ID {id_in.upper()} AUTO {desc_auto}")
        with st.form("form_cad_auto"):
            lote_n = st.text_input(f"LOTE BASE {lote_auto}"); locs = st.multiselect("LOCAIS*", LOCAIS, default=[LOCAL_GALPAO]); ent = st.number_input("PALETES*", value=1.0, min_value=0.1)
            if st.form_submit_button("CADASTRAR E GUARDAR", type="primary"):
                lf = lote_n.upper() if lote_n else lote_auto
                if lf and locs:
                    for lc in locs: st.session_state.cad.append({"ID": id_in.upper(), "DESCRICAO": desc_auto.upper(), "MARCA": marca_auto.upper(), "LOTE": lf.upper(), "QTD_PALETE": qtd_auto, "ENTRADA": ent, "TOTAL": qtd_auto*ent, "LOCAL": lc, "FABRICACAO": agora.strftime("%d/%m/%Y %H:%M:%S")})
                    salvar_tudo(); st.success(f"✅ GUARDADO CAD: {len(st.session_state.cad)}"); st.rerun()
    else:
        if id_in: st.warning(f"NOVO ID {id_in.upper()}")
        with st.form("form_cad_novo"):
            d = st.text_input("DESCRICAO*"); m = st.text_input("MARCA*"); l = st.text_input("LOTE*"); locs = st.multiselect("LOCAIS*", LOCAIS, default=[LOCAL_GALPAO]); q = st.number_input("QTD/PAL*", value=1250.0); ent = st.number_input("PALETES", value=0.0)
            if st.form_submit_button("CADASTRAR NOVO E GUARDAR", type="primary"):
                if id_in and d and m and l and locs:
                    for lc in locs: st.session_state.cad.append({"ID": id_in.upper(), "DESCRICAO": d.upper(), "MARCA": m.upper(), "LOTE": l.upper(), "QTD_PALETE": q, "ENTRADA": ent, "TOTAL": q*ent, "LOCAL": lc, "FABRICACAO": agora.strftime("%d/%m/%Y %H:%M:%S")})
                    salvar_tudo(); st.success("✅ GUARDADO"); st.rerun()

with tab_mov:
    st.header("4 - MOV AUTO - GUARDA 100%")
    id_mov = st.text_input("DIGITE ID* AUTO", key="mov_id")
    desc_m = ""; marca_m = ""; qtd_m = 1250.0; lotes = []; enc_m = False
    if id_mov:
        up = id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID', '')).upper().strip() == up:
                desc_m = r.get('DESCRICAO', ''); marca_m = r.get('MARCA', ''); qtd_m = safe_float(r.get('QTD_PALETE', 1250), 1250); enc_m = True
                if r.get('LOTE', '') and str(r.get('LOTE', '')).upper() not in lotes: lotes.append(str(r.get('LOTE', '')).upper())
        for v in get_saldos().values():
            if v['ID'] == up and v['SALDO'] > 0 and v['LOTE'] not in lotes: lotes.append(v['LOTE'])
    if not id_mov: st.info("DIGITE ID")
    elif not enc_m: st.error(f"ID {id_mov.upper()} NAO CADASTRADO")
    else:
        saldo_id = [v for v in get_saldos().values() if v['ID'] == id_mov.upper() and v['SALDO'] > 0]
        if saldo_id: st.dataframe(pd.DataFrame(saldo_id), use_container_width=True)
        with st.form("form_mov"):
            if lotes: sel = st.selectbox("LOTE AUTO", options=lotes+["NOVO LOTE"]); lf = st.text_input("NOVO LOTE*") if sel == "NOVO LOTE" else sel
            else: lf = st.text_input("LOTE*")
            mf = st.text_input("MARCA AUTO", value=marca_m); loc = st.selectbox("LOCAL*", LOCAIS); tip = st.selectbox("TIPO*", ["ENTRADA", "SAIDA"]); pal = st.number_input("PALETES*", value=1.0, min_value=0.1)
            if st.form_submit_button(f"CONFIRMAR E GUARDAR - {agora.strftime('%H:%M:%S')}", type="primary", use_container_width=True):
                if lf:
                    agora_str = datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    tot = pal*qtd_m
                    base = {"ID": id_mov.upper(), "LOTE": lf.upper().strip(), "MARCA": mf.upper(), "DESCRICAO": desc_m, "PALETES": pal, "TOTAL_QTD": tot, "DATA": agora_str.split(" ")[0], "DATA_HORA": agora_str}
                    if loc == LOCAL_GALPAO and tip == "ENTRADA": st.session_state.mov.append({**base, "TIPO": "ENTRADA", "LOCAL_MOV": LOCAL_GALPAO})
                    elif loc == LOCAL_GALPAO and tip == "SAIDA":
                        st.session_state.mov.append({**base, "TIPO": "SAIDA", "LOCAL_MOV": LOCAL_GALPAO}); st.session_state.mov.append({**base, "TIPO": "ENTRADA", "LOCAL_MOV": LOCAL_OFICINA})
                    elif loc == LOCAL_SALA and tip == "ENTRADA":
                        st.session_state.mov.append({**base, "TIPO": "SAIDA", "LOCAL_MOV": LOCAL_GALPAO}); st.session_state.mov.append({**base, "TIPO": "ENTRADA", "LOCAL_MOV": LOCAL_SALA})
                    elif loc == LOCAL_SALA and tip == "SAIDA":
                        st.session_state.mov.append({**base, "TIPO": "SAIDA", "LOCAL_MOV": LOCAL_SALA}); st.session_state.mov.append({**base, "TIPO": "ENTRADA", "LOCAL_MOV": LOCAL_OFICINA})
                    elif loc == LOCAL_OFICINA and tip == "ENTRADA": st.session_state.mov.append({**base, "TIPO": "ENTRADA", "LOCAL_MOV": LOCAL_OFICINA})
                    else: st.session_state.mov.append({**base, "TIPO": "SAIDA", "LOCAL_MOV": LOCAL_OFICINA})
                    salvar_tudo(); st.success(f"✅ GUARDADO MOV: {len(st.session_state.mov)}"); st.rerun()
    if st.session_state.mov: st.dataframe(df_safe_sort(pd.DataFrame(st.session_state.mov), False).head(20), use_container_width=True)

with tab_est:
    st.header("5 - ESTOQUE")
    lista = [v for v in get_saldos().values() if v['SALDO'] > 0]
    if lista: st.dataframe(pd.DataFrame(lista).sort_values(by='ID'), use_container_width=True)
    else: st.info("Sem estoque")

with tab_busca:
    st.header("6 - BUSCA ID")
    id_b = st.text_input("ID BUSCA", key="busca_id")
    if id_b:
        up = id_b.upper().strip()
        lista = [v for v in get_saldos().values() if v['ID'] == up and v['SALDO'] > 0]
        if lista: st.dataframe(pd.DataFrame(lista), use_container_width=True)

# ========== 7 GRD - VOCE DECIDE HORAS ==========
with tab_grd:
    st.header(f"7 - GRD SALA - VOCE DECIDE AS HORAS - ATUAL {st.session_state.tempo_quarentena}H")
    c_h1, c_h2, c_h3 = st.columns([2,1,1])
    with c_h1:
        nova_hora = st.number_input("⏰ VOCE DECIDE QTD HORAS QUARENTENA - EDITAVEL", min_value=1, max_value=720, value=int(st.session_state.tempo_quarentena), step=1, key="input_horas_grd", help="1=1hora, 24=1dia, 48=2dias, 72=3dias, 168=7dias")
    with c_h2:
        if st.button("💾 SALVAR HORAS - VOCE DECIDE", type="primary"):
            st.session_state.tempo_quarentena = int(nova_hora)
            st.success(f"✅ AGORA VOCE DECIDIU {nova_hora}H = {nova_hora/24:.1f} dias - GUARDADO")
            st.rerun()
    with c_h3: st.metric("VOCE DECIDIU", f"{st.session_state.tempo_quarentena}H")

    total_sala, pendente_sala, disp_sala = get_saldo_sala_com_quarentena(st.session_state.tempo_quarentena)
    if not total_sala:
        saldos_geral = get_saldos(); total_sala = {k: v for k, v in saldos_geral.items() if v['LOCAL'] == LOCAL_SALA and v['SALDO'] > 0}; disp_sala = total_sala.copy()
    df_total = pd.DataFrame(list(total_sala.values())) if total_sala else pd.DataFrame()
    if not df_total.empty: st.dataframe(df_total.sort_values(by='ID'), use_container_width=True)
    ids_disp = sorted(list(set([v['ID'] for v in disp_sala.values()]))) if disp_sala else []
    if ids_disp:
        tipo = st.radio("Tipo GRD", ["INDIVIDUAL", "CONJUNTO MESMO NUMERO"], key="tipo_grd")
        if tipo == "INDIVIDUAL":
            id_g = st.selectbox("ID", ids_disp, key="id_grd")
            saldo_id = [v for v in disp_sala.values() if v['ID'] == id_g]
            lote_sel = st.selectbox("LOTE", sorted(list(set([v['LOTE'] for v in saldo_id]))), key="lote_grd")
            saldo_lote = [v for v in saldo_id if v['LOTE'] == lote_sel][0]
            qtd = st.number_input(f"PAL MAX {saldo_lote['PAL']:.1f} - LIBERADO >{st.session_state.tempo_quarentena}H", value=1.0, key="qtd_grd")
            os_g = st.text_input("OS*", key="os_grd")
            if st.button(f"GERAR GRD - {st.session_state.tempo_quarentena}H QUE VOCE DECIDIU", type="primary", key="btn_grd"):
                num = f"GRD-{st.session_state.tempo_quarentena}H-{agora.strftime('%Y%m%d%H%M%S')}"; tot = qtd*saldo_lote['QTD_PAL'] if saldo_lote['QTD_PAL'] > 0 else qtd*1250
                st.session_state.grd.append({"NUM_GRD": num, "ID": id_g, "DESCRICAO": saldo_lote['DESCRICAO'], "LOTE": lote_sel, "MARCA": saldo_lote['MARCA'], "QTD_PALETES": qtd, "TOTAL_QTD": tot, "ORIGEM": LOCAL_SALA, "DESTINO": LOCAL_OFICINA, "OS": os_g, "DATA": agora.strftime("%d/%m/%Y"), "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S"), "QUARENTENA_H": st.session_state.tempo_quarentena})
                st.session_state.mov.append({"ID": id_g, "LOTE": lote_sel, "MARCA": saldo_lote['MARCA'], "DESCRICAO": saldo_lote['DESCRICAO'], "TIPO": "SAIDA", "PALETES": qtd, "TOTAL_QTD": tot, "LOCAL_MOV": LOCAL_SALA, "DATA": agora.strftime("%d/%m/%Y"), "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S")})
                st.session_state.mov.append({"ID": id_g, "LOTE": lote_sel, "MARCA": saldo_lote['MARCA'], "DESCRICAO": saldo_lote['DESCRICAO'], "TIPO": "ENTRADA", "PALETES": qtd, "TOTAL_QTD": tot, "LOCAL_MOV": LOCAL_OFICINA, "DATA": agora.strftime("%d/%m/%Y"), "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S")})
                salvar_tudo(); st.success(f"GRD {num} - {st.session_state.tempo_quarentena}H QUE VOCE DECIDIU - GUARDADO"); st.rerun()
        else:
            ids_multi = st.multiselect("IDS MESMO GRD", ids_disp, default=ids_disp[:2] if len(ids_disp) >= 2 else ids_disp, key="ids_conj")
            if ids_multi:
                qtds = {}
                for id_sel in ids_multi:
                    saldo_id = [v for v in disp_sala.values() if v['ID'] == id_sel]
                    lote_id = st.selectbox(f"LOTE ID {id_sel}", sorted(list(set([v['LOTE'] for v in saldo_id]))), key=f"lote_conj_{id_sel}")
                    saldo_lote = [v for v in saldo_id if v['LOTE'] == lote_id][0]
                    qtd = st.number_input(f"PAL ID {id_sel} MAX {saldo_lote['PAL']:.1f}", value=1.0, key=f"qtd_conj_{id_sel}")
                    qtds[id_sel] = {'lote': lote_id, 'saldo_lote': saldo_lote, 'qtd': qtd}
                os_g = st.text_input("OS* CONJUNTO", key="os_conj")
                if st.button(f"GERAR GRD CONJUNTO {st.session_state.tempo_quarentena}H - VOCE DECIDE", type="primary", use_container_width=True, key="btn_conj"):
                    num = f"GRD-CONJ-{st.session_state.tempo_quarentena}H-{agora.strftime('%Y%m%d%H%M%S')}"
                    for id_sel in ids_multi:
                        info = qtds[id_sel]; tot = info['qtd']*info['saldo_lote']['QTD_PAL'] if info['saldo_lote']['QTD_PAL'] > 0 else info['qtd']*1250
                        st.session_state.grd.append({"NUM_GRD": num, "ID": id_sel, "DESCRICAO": info['saldo_lote']['DESCRICAO'], "LOTE": info['lote'], "MARCA": info['saldo_lote']['MARCA'], "QTD_PALETES": info['qtd'], "TOTAL_QTD": tot, "ORIGEM": LOCAL_SALA, "DESTINO": LOCAL_OFICINA, "OS": os_g, "DATA": agora.strftime("%d/%m/%Y"), "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S"), "QUARENTENA_H": st.session_state.tempo_quarentena, "TIPO_GRD": "CONJUNTO"})
                        st.session_state.mov.append({"ID": id_sel, "LOTE": info['lote'], "MARCA": info['saldo_lote']['MARCA'], "DESCRICAO": info['saldo_lote']['DESCRICAO'], "TIPO": "SAIDA", "PALETES": info['qtd'], "TOTAL_QTD": tot, "LOCAL_MOV": LOCAL_SALA, "DATA": agora.strftime("%d/%m/%Y"), "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S")})
                        st.session_state.mov.append({"ID": id_sel, "LOTE": info['lote'], "MARCA": info['saldo_lote']['MARCA'], "DESCRICAO": info['saldo_lote']['DESCRICAO'], "TIPO": "ENTRADA", "PALETES": info['qtd'], "TOTAL_QTD": tot, "LOCAL_MOV": LOCAL_OFICINA, "DATA": agora.strftime("%d/%m/%Y"), "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S")})
                    salvar_tudo(); st.success(f"GRD CONJ {num} - {st.session_state.tempo_quarentena}H VOCE DECIDIU"); st.rerun()
    if st.session_state.grd: st.dataframe(df_safe_sort(pd.DataFrame(st.session_state.grd), False), use_container_width=True)

# ========== 8 GRAFICOS EMPILHADOS - NUMEROS GRANDES + DATA/HORA ==========
with tab_graf:
    st.header(f"8 - GRAFICOS EMPILHADOS - SALDO TOTAL - VOCE DECIDIU {st.session_state.tempo_quarentena}H - NUMEROS GRANDES + DATA/HORA ULTIMA MOV - {agora.strftime('%d/%m/%Y %H:%M:%S')}")
    saldos = get_saldos(); lista = [v for v in saldos.values() if v['SALDO'] > 0]
    if not lista: st.warning("Sem estoque")
    else:
        df_estoque = pd.DataFrame(lista)
        ultimas = {}
        for m in st.session_state.mov:
            try:
                idp = str(m.get('ID','')).upper().strip()
                if not idp: continue
                dh = str(m.get('DATA_HORA', m.get('DATA','')))
                dtm = parse_data_hora(dh)
                if idp not in ultimas or dtm > ultimas[idp]['dt']:
                    ultimas[idp] = {'dt': dtm, 'data_hora': dh, 'tipo': m.get('TIPO',''), 'local': m.get('LOCAL_MOV','')}
            except: continue
        df_estoque['ULTIMA_DATA_HORA'] = df_estoque['ID'].apply(lambda x: ultimas.get(x,{}).get('data_hora','SEM MOV'))
        df_estoque['ULTIMO_TIPO'] = df_estoque['ID'].apply(lambda x: ultimas.get(x,{}).get('tipo',''))
        df_emp = df_estoque.groupby(['ID','LOCAL'], as_index=False)['SALDO'].sum()
        df_ult = df_estoque.groupby('ID', as_index=False).agg({'ULTIMA_DATA_HORA':'first','ULTIMO_TIPO':'first','SALDO':'sum'}).rename(columns={'SALDO':'TOTAL_ID'})
        df_emp = df_emp.merge(df_ult, on='ID', how='left')
        df_emp['TEXTO_GRANDE'] = df_emp['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_emp = df_emp.sort_values(by='ID')
        fig_stack = px.bar(df_emp, x='ID', y='SALDO', color='LOCAL', text='TEXTO_GRANDE', title=f"SALDO EMPILHADO POR LOCAL - QUARENTENA {st.session_state.tempo_quarentena}H VOCE DECIDIU - {agora.strftime('%d/%m/%Y %H:%M:%S')}", hover_data=['ULTIMA_DATA_HORA','ULTIMO_TIPO','TOTAL_ID'], barmode='stack')
        fig_stack.update_traces(textposition='inside', textfont=dict(size=18, color='white', family='Arial Black'))
        fig_stack.update_layout(height=600, title_font_size=20)
        st.plotly_chart(fig_stack, use_container_width=True, key=f"stack_{agora.strftime('%H%M%S')}")
        df_total_id = df_estoque.groupby(['ID','DESCRICAO'], as_index=False).agg({'SALDO':'sum','ULTIMA_DATA_HORA':'first','ULTIMO_TIPO':'first'})
        df_total_id['TEXTO_NUM'] = df_total_id['SALDO'].apply(lambda x: f"{x:,.0f}")
        df_total_id = df_total_id.sort_values(by='SALDO', ascending=False)
        fig_total = px.bar(df_total_id, x='ID', y='SALDO', text='TEXTO_NUM', color='SALDO', title=f"SALDO TOTAL POR ID + ULTIMA MOV {st.session_state.tempo_quarentena}H VOCE DECIDE - {agora.strftime('%d/%m/%Y %H:%M:%S')}", hover_data=['DESCRICAO','ULTIMA_DATA_HORA','ULTIMO_TIPO'])
        fig_total.update_traces(textposition='outside', textfont=dict(size=18, family='Arial Black'), cliponaxis=False)
        fig_total.update_layout(height=650)
        st.plotly_chart(fig_total, use_container_width=True, key=f"total_{agora.strftime('%H%M%S')}")
        st.subheader(f"📊 TABELA SALDO TOTAL + DATA/HORA ULTIMA ENTRADA/SAIDA - {st.session_state.tempo_quarentena}H VOCE DECIDIU - NUMEROS GRANDES")
        df_total_id['AGORA'] = agora.strftime("%d/%m/%Y %H:%M:%S")
        df_total_id['QUARENTENA_H_VOCE_DECIDIU'] = f"{st.session_state.tempo_quarentena}H"
        st.dataframe(df_total_id[['ID','DESCRICAO','SALDO','ULTIMA_DATA_HORA','ULTIMO_TIPO','QUARENTENA_H_VOCE_DECIDE','AGORA']].sort_values(by='SALDO', ascending=False) if 'QUARENTENA_H_VOCE_DECIDE' in df_total_id.columns else df_total_id, use_container_width=True, height=500)
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("SALDO TOTAL GERAL", f"{df_estoque['SALDO'].sum():,.0f}")
        with c2:
            if ultimas:
                ultima_geral = max([v['dt'] for v in ultimas.values()])
                st.metric("ULTIMA MOV GERAL", ultima_geral.strftime("%d/%m/%Y %H:%M:%S"))
        with c3: st.metric("QTD IDS", f"{df_estoque['ID'].nunique()}")

with tab_hist:
    st.header("9 - HISTORICO")
    if not st.session_state.mov: st.warning("Sem mov")
    else:
        try:
            df_all = pd.DataFrame(st.session_state.mov)
            if "DATA_HORA" not in df_all.columns: df_all["DATA_HORA"] = df_all.get("DATA", "")
            df_all['DATA_DT'] = df_all['DATA'].apply(lambda x: parse_data_hora(x))
            df_all['DIA'] = df_all['DATA_DT'].dt.strftime("%d/%m/%Y")
            df_all['MES'] = df_all['DATA_DT'].dt.strftime("%m/%Y")
            df_all['ANO'] = df_all['DATA_DT'].dt.strftime("%Y")
            df_all['QTD'] = df_all['TOTAL_QTD'].apply(lambda x: safe_float(x))
            ids_raw = [str(r.get('ID', '')).strip().upper() for r in st.session_state.cad if str(r.get('ID', '')).strip()!= '']
            ids_hist = ["TODOS"] + sorted(list(set(ids_raw)))
            c1, c2, c3, c4 = st.columns(4)
            with c1: id_f = st.selectbox("ID", ids_hist, key="hist_id")
            with c2: tip_f = st.selectbox("TIPO", ["TODOS", "ENTRADA", "SAIDA"], key="hist_tip")
            with c3: per_f = st.selectbox("PERIODO", ["DIA", "MES", "ANO"], key="hist_per")
            with c4: loc_f = st.selectbox("LOCAL", ["TODOS"]+LOCAIS, key="hist_loc")
            df_f = df_all.copy()
            if id_f!= "TODOS": df_f = df_f[df_f['ID'].astype(str).str.upper() == id_f]
            if tip_f!= "TODOS": df_f = df_f[df_f['TIPO'] == tip_f]
            if loc_f!= "TODOS": df_f = df_f[df_f['LOCAL_MOV'] == loc_f]
            if not df_f.empty:
                df_ent = df_f[df_f['TIPO'] == "ENTRADA"]; df_sai = df_f[df_f['TIPO'] == "SAIDA"]
                c1, c2, c3 = st.columns(3)
                with c1: st.metric(f"ENT {id_f}", f"{df_ent['QTD'].sum():,.0f}")
                with c2: st.metric(f"SAI {id_f}", f"{df_sai['QTD'].sum():,.0f}")
                with c3: st.metric(f"SALDO", f"{df_ent['QTD'].sum()-df_sai['QTD'].sum():,.0f}")
                col = {'DIA': 'DIA', 'MES': 'MES', 'ANO': 'ANO'}[per_f]
                df_g = df_f.groupby([col, 'TIPO'], as_index=False)['QTD'].sum()
                if not df_g.empty: st.plotly_chart(px.bar(df_g, x=col, y='QTD', color='TIPO', barmode='group', text='QTD'), use_container_width=True, key=f"hist_{id_f}_{tip_f}_{per_f}_{loc_f}")
                st.dataframe(df_safe_sort(df_f, False), use_container_width=True, height=400)
        except Exception as e:
            st.error(f"Erro hist: {e}")
            st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

st.caption(f"REFORMA FORNOS - VOCE DECIDE {st.session_state.tempo_quarentena}H - {agora.strftime('%d/%m/%Y %H:%M:%S')} - FINAL COMPLETO - GUARDA 100% - GRAFICO EMPILHADO NUMEROS GRANDES + DATA/HORA ULTIMA MOV - CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
