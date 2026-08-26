import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_EMAILS = "emails.csv"
LOCAL_GALPAO = "GALPÃO DE MATERIAIS REFRATARIOS"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"

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
        lote=str(r.get('LOTE','')).strip()
        if not lote: continue
        local = str(r.get('LOCAL', LOCAL_GALPAO))
        if "GALP" in local.upper(): local = LOCAL_GALPAO
        else: local = LOCAL_OFICINA if "OFIC" in local.upper() else LOCAL_GALPAO
        qtd_palete=safe_float(r.get('QTD_PALETE',0),0)
        entrada_pal=safe_float(r.get('ENTRADA',0),0)
        total=safe_float(r.get('TOTAL',0),0)
        if total==0: total=qtd_palete*entrada_pal
        unidade=str(r.get('UNIDADE','KG')).upper().strip() or "KG"
        chave = f"{lote}__{local}"
        if chave not in saldos:
            saldos[chave]=r.copy()
            saldos[chave]['LOCAL']=local
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
        local_mov=str(m.get('LOCAL_MOV','')).strip()
        if "GALP" in local_mov.upper(): local_mov=LOCAL_GALPAO
        else: local_mov=LOCAL_OFICINA
        tipo=str(m.get('TIPO','')).upper()
        paletes=safe_float(m.get('PALETES',0),0)
        qtd=safe_float(m.get('TOTAL_QTD',0),0)
        chave = f"{lote}__{local_mov}"
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

