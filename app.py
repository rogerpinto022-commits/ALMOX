import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit.components.v1 as components

# ================= CONFIG =================
st.set_page_config(page_title="REFORMA DE FORNOS V5", layout="wide", page_icon="🔥")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_EMAILS = "emails.csv"

LOCAL_GALPAO = "GALPÃO DE MATERIAIS REFRATARIOS"
LOCAL_SALA = "SALA ANEXA"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"
LOCAIS = [LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]

def safe_float(v, padrao=0.0):
    try:
        if v is None or v=="" or str(v).strip()=="": return float(padrao)
        return float(str(v).replace(",",".").strip())
    except: return float(padrao)

def carregar_seguro(caminho):
    if not os.path.exists(caminho): return []
    try:
        df=pd.read_csv(caminho).fillna("")
        df.columns=[str(c).upper().strip() for c in df.columns]
        if "LOCAL" not in df.columns: df["LOCAL"] = LOCAL_GALPAO
        if "MARCA" not in df.columns: df["MARCA"] = "SEM MARCA"
        return df.to_dict('records')
    except:
        try: os.remove(caminho)
        except: pass
        return []

if 'lista_cadastro' not in st.session_state: st.session_state.lista_cadastro=carregar_seguro(ARQ_CAD)
if 'lista_mov' not in st.session_state: st.session_state.lista_mov=carregar_seguro(ARQ_MOV)
if 'id_selecionado' not in st.session_state: st.session_state.id_selecionado=None
if 'logado' not in st.session_state: st.session_state.logado=False

if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO"}]).to_csv(ARQ_EMAILS, index=False)

if not st.session_state.logado:
    st.title("🔐 REFORMA DE FORNOS - Login")
    e = st.text_input("Email").lower().strip()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        df_e = pd.read_csv(ARQ_EMAILS)
        user = df_e[(df_e["EMAIL"]==e) & (df_e["SENHA"]==s) & (df_e["STATUS"]=="LIBERADO")]
        if not user.empty:
            st.session_state.logado=True
            st.session_state.local_acesso=user.iloc[0]["LOCAL"]
            st.session_state.usuario=e
            st.rerun()
        else: st.error("Login inválido")
    st.stop()

agora_br = datetime.now(fuso)

st.sidebar.divider()
st.sidebar.subheader("⚙️ Controles")
auto = st.sidebar.toggle("🔄 ATUALIZAÇÃO AUTOMÁTICA (10s)", value=False)
if auto:
    st.sidebar.caption("✅ Atualizando a cada 10s")
    components.html("""<script>setTimeout(()=>{window.parent.location.reload();},10000);</script>""", height=0)

manter = st.sidebar.toggle("🔒 MANTER ABERTO", value=True)
if manter:
    components.html("""<script>let wakeLock=null; async function requestLock(){ try{ if('wakeLock' in navigator){ wakeLock=await navigator.wakeLock.request('screen'); } }catch(e){} } requestLock(); document.addEventListener('visibilitychange',()=>{ if(wakeLock!==null && document.visibilityState==='visible'){requestLock();} });</script>""", height=0)

if st.sidebar.button("🔴 DESLIGAR / FECHAR", type="primary", use_container_width=True):
    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
    pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
    st.session_state.clear()
    st.stop()

if st.sidebar.button("🚪 Sair do Login"):
    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
    pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
    st.session_state.clear()
    st.rerun()

def calcular_valido_ate(fab_str, tempo_meses):
    try:
        fab=datetime.strptime(fab_str, "%d/%m/%Y")
        valido=fab + relativedelta(months=int(safe_float(tempo_meses,12)))
        return valido.strftime("%d/%m/%Y")
    except: return "00/00/0000"

