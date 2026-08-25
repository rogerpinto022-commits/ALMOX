import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"

st.markdown("""
<style>
.block-container { z-index:2; position:relative; }
.wm { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; opacity:0.10; pointer-events:none; display:flex; flex-wrap:wrap; gap:80px; justify-content:center; align-content:center; }
.wm span { font-size:28px; font-weight:900; color:#ff4e00; transform:rotate(-30deg); border:3px solid #ff4e00; padding:8px 14px; border-radius:10px; }
.top { position:fixed; top:10px; right:15px; z-index:9999; background:linear-gradient(90deg,#ff4e00,#ff0000); color:#fff; font-weight:900; padding:6px 16px; border-radius:20px; border:2px solid #000; }
.tabela { width:100%; border-collapse:collapse; font-size:11px; display:block; overflow-x:auto; white-space:nowrap; }
.tabela th { background:#1a252f; color:#fff; padding:10px 6px; border:2px solid #000; text-align:center; font-family:Arial Black; font-size:10px; }
.tabela td { padding:8px 5px; border:1.5px solid #000; text-align:center; background:#fff; color:#000; font-weight:700; font-size:11px; }
.lote { background:#00ff66!important; font-size:13px; border:3px solid #000!important; }
.val { background:#ffff00!important; border:2px solid #000!important; }
.fab { background:#a0d8ff!important; }
.fundo-verde { background:#A8C5A2; border-left:6px solid #000; padding:20px 10px 20px 0; margin:15px 0; border:3px solid #000; }
.barra { height:54px; margin:16px 0; border:2.5px solid #000; display:flex; align-items:center; padding-left:12px; font-family:Arial Black; font-size:11px; box-shadow:4px 4px 0 #000; }
.azul { background:#6FA8DC; }.branca { background:#FFFFFF; }.cinza { background:#8A8A8A; color:#fff; }
.card { border:3px solid #000; border-radius:12px; padding:12px; text-align:center; background:white; box-shadow:5px 5px 0 #000; }
</style>
<div class="wm"><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span><span>REFORMA DE FORNOS</span></div>
<div class="top">🔥 REFORMA DE FORNOS 🔥</div>
""", unsafe_allow_html=True)

def carregar_seguro(caminho):
    if not os.path.exists(caminho): return []
    try:
        df=pd.read_csv(caminho).fillna("")
        df.columns=[str(c).upper().strip() for c in df.columns]
        for col in ["ID","DESCRICAO","MARCA","LOTE","FABRICACAO","TEMPO_VALIDADE","VALIDO_ATE","QTD_PALETE","ENTRADA","TOTAL","DATA_CADASTRO"]:
            if col not in df.columns: df[col]=""
        df["TOTAL"]=pd.to_numeric(df["TOTAL"], errors='coerce').fillna(0)
        return df.to_dict('records')
    except:
        try: os.remove(caminho)
        except: pass
        return []

if 'lista_cadastro' not in st.session_state: st.session_state.lista_cadastro=carregar_seguro(ARQ_CAD)
if 'lista_mov' not in st.session_state: st.session_state.lista_mov=carregar_seguro(ARQ_MOV)
if 'id_selecionado' not in st.session_state: st.session_state.id_selecionado=None

def calcular_valido_ate(fab_str, tempo_meses):
    try:
        fab=datetime.strptime(fab_str, "%d/%m/%Y")
        valido=fab + relativedelta(months=int(tempo_meses))
        return valido.strftime("%d/%m/%Y")
    except: return "00/00/0000"