st.markdown(f"<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00; font-family:Arial Black;'>🔥 {st.session_state.local_acesso} | {agora_br.strftime('%d/%m/%Y %H:%M')} Brasília 🔥</h1>", unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5=st.tabs(["📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 ESTOQUE","📊 LOTES","📈 GRAFICOS"])

with tab1:
    with st.form("form_cad", clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1:
            id_in=st.text_input("ID*","1")
            desc_in=st.text_input("DESCRIÇÃO*","CIMENTO FONDU")
            marca_in=st.text_input("MARCA*","FONDU")
            lote_in=st.text_input("LOTE*","")
            local_in=st.selectbox("LOCAL*", [LOCAL_GALPAO, LOCAL_OFICINA])
        with c2:
            fab_in=st.date_input("FABRICAÇÃO*", value=date.today())
            tempo_in=st.number_input("VALIDADE MESES*", value=12, min_value=1)
            unidade_in=st.selectbox("UNIDADE*",["KG","UNIDADE","SACO","BLOCO","TIJOLO","LATA","CAIXA","METRO","LITRO"])
            qtd_in=st.number_input(f"QTD/PALETE ({unidade_in})*", value=1250.0)
        with c3:
            ent_in=st.number_input("QTD PALETES*", value=11.0)
            st.metric(f"TOTAL {unidade_in}", f"{safe_float(qtd_in)*safe_float(ent_in):,.0f}")
        if st.form_submit_button("💾 CADASTRAR", type="primary", use_container_width=True):
            if not lote_in.strip():
                st.error("LOTE obrigatório")
            else:
                fab_str=fab_in.strftime("%d/%m/%Y")
                valido=calcular_valido_ate(fab_str, tempo_in)
                total=safe_float(qtd_in)*safe_float(ent_in)
                st.session_state.lista_cadastro.append({"ID":id_in.strip(),"DESCRICAO":desc_in.upper().strip(),"MARCA":marca_in.upper().strip(),"LOTE":lote_in.strip(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido,"QTD_PALETE":safe_float(qtd_in),"ENTRADA":safe_float(ent_in),"TOTAL":total,"UNIDADE":unidade_in.upper(),"LOCAL":local_in,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")})
                pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                st.success(f"✅ CADASTRADO LOTE {lote_in}"); st.rerun()

    st.divider()
    st.subheader("📋 CADASTROS - COM BOTÃO EXCLUIR")
    if st.session_state.lista_cadastro:
        df_cad = pd.DataFrame(st.session_state.lista_cadastro)
        for idx, row in df_cad.iterrows():
            c1,c2,c3,c4 = st.columns([3,4,2,1])
            with c1: st.write(f"**LOTE {row.get('LOTE')}** | ID {row.get('ID')}")
            with c2: st.write(f"{row.get('DESCRICAO')} | {row.get('LOCAL')} | {row.get('ENTRADA')} PAL")
            with c3: st.write(f"{row.get('TOTAL')} {row.get('UNIDADE')}")
            with c4:
                if st.button("🗑️ EXCLUIR", key=f"del_cad_{idx}", type="primary"):
                    st.session_state.lista_cadastro.pop(idx)
                    pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
                    st.warning(f"Excluído LOTE {row.get('LOTE')}")
                    st.rerun()
        st.dataframe(df_cad, use_container_width=True)

with tab2:
    st.markdown("### 🔄 MOVIMENTAÇÃO - AUTO PREENCHIMENTO + EXCLUIR")
    if not st.session_state.get('lista_cadastro'): st.warning("Cadastre primeiro")
    else:
        lotes_disponiveis=list(set([str(r.get('LOTE','')) for r in st.session_state.lista_cadastro if r.get('LOTE')]))
        c1,c2,c3=st.columns(3)
        with c1:
            lote_mov=st.selectbox("LOTE*", options=lotes_disponiveis, key="sel_lote_mov")
            qtd_base=1250; unidade_base="KG"; desc_base=""
            for r in st.session_state.lista_cadastro:
                if str(r.get('LOTE'))==str(lote_mov):
                    qtd_base=safe_float(r.get('QTD_PALETE',1250),1250)
                    unidade_base=str(r.get('UNIDADE','KG')).upper() or "KG"
                    desc_base=str(r.get('DESCRICAO',''))
                    break
            st.info(f"{desc_base} | {qtd_base:.0f} {unidade_base}/PAL")
            local_mov=st.selectbox("LOCAL*", [LOCAL_GALPAO, LOCAL_OFICINA], key="sel_local_mov")
        ult_qtd=1.0; ult_tipo="ENTRADA"; ult_data=""
        if st.session_state.get('lista_mov'):
            movs_lote=[m for m in st.session_state.lista_mov if str(m.get('LOTE'))==str(lote_mov)]
            if movs_lote:
                ultimo=movs_lote[-1]
                ult_qtd=safe_float(ultimo.get('PALETES',1.0),1.0)
                ult_tipo=str(ultimo.get('TIPO','ENTRADA'))
                ult_data=str(ultimo.get('DATA',''))+" "+str(ultimo.get('HORA',''))
        with c2:
            tipo_mov=st.selectbox("TIPO*", ["SAIDA","ENTRADA"], index=0 if ult_tipo=="SAIDA" else 1, key="sel_tipo_mov")
            paletes_mov=st.number_input(f"QTD PALETES - última {ult_qtd:.1f} ({ult_data})", value=float(ult_qtd), min_value=0.1, step=0.5, key=f"num_pal_{lote_mov}")
            total_qtd_mov=safe_float(paletes_mov)*safe_float(qtd_base)
            st.metric(f"TOTAL {unidade_base}", f"{total_qtd_mov:,.0f}")
        with c3:
            motivo=st.text_input("MOTIVO*","REFORMA FORNO")
            saldos=get_saldos_completos()
            chave_atual=f"{lote_mov}__{local_mov}"
            saldo_atual=saldos.get(chave_atual,{})
            if saldo_atual:
                st.metric(f"SALDO PAL {local_mov}", f"{safe_float(saldo_atual.get('SALDO_PALETES',0)):.1f}")
                st.metric(f"SALDO {unidade_base}", f"{safe_float(saldo_atual.get('SALDO_QTD',0)):,.0f}")
        if st.button("✅ CONFIRMAR", type="primary", use_container_width=True):
            if tipo_mov=="SAIDA" and saldo_atual and safe_float(saldo_atual.get('SALDO_PALETES',0))<safe_float(paletes_mov):
                st.error(f"⛔ SALDO INSUFICIENTE {safe_float(saldo_atual.get('SALDO_PALETES',0)):.1f}")
            else:
                if local_mov==LOCAL_OFICINA and tipo_mov=="ENTRADA":
                    st.session_state.lista_mov.append({"LOTE":str(lote_mov),"TIPO":"SAIDA","PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_base),"TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":f"AUTO TRANSFER -> {motivo}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":LOCAL_GALPAO,"OBS":"TRANSFER AUTO"})
                    st.session_state.lista_mov.append({"LOTE":str(lote_mov),"TIPO":"ENTRADA","PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_base),"TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":LOCAL_OFICINA,"OBS":"TRANSFER AUTO"})
                elif local_mov==LOCAL_GALPAO and tipo_mov=="SAIDA":
                    st.session_state.lista_mov.append({"LOTE":str(lote_mov),"TIPO":"SAIDA","PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_base),"TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":f"AUTO TRANSFER -> {motivo}","DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":LOCAL_GALPAO,"OBS":"TRANSFER AUTO"})
                    st.session_state.lista_mov.append({"LOTE":str(lote_mov),"TIPO":"ENTRADA","PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_base),"TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":LOCAL_OFICINA,"OBS":"TRANSFER AUTO"})
                elif local_mov==LOCAL_OFICINA and tipo_mov=="SAIDA":
                    st.session_state.lista_mov.append({"LOTE":str(lote_mov),"TIPO":"SAIDA","PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_base),"TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":LOCAL_OFICINA,"OBS":"SAIDA REAL"})
                else:
                    st.session_state.lista_mov.append({"LOTE":str(lote_mov),"TIPO":"ENTRADA","PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_base),"TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now(fuso).strftime("%H:%M"),"LOCAL_MOV":LOCAL_GALPAO,"OBS":"ENTRADA REAL"})
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success("✅ REGISTRADO - TUDO ATUALIZADO")
                st.rerun()

        st.divider()
        st.subheader("📋 MOVIMENTAÇÕES - COM BOTÃO EXCLUIR")
        if st.session_state.get('lista_mov'):
            df_mov=pd.DataFrame(st.session_state.lista_mov)
            for idx, row in df_mov.sort_index(ascending=False).iterrows():
                c1,c2,c3,c4 = st.columns([2,4,2,1])
                with c1: st.write(f"**{row.get('DATA')} {row.get('HORA')}** | LOTE {row.get('LOTE')}")
                with c2: st.write(f"{row.get('TIPO')} | {row.get('LOCAL_MOV')} | {row.get('PALETES')} PAL = {row.get('TOTAL_QTD')} {row.get('UNIDADE')} | {row.get('MOTIVO')}")
                with c3: st.write(f"{row.get('OBS','')}")
                with c4:
                    if st.button("🗑️", key=f"del_mov_{idx}", type="primary"):
                        st.session_state.lista_mov.pop(idx)
                        pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                        st.warning("Excluído!")
                        st.rerun()

with tab3:
    st.markdown("### 📦 ESTOQUE ATUALIZADO AUTOMATICAMENTE")
    if not st.session_state.get('lista_cadastro'): st.warning("Sem cadastro")
    else:
        saldos=get_saldos_completos()
        df_estoque=[]
        for chave,r in saldos.items():
            df_estoque.append({"LOTE":r.get('LOTE_ORIG'),"ID":r.get('ID'),"DESCRIÇÃO":r.get('DESCRICAO'),"MARCA":r.get('MARCA'),"LOCAL":r.get('LOCAL'),"FAB":r.get('FABRICACAO'),"VÁLIDO ATÉ":r.get('VALIDO_ATE'),"UNIDADE":r.get('UNIDADE'),"QTD/PAL":safe_float(r.get('QTD_PALETE_BASE',0)),"SALDO PAL":safe_float(r.get('SALDO_PALETES',0)),"SALDO QTD":safe_float(r.get('SALDO_QTD',0)),"ENT PAL":safe_float(r.get('ENTRADAS_PALETES',0)),"SAI PAL":safe_float(r.get('SAIDAS_PALETES',0))})
        df=pd.DataFrame(df_estoque)
        if not df.empty:
            st.dataframe(df.sort_values(by="SALDO QTD", ascending=False), use_container_width=True, height=600)
        else:
            st.info("Sem estoque")

with tab4:
    st.markdown("### 📊 LOTES - BARRAS")
    if not st.session_state.get('lista_cadastro'): st.warning("Cadastre")
    else:
        mapa={}
        for r in st.session_state.lista_cadastro:
            idk=str(r.get('ID','?')).strip()
            if idk not in mapa: mapa[idk]={"ID":idk,"DESCRICAO":r.get('DESCRICAO',''),"QTD":0}
            mapa[idk]["QTD"]+=1
        cols=st.columns(4)
        for idx,(idk,info) in enumerate(mapa.items()):
            with cols[idx%4]:
                if st.button(f"ID {info['ID']} - {info['DESCRICAO']} ({info['QTD']})", key=f"btn_ver_{idk}_{idx}", use_container_width=True, type="primary"):
                    st.session_state.id_selecionado=idk
        if st.session_state.get('id_selecionado'):
            id_sel=str(st.session_state.id_selecionado)
            lotes=[r for r in st.session_state.lista_cadastro if str(r.get('ID'))==id_sel]
            saldos=get_saldos_completos()
            st.success(f"ID {id_sel} - {len(lotes)} LOTES")
            for i,r in enumerate(sorted(lotes, key=lambda x: str(x.get('LOTE','')))):
                lote=str(r.get('LOTE'))
                saldo_g=saldos.get(f"{lote}__{LOCAL_GALPAO}",{})
                saldo_o=saldos.get(f"{lote}__{LOCAL_OFICINA}",{})
                saldo_qtd=safe_float(saldo_g.get('SALDO_QTD',0))+safe_float(saldo_o.get('SALDO_QTD',0))
                saldo_pal=safe_float(saldo_g.get('SALDO_PALETES',0))+safe_float(saldo_o.get('SALDO_PALETES',0))
                unidade=str(r.get('UNIDADE','KG'))
                st.info(f"LOTE {lote} | VAL {r.get('VALIDO_ATE')} | TOTAL {saldo_qtd:,.0f} {unidade} ({saldo_pal:.1f} PAL) | GALPÃO {safe_float(saldo_g.get('SALDO_QTD',0)):,.0f} | OFICINA {safe_float(saldo_o.get('SALDO_QTD',0)):,.0f}")

with tab5:
    st.markdown("### 📈 GRAFICOS - ATUALIZAÇÃO AUTOMÁTICA")
    if not st.session_state.get('lista_cadastro'): st.warning("Sem dados")
    else:
        saldos=get_saldos_completos()
        if not saldos: st.warning("Sem saldo")
        else:
            lista=[]
            for chave,d in saldos.items():
                lista.append({"LOTE":str(d.get('LOTE_ORIG')),"DESCRICAO":f"ID {d.get('ID','?')} - {str(d.get('DESCRICAO',''))[:20]}","LOCAL":str(d.get('LOCAL')),"VALIDO_ATE":str(d.get('VALIDO_ATE','')),"UNIDADE":str(d.get('UNIDADE','KG')),"SALDO_QTD":safe_float(d.get('SALDO_QTD',0)),"SALDO_PAL":safe_float(d.get('SALDO_PALETES',0)),"TEXTO_QTD":f"{safe_float(d.get('SALDO_QTD',0)):,.0f}","TEXTO_PAL":f"{safe_float(d.get('SALDO_PALETES',0)):.1f} PAL"})
            df=pd.DataFrame(lista)
            df=df[df["SALDO_QTD"]>0]
            if df.empty: st.info("Sem saldo")
            else:
                col1,col2,col3,col4=st.columns(4)
                total_geral_qtd=df["SALDO_QTD"].sum()
                total_geral_pal=df["SALDO_PAL"].sum()
                total_galpao=df[df["LOCAL"]==LOCAL_GALPAO]["SALDO_QTD"].sum()
                total_oficina=df[df["LOCAL"]==LOCAL_OFICINA]["SALDO_QTD"].sum()
                col1.metric("TOTAL GERAL QTD", f"{total_geral_qtd:,.0f}")
                col2.metric("TOTAL PAL", f"{total_geral_pal:.1f}")
                col3.metric("GALPÃO", f"{total_galpao:,.0f}")
                col4.metric("OFICINA", f"{total_oficina:,.0f}")
                fig1=px.bar(df, x='DESCRICAO', y='SALDO_QTD', color='LOCAL', barmode="group", text='TEXTO_QTD', title="SALDO QTD POR PRODUTO")
                fig1.update_traces(textposition='outside', textfont_size=14, textfont_family="Arial Black")
                fig1.update_layout(height=600, plot_bgcolor='#A8C5A2')
                st.plotly_chart(fig1, use_container_width=True, key="graf1")
                c1,c2=st.columns(2)
                with c1:
                    fig2=px.bar(df, x='LOTE', y='SALDO_PAL', color='LOCAL', text='TEXTO_PAL', title="PALETES POR LOTE")
                    fig2.update_traces(textposition='outside', textfont_size=14)
                    fig2.update_layout(height=500)
                    st.plotly_chart(fig2, use_container_width=True, key="graf2")
                with c2:
                    df_pizza=df.groupby("LOCAL")[["SALDO_QTD"]].sum().reset_index()
                    fig_pizza=px.pie(df_pizza, values='SALDO_QTD', names='LOCAL', title="GALPÃO vs OFICINA", hole=0.3)
                    fig_pizza.update_traces(textinfo='value+percent', textfont_size=16)
                    st.plotly_chart(fig_pizza, use_container_width=True, key="graf_pizza")
                fig3=px.bar(df.sort_values(by="VALIDO_ATE"), x='LOTE', y='SALDO_QTD', color='LOCAL', barmode="group", text='TEXTO_QTD', title="SALDO QTD POR LOTE")
                fig3.update_traces(textposition='outside', textfont_size=12)
                fig3.update_layout(height=700, xaxis_tickangle=-45, plot_bgcolor='#A8C5A2')
                st.plotly_chart(fig3, use_container_width=True, key="graf3")
                st.dataframe(df.sort_values(by="SALDO_QTD", ascending=False), use_container_width=True, height=500)