def get_saldos_completos():
    saldos={}
    for r in st.session_state.get('lista_cadastro',[]):
        id_prod = str(r.get('ID','')).strip()
        lote=str(r.get('LOTE','')).strip()
        if not lote or not id_prod: continue
        local = str(r.get('LOCAL', LOCAL_GALPAO))
        if "SALA" in local.upper(): local = LOCAL_SALA
        elif "OFIC" in local.upper(): local = LOCAL_OFICINA
        else: local = LOCAL_GALPAO
        marca = str(r.get('MARCA','SEM MARCA')).upper().strip() or "SEM MARCA"
        qtd_palete=safe_float(r.get('QTD_PALETE',0),0)
        entrada_pal=safe_float(r.get('ENTRADA',0),0)
        total=safe_float(r.get('TOTAL',0),0)
        if total==0: total=qtd_palete*entrada_pal
        unidade=str(r.get('UNIDADE','KG')).upper().strip() or "KG"
        chave = f"{id_prod}__{local}__{marca}__{lote}"
        if chave not in saldos:
            saldos[chave]=r.copy()
            saldos[chave]['ID']=id_prod
            saldos[chave]['LOCAL']=local
            saldos[chave]['MARCA']=marca
            saldos[chave]['LOTE_ORIG']=lote
            saldos[chave]['UNIDADE']=unidade
            saldos[chave]['ENTRADAS_PALETES']=entrada_pal
            saldos[chave]['SAIDAS_PALETES']=0
            saldos[chave]['ENTRADAS_QTD']=total
            saldos[chave]['SAIDAS_QTD']=0
            saldos[chave]['SALDO_PALETES']=entrada_pal
            saldos[chave]['SALDO_QTD']=total
            saldos[chave]['QTD_PALETE_BASE']=qtd_palete
        else:
            saldos[chave]['ENTRADAS_PALETES']+=entrada_pal
            saldos[chave]['ENTRADAS_QTD']+=total
            saldos[chave]['SALDO_PALETES']+=entrada_pal
            saldos[chave]['SALDO_QTD']+=total
    for m in st.session_state.get('lista_mov',[]):
        lote=str(m.get('LOTE','')).strip()
        id_busca = str(m.get('ID', '')).strip() or lote
        local_mov=str(m.get('LOCAL_MOV','')).strip()
        if "SALA" in local_mov.upper(): local_mov=LOCAL_SALA
        elif "OFIC" in local_mov.upper(): local_mov=LOCAL_OFICINA
        else: local_mov=LOCAL_GALPAO
        marca = str(m.get('MARCA', 'SEM MARCA')).upper().strip() or "SEM MARCA"
        tipo=str(m.get('TIPO','')).upper()
        paletes=safe_float(m.get('PALETES',0),0)
        qtd=safe_float(m.get('TOTAL_QTD',0),0)
        chave = f"{id_busca}__{local_mov}__{marca}__{lote}"
        if chave not in saldos: continue
        if tipo=="ENTRADA":
            saldos[chave]['ENTRADAS_PALETES']+=paletes
            saldos[chave]['ENTRADAS_QTD']+=qtd
            saldos[chave]['SALDO_PALETES']+=paletes
            saldos[chave]['SALDO_QTD']+=qtd
        else:
            saldos[chave]['SAIDAS_PALETES']+=paletes
            saldos[chave]['SAIDAS_QTD']+=qtd
            saldos[chave]['SALDO_PALETES']-=paletes
            saldos[chave]['SALDO_QTD']-=qtd
    return saldos

def buscar_por_id(id_digitado):
    id_digitado = str(id_digitado).strip().upper()
    saldos = get_saldos_completos()
    resultados = []
    for chave, dados in saldos.items():
        if dados.get('ID','').upper() == id_digitado:
            resultados.append(dados)
    try:
        resultados.sort(key=lambda x: datetime.strptime(x.get('FABRICACAO','01/01/2000'), "%d/%m/%Y"))
    except: pass
    return resultados