def get_saldos_completos():
    saldos={}
    for r in st.session_state.get('lista_cadastro',[]):
        lote=str(r.get('LOTE','')).strip()
        if not lote: continue
        qtd_palete=float(r.get('QTD_PALETE',0) or 0)
        if lote not in saldos:
            saldos[lote]=r.copy()
            saldos[lote]['ENTRADAS_PALETES']=float(r.get('ENTRADA',0) or 0)
            saldos[lote]['SAIDAS_PALETES']=0
            saldos[lote]['ENTRADAS_KG']=float(r.get('TOTAL',0) or 0)
            saldos[lote]['SAIDAS_KG']=0
            saldos[lote]['SALDO_PALETES']=float(r.get('ENTRADA',0) or 0)
            saldos[lote]['SALDO_KG']=float(r.get('TOTAL',0) or 0)
            saldos[lote]['QTD_PALETE_BASE']=qtd_palete
        else:
            saldos[lote]['ENTRADAS_PALETES']+=float(r.get('ENTRADA',0) or 0)
            saldos[lote]['ENTRADAS_KG']+=float(r.get('TOTAL',0) or 0)
            saldos[lote]['SALDO_PALETES']+=float(r.get('ENTRADA',0) or 0)
            saldos[lote]['SALDO_KG']+=float(r.get('TOTAL',0) or 0)
    for m in st.session_state.get('lista_mov',[]):
        lote=str(m.get('LOTE','')).strip()
        if lote in saldos:
            try:
                paletes=float(m.get('PALETES',0) or 0)
                kg=float(m.get('TOTAL_KG',0) or 0)
                if str(m.get('TIPO','')).upper()=="ENTRADA":
                    saldos[lote]['ENTRADAS_PALETES']+=paletes
                    saldos[lote]['ENTRADAS_KG']+=kg
                    saldos[lote]['SALDO_PALETES']+=paletes
                    saldos[lote]['SALDO_KG']+=kg
                else:
                    saldos[lote]['SAIDAS_PALETES']+=paletes
                    saldos[lote]['SAIDAS_KG']+=kg
                    saldos[lote]['SALDO_PALETES']-=paletes
                    saldos[lote]['SALDO_KG']-=kg
            except: pass
    return saldos

st.markdown("<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00; font-family:Arial Black;'>🔥 REFORMA DE FORNOS - CONTROLE POR PALETES 🔥</h1>", unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5=st.tabs(["📝 CADASTRO","🔄 ENTRADA/SAIDA POR PALETES","📦 ESTOQUE COMPLETO","📊 LOTES - BARRAS VALIDADE","📈 GRAFICOS"])

with tab1:
    with st.form("form_cadastro_principal", clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1:
            id_in=st.text_input("ID*","1")
            desc_in=st.text_input("DESCRIÇÃO*","CIMENTO FONDU")
            marca_in=st.text_input("MARCA*","FONDU")
            lote_in=st.text_input("LOTE*","999999999")
        with c2:
            fab_in=st.date_input("DATA FABRICAÇÃO*", value=date.today())
            tempo_in=st.number_input("TEMPO VALIDADE (MESES)*", value=12, min_value=1)
            qtd_in=st.number_input("QTD KG POR PALETE*", value=1250.0)
            ent_in=st.number_input("QTD PALETES ENTRADA*", value=11.0)
        with c3:
            local_in=st.text_input("LOCAL","FORNO 1")
            obs_in=st.text_input("OBS","REFORMA")
            total_prev=float(qtd_in)*float(ent_in)
            st.metric("TOTAL KG CALCULADO", f"{total_prev:,.0f} KG")
            st.metric("TOTAL PALETES", f"{ent_in:.0f} PALETES")
        if st.form_submit_button("💾 CADASTRAR", type="primary", use_container_width=True):
            fab_str=fab_in.strftime("%d/%m/%Y")
            valido_ate=calcular_valido_ate(fab_str, tempo_in)
            total=float(qtd_in)*float(ent_in)
            st.session_state.lista_cadastro.append({
                "ID":str(id_in).strip(),"DESCRICAO":str(desc_in).upper().strip(),"MARCA":str(marca_in).upper().strip(),
                "LOTE":str(lote_in).strip(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido_ate,
                "QTD_PALETE":float(qtd_in),"ENTRADA":float(ent_in),"TOTAL":float(total),
                "LOCAL":local_in,"OBS":obs_in,"DATA_CADASTRO":date.today().strftime("%d/%m/%Y")
            })
            pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
            st.success(f"✅ LOTE {lote_in} - {ent_in:.0f} PALETES = {total:.0f} KG"); st.rerun()

with tab2:
    st.markdown("### 🔄 MOVIMENTAÇÃO POR QTD DE PALETES - APP CALCULA TOTAIS")
    if not st.session_state.get('lista_cadastro'):
        st.warning("Cadastre primeiro")
    else:
        # Busca dados do lote selecionado
        lotes_disponiveis = [str(r.get('LOTE','')) for r in st.session_state.lista_cadastro if r.get('LOTE')]
        c1,c2,c3=st.columns(3)
        with c1:
            lote_mov=st.selectbox("LOTE*", options=lotes_disponiveis, key="sel_lote_mov")
            # pega qtd por palete desse lote
            qtd_por_palete_base=1250
            fab_lote=""
            valido_lote=""
            for r in st.session_state.lista_cadastro:
                if str(r.get('LOTE'))==str(lote_mov):
                    qtd_por_palete_base=float(r.get('QTD_PALETE',1250) or 1250)
                    fab_lote=r.get('FABRICACAO','')
                    valido_lote=r.get('VALIDO_ATE','')
                    break
            st.info(f"📌 LOTE {lote_mov}\n\nQTD/PALETE: {qtd_por_palete_base:.0f} KG\n\nFAB: {fab_lote}\n\nVÁLIDO ATÉ: {valido_lote}")
        with c2:
            tipo_mov=st.selectbox("TIPO*", ["SAIDA","ENTRADA"], key="sel_tipo_mov")
            paletes_mov=st.number_input("QTD PALETES* (entrada/saida)", value=1.0, min_value=0.1, step=0.5, key="num_paletes_mov")
            total_kg_mov=float(paletes_mov)*float(qtd_por_palete_base)
            st.metric("TOTAL KG CALCULADO AUTOMATICAMENTE", f"{total_kg_mov:,.0f} KG", f"{paletes_mov:.1f} PALETES x {qtd_por_palete_base:.0f} KG")
        with c3:
            motivo=st.text_input("MOTIVO*","CONSUMO REFORMA FORNO 2", key="txt_motivo")
            st.write(f"Data: {date.today().strftime('%d/%m/%Y')} {datetime.now().strftime('%H:%M')}")
            # mostra saldo atual
            saldos=get_saldos_completos()
            saldo_atual=saldos.get(str(lote_mov),{})
            if saldo_atual:
                st.metric("SALDO ATUAL PALETES", f"{float(saldo_atual.get('SALDO_PALETES',0)):.1f}")
                st.metric("SALDO ATUAL KG", f"{float(saldo_atual.get('SALDO_KG',0)):,.0f} KG")

        if st.button("✅ REGISTRAR MOVIMENTAÇÃO (PALETES -> KG AUTOMÁTICO)", type="primary", use_container_width=True, key="btn_reg_mov"):
            if total_kg_mov<=0:
                st.error("QTD inválida")
            else:
                # verifica saldo se for saída
                if tipo_mov=="SAIDA" and saldo_atual and float(saldo_atual.get('SALDO_PALETES',0))<float(paletes_mov):
                    st.error(f"⛔ SALDO INSUFICIENTE! Saldo: {float(saldo_atual.get('SALDO_PALETES',0)):.1f} PALETES")
                else:
                    st.session_state.lista_mov.append({
                        "LOTE":str(lote_mov),"TIPO":tipo_mov,"PALETES":float(paletes_mov),"QTD_POR_PALETE":float(qtd_por_palete_base),
                        "TOTAL_KG":float(total_kg_mov),"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now().strftime("%H:%M")
                    })
                    pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                    st.success(f"✅ {tipo_mov} REGISTRADA: {paletes_mov:.1f} PALETES = {total_kg_mov:,.0f} KG no LOTE {lote_mov}"); st.rerun()

        if st.session_state.get('lista_mov'):
            st.markdown("#### 📋 HISTÓRICO MOVIMENTAÇÕES POR PALETES")
            df_mov=pd.DataFrame(st.session_state.lista_mov)
            st.dataframe(df_mov, use_container_width=True)
            # resumo
            total_entr_pal=df_mov[df_mov['TIPO']=='ENTRADA']['PALETES'].sum() if 'PALETES' in df_mov.columns else 0
            total_said_pal=df_mov[df_mov['TIPO']=='SAIDA']['PALETES'].sum() if 'PALETES' in df_mov.columns else 0
            c1,c2=st.columns(2)
            c1.metric("TOTAL ENTRADAS", f"{total_entr_pal:.1f} PALETES")
            c2.metric("TOTAL SAIDAS", f"{total_said_pal:.1f} PALETES")

with tab3:
    st.markdown("### 📦 ESTOQUE COMPLETO - ATUALIZADO AUTOMATICAMENTE")
    if not st.session_state.get('lista_cadastro'): st.warning("Sem cadastro")
    else:
        saldos=get_saldos_completos()
        total_geral_kg=sum([float(v.get('SALDO_KG',0) or 0) for v in saldos.values()])
        total_geral_pal=sum([float(v.get('SALDO_PALETES',0) or 0) for v in saldos.values()])
        c1,c2,c3,c4=st.columns(4)
        c1.markdown(f"<div class='card'><h4>📦 SALDO KG</h4><h2 style='color:#ff4e00;'>{total_geral_kg:,.0f} KG</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='card'><h4>📦 SALDO PALETES</h4><h2>{total_geral_pal:.1f}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='card'><h4>📥 ENTRADAS KG</h4><h2 style='color:green;'>{sum([float(v.get('ENTRADAS_KG',0) or 0) for v in saldos.values()]):,.0f}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='card'><h4>📤 SAIDAS KG</h4><h2 style='color:red;'>{sum([float(v.get('SAIDAS_KG',0) or 0) for v in saldos.values()]):,.0f}</h2></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        html="""<table class="tabela"><tr><th>ID</th><th>DESCRIÇÃO</th><th>LOTE</th><th>FABRICAÇÃO</th><th>TEMPO</th><th>VÁLIDO ATÉ</th><th>QTD/PAL</th><th>ENTRADAS PAL</th><th>SAIDAS PAL</th><th>SALDO PAL</th><th>ENTRADAS KG</th><th>SAIDAS KG</th><th>SALDO KG</th><th>STATUS</th></tr>"""
        for lote,r in saldos.items():
            saldo_kg=float(r.get('SALDO_KG',0) or 0)
            saldo_pal=float(r.get('SALDO_PALETES',0) or 0)
            html+=f"""<tr><td><b>{r.get('ID','')}</b></td><td>{r.get('DESCRICAO','')}</td><td class='lote'>{lote}</td><td class='fab'><b>{r.get('FABRICACAO','')}</b></td><td>{r.get('TEMPO_VALIDADE','')}M</td><td class='val'><b>{r.get('VALIDO_ATE','')}</b></td><td>{float(r.get('QTD_PALETE_BASE',0) or r.get('QTD_PALETE',0)):,.0f}</td><td style='background:#a0ffa0;'>{float(r.get('ENTRADAS_PALETES',0)):.1f}</td><td style='background:#ffb0b0;'>{float(r.get('SAIDAS_PALETES',0)):.1f}</td><td style='background:#7fff7f;'><b>{saldo_pal:.1f}</b></td><td style='background:#a0ffa0;'>{float(r.get('ENTRADAS_KG',0)):,.0f}</td><td style='background:#ffb0b0;'>{float(r.get('SAIDAS_KG',0)):,.0f}</td><td style='background:#7fff7f;'><b>{saldo_kg:,.0f}</b></td><td>{'✅ OK' if saldo_kg>0 else '⛔ ZERADO'}</td></tr>"""
        html+="</table>"
        st.markdown(html, unsafe_allow_html=True)

with tab4:
    st.markdown("### 📊 LOTES DO PRODUTO - GRAFICO DE BARRAS VALIDADE")
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
                if st.button(f"ID {info['ID']} - {info['DESCRICAO']} ({info['QTD']} LOTES)", key=f"btn_ver_{idk}_{idx}", use_container_width=True, type="primary"):
                    st.session_state.id_selecionado=idk
        if st.session_state.get('id_selecionado'):
            id_sel=str(st.session_state.id_selecionado)
            lotes=[r for r in st.session_state.lista_cadastro if str(r.get('ID'))==id_sel]
            saldos=get_saldos_completos()
            st.success(f"ID {id_sel} - {lotes[0].get('DESCRICAO')} - {len(lotes)} LOTES")
            html="""<table class="tabela"><tr><th>LOTE</th><th>FAB</th><th>VÁLIDO ATÉ</th><th>QTD/PAL</th><th>SALDO PAL</th><th>SALDO KG</th></tr>"""
            for r in sorted(lotes, key=lambda x: str(x.get('LOTE',''))):
                lote=str(r.get('LOTE','')); s=saldos.get(lote,{})
                html+=f"<tr><td class='lote'>{lote}</td><td class='fab'>{r.get('FABRICACAO','')}</td><td class='val'><b>{r.get('VALIDO_ATE','')}</b></td><td>{float(r.get('QTD_PALETE',0)):,.0f}</td><td style='background:#7fff7f;'>{float(s.get('SALDO_PALETES',0) or 0):.1f}</td><td style='background:#7fff7f;'><b>{float(s.get('SALDO_KG',0) or 0):,.0f}</b></td></tr>"
            html+="</table>"
            st.markdown(html, unsafe_allow_html=True)
            st.markdown('<div style="background:#000; color:#fff; padding:8px; text-align:center; font-family:Arial Black; margin-top:20px; border:3px solid #00ff66;">📊 GRAFICO DE BARRAS - VALIDADE - FUNDO VERDE</div><div class="fundo-verde">', unsafe_allow_html=True)
            max_t=max([float(saldos.get(str(r.get('LOTE')),{}).get('SALDO_KG',0) or 0) for r in lotes]) or 1
            for i,r in enumerate(sorted(lotes, key=lambda x: str(x.get('LOTE','')))):
                lote=str(r.get('LOTE')); saldo_kg=float(saldos.get(lote,{}).get('SALDO_KG',0) or 0)
                prop=30+(saldo_kg/max_t*65) if max_t>0 else 50
                cor=["azul","branca","cinza","branca"][i%4]
                st.markdown(f'<div class="barra {cor}" style="width:{prop:.1f}%;">LOTE {r.get("LOTE")} | FAB {r.get("FABRICACAO")} | VÁLIDO ATÉ {r.get("VALIDO_ATE")} | SALDO {saldo_kg:,.0f} KG ({float(saldos.get(lote,{}).get("SALDO_PALETES",0) or 0):.1f} PAL)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown("### 📈 GRAFICOS")
    if not st.session_state.get('lista_cadastro'): st.warning("Sem dados")
    else:
        saldos=get_saldos_completos()
        df=pd.DataFrame(list(saldos.values()))
        if not df.empty and "SALDO_KG" in df.columns:
            df["SALDO_KG_NUM"]=pd.to_numeric(df["SALDO_KG"], errors='coerce').fillna(0)
            c1,c2=st.columns(2)
            with c1:
                fig1=px.bar(df, x='DESCRICAO', y='SALDO_KG_NUM', color='ID', title="SALDO ATUAL KG POR PRODUTO")
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                fig2=px.bar(df, x='DESCRICAO', y='SALDO_PALETES', color='ID', title="SALDO ATUAL PALETES POR PRODUTO")
                st.plotly_chart(fig2, use_container_width=True)
            fig3=px.bar(df, x='LOTE', y='SALDO_KG_NUM', color='VALIDO_ATE', title="GRAFICO BARRAS - SALDO KG X VALIDADE")
            fig3.update_layout(plot_bgcolor='#A8C5A2')
            st.plotly_chart(fig3, use_container_width=True)