st.markdown(f"""
<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00; font-family:Orbitron, Arial Black; text-shadow: 0 0 10px #00ff66;'>
🔥 REFORMA DE FORNOS - {st.session_state.local_acesso} | {agora_br.strftime('%d/%m/%Y %H:%M')} Brasília 🔥
</h1>
<div style='text-align:center; color:#FFD700; font-family:Orbitron;'>ID pode estar em GALPÃO + SALA ANEXA + OFICINA | 1 ID pode ter várias MARCAS | FIFO ATIVO</div>
""", unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5=st.tabs(["📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 ESTOQUE","📊 BUSCA POR ID","📈 GRAFICOS"])

with tab1:
    with st.form("form_cad", clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1:
            id_in=st.text_input("ID* (digite e depois puxa tudo)","1")
            desc_in=st.text_input("DESCRIÇÃO*","CIMENTO FONDU")
            marca_in=st.text_input("MARCA* (1 ID pode ter várias)","FONDU")
            lote_in=st.text_input("LOTE*","")
            local_in=st.selectbox("LOCAL* (qualquer dos 3)", LOCAIS)
        with c2:
            fab_in=st.date_input("FABRICAÇÃO*", value=date.today())
            tempo_in=st.number_input("VALIDADE MESES*", value=12, min_value=1)
            unidade_in=st.selectbox("UNIDADE*",["KG","UNIDADE","SACO","BLOCO","TIJOLO","LATA","CAIXA","METRO","LITRO"])
            qtd_in=st.number_input(f"QTD/PALETE ({unidade_in})*", value=1250.0)
        with c3:
            ent_in=st.number_input("QTD PALETES*", value=11.0)
            st.metric(f"TOTAL {unidade_in}", f"{safe_float(qtd_in)*safe_float(ent_in):,.0f}")
        if st.form_submit_button("💾 CADASTRAR", type="primary", use_container_width=True):
            if not lote_in.strip() or not id_in.strip():
                st.error("ID e LOTE obrigatório")
            else:
                fab_str=fab_in.strftime("%d/%m/%Y")
                valido=calcular_valido_ate(fab_str, tempo_in)
                total=safe_float(qtd_in)*safe_float(ent_in)
                st.session_state.lista_cadastro.append({"ID":id_in.strip().upper(),"DESCRICAO":desc_in.upper().strip(),"MARCA":marca_in.upper().strip(),"LOTE":lote_in.strip().upper(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido,"QTD_PALETE":safe_float(qtd_in),"ENTRADA":safe_float(ent_in),"TOTAL":total,"UNIDADE":unidade_in.upper(),"LOCAL":local_in,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                st.success(f"✅ CADASTRADO ID {id_in} LOTE {lote_in} MARCA {marca_in} LOCAL {local_in}"); st.rerun()
    st.divider()
    if st.session_state.lista_cadastro:
        df_cad = pd.DataFrame(st.session_state.lista_cadastro)
        for idx, row in df_cad.iterrows():
            c1,c2,c3,c4 = st.columns([3,4,2,1])
            with c1: st.write(f"**ID {row.get('ID')} | LOTE {row.get('LOTE')}** | {row.get('MARCA')}")
            with c2: st.write(f"{row.get('DESCRICAO')} | {row.get('LOCAL')} | {row.get('ENTRADA')} PAL")
            with c3: st.write(f"{row.get('TOTAL')} {row.get('UNIDADE')}")
            with c4:
                if st.button("🗑️ EXCLUIR", key=f"del_cad_{idx}", type="primary"):
                    st.session_state.lista_cadastro.pop(idx)
                    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                    st.rerun()

with tab2:
    if not st.session_state.get('lista_cadastro'): st.warning("Cadastre primeiro")
    else:
        col_busca1, col_busca2 = st.columns([2,3])
        with col_busca1:
            id_busca_mov = st.text_input("🔍 DIGITE O ID PARA PUXAR TUDO", placeholder="Ex: 1, 1020...")
        with col_busca2:
            if id_busca_mov:
                dados_id = buscar_por_id(id_busca_mov)
                if dados_id:
                    total_geral = sum([safe_float(d.get('SALDO_QTD',0)) for d in dados_id])
                    st.success(f"ID {id_busca_mov} | {len(dados_id)} lotes | Marcas: {', '.join(set([d.get('MARCA','') for d in dados_id]))} | TOTAL: {total_geral:,.0f}")
        ids_disponiveis = sorted(list(set([str(r.get('ID','')).strip() for r in st.session_state.lista_cadastro if r.get('ID')])))
        c1,c2,c3=st.columns(3)
        with c1:
            id_mov_sel = st.selectbox("ID*", options=ids_disponiveis, index=ids_disponiveis.index(id_busca_mov.upper()) if id_busca_mov and id_busca_mov.upper() in ids_disponiveis else 0)
            lotes_do_id = [r for r in st.session_state.lista_cadastro if str(r.get('ID','')).upper()==str(id_mov_sel).upper()]
            marcas_do_id = sorted(list(set([str(r.get('MARCA','')).upper() for r in lotes_do_id])))
            lote_mov=st.selectbox("LOTE* (do ID)", options=sorted(list(set([r.get('LOTE','') for r in lotes_do_id]))))
            marca_mov=st.selectbox("MARCA*", options=marcas_do_id if marcas_do_id else ["SEM MARCA"])
            qtd_base=1250; unidade_base="KG"
            for r in lotes_do_id:
                if str(r.get('LOTE'))==str(lote_mov) and str(r.get('MARCA')).upper()==str(marca_mov).upper():
                    qtd_base=safe_float(r.get('QTD_PALETE',1250),1250)
                    unidade_base=str(r.get('UNIDADE','KG')).upper() or "KG"
                    break
            local_mov=st.selectbox("LOCAL ORIGEM*", LOCAIS)
        with c2:
            tipo_mov=st.selectbox("TIPO*", ["SAIDA","ENTRADA","TRANSFERENCIA"])
            paletes_mov=st.number_input(f"QTD PALETES", value=1.0, min_value=0.1, step=0.5)
            total_qtd_mov=safe_float(paletes_mov)*safe_float(qtd_base)
            st.metric(f"TOTAL {unidade_base}", f"{total_qtd_mov:,.0f}")
            local_dest = st.selectbox("Destino TRANSFER", LOCAIS, index=1)
        with c3:
            motivo=st.text_input("MOTIVO*","REFORMA FORNO")
            saldos=get_saldos_completos()
            chave_atual=f"{id_mov_sel.upper()}__{local_mov}__{marca_mov}__{lote_mov}"
            saldo_atual=saldos.get(chave_atual,{})
            if saldo_atual:
                st.metric(f"SALDO {marca_mov}", f"{safe_float(saldo_atual.get('SALDO_PALETES',0)):.1f} PAL")
        if st.button("✅ CONFIRMAR (FIFO)", type="primary", use_container_width=True):
            saldos_atual = get_saldos_completos()
            lotes_fifo = []
            for chave, d in saldos_atual.items():
                if d.get('ID','').upper()==id_mov_sel.upper() and d.get('LOCAL')==local_mov and d.get('MARCA','').upper()==marca_mov.upper():
                    if safe_float(d.get('SALDO_QTD',0))>0:
                        lotes_fifo.append((chave, d))
            try:
                lotes_fifo.sort(key=lambda x: datetime.strptime(x[1].get('FABRICACAO','01/01/2000'), "%d/%m/%Y"))
            except: pass
            saldo_total = sum([safe_float(x[1].get('SALDO_PALETES',0)) for x in lotes_fifo])
            if tipo_mov in ["SAIDA","TRANSFERENCIA"] and saldo_total < safe_float(paletes_mov)-0.001:
                st.error(f"⛔ SALDO INSUFICIENTE FIFO: {saldo_total:.1f} PAL")
            else:
                if tipo_mov=="SAIDA":
                    qtd_rest = safe_float(paletes_mov)
                    for _, dados_fifo in lotes_fifo:
                        if qtd_rest<=0: break
                        saldo_pal = safe_float(dados_fifo.get('SALDO_PALETES',0))
                        consumir = min(saldo_pal, qtd_rest)
                        st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":dados_fifo.get('LOTE_ORIG'),"MARCA":marca_mov.upper(),"TIPO":"SAIDA","PALETES":consumir,"QTD_POR_PALETE":safe_float(dados_fifo.get('QTD_PALETE_BASE',qtd_base)),"TOTAL_QTD":consumir*safe_float(dados_fifo.get('QTD_PALETE_BASE',qtd_base)),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"FIFO FAB {dados_fifo.get('FABRICACAO')}"})
                        qtd_rest-=consumir
                elif tipo_mov=="ENTRADA":
                    st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":lote_mov,"MARCA":marca_mov.upper(),"TIPO":"ENTRADA","PALETES":paletes_mov,"QTD_POR_PALETE":qtd_base,"TOTAL_QTD":total_qtd_mov,"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":"ENTRADA"})
                else:
                    qtd_rest = safe_float(paletes_mov)
                    for _, dados_fifo in lotes_fifo:
                        if qtd_rest<=0: break
                        saldo_pal = safe_float(dados_fifo.get('SALDO_PALETES',0))
                        consumir = min(saldo_pal, qtd_rest)
                        st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":dados_fifo.get('LOTE_ORIG'),"MARCA":marca_mov.upper(),"TIPO":"SAIDA","PALETES":consumir,"QTD_POR_PALETE":safe_float(dados_fifo.get('QTD_PALETE_BASE',qtd_base)),"TOTAL_QTD":consumir*safe_float(dados_fifo.get('QTD_PALETE_BASE',qtd_base)),"UNIDADE":unidade_base,"MOTIVO":f"TRANSFER -> {local_dest}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_mov,"OBS":f"TRANSFER"})
                        st.session_state.lista_mov.append({"ID":id_mov_sel.upper(),"LOTE":dados_fifo.get('LOTE_ORIG'),"MARCA":marca_mov.upper(),"TIPO":"ENTRADA","PALETES":consumir,"QTD_POR_PALETE":safe_float(dados_fifo.get('QTD_PALETE_BASE',qtd_base)),"TOTAL_QTD":consumir*safe_float(dados_fifo.get('QTD_PALETE_BASE',qtd_base)),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":local_dest,"OBS":f"TRANSFER"})
                        qtd_rest-=consumir
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success("✅ OK - FIFO"); st.rerun()

with tab3:
    saldos=get_saldos_completos()
    df_estoque=[{"ID":r.get('ID'),"LOTE":r.get('LOTE_ORIG'),"MARCA":r.get('MARCA'),"LOCAL":r.get('LOCAL'),"FAB":r.get('FABRICACAO'),"VALIDO":r.get('VALIDO_ATE'),"SALDO PAL":safe_float(r.get('SALDO_PALETES',0)),"SALDO QTD":safe_float(r.get('SALDO_QTD',0))} for r in saldos.values() if safe_float(r.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(df_estoque)
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=600)

with tab4:
    id_busca = st.text_input("Digite o ID", key="busca_tab4")
    if id_busca:
        dados = buscar_por_id(id_busca)
        if dados:
            df_busca = pd.DataFrame([{"ID": d.get('ID'),"LOTE": d.get('LOTE_ORIG'),"MARCA": d.get('MARCA'),"LOCAL": d.get('LOCAL'),"FAB": d.get('FABRICACAO'),"SALDO QTD": safe_float(d.get('SALDO_QTD',0)),"SALDO PAL": safe_float(d.get('SALDO_PALETES',0))} for d in dados])
            st.dataframe(df_busca, use_container_width=True)
            fig = px.bar(df_busca, x='LOCAL', y='SALDO QTD', color='MARCA', barmode='group', title=f'ID {id_busca} - 3 locais + marcas - FIFO')
            st.plotly_chart(fig, use_container_width=True)

with tab5:
    saldos=get_saldos_completos()
    lista=[{"ID":d.get('ID'),"LOCAL":d.get('LOCAL'),"MARCA":d.get('MARCA'),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0))} for d in saldos.values() if safe_float(d.get('SALDO_QTD',0))>0]
    df=pd.DataFrame(lista)
    if not df.empty:
        fig1=px.bar(df, x='ID', y='SALDO_QTD', color='LOCAL', barmode="group", title="Saldo por ID - 3 locais")
        st.plotly_chart(fig1, use_container_width=True)
        fig2=px.pie(df.groupby("LOCAL")[["SALDO_QTD"]].sum().reset_index(), values='SALDO_QTD', names='LOCAL', title="Galpão vs Sala Anexa vs Oficina")
        st.plotly_chart(fig2, use_container_width=True)
