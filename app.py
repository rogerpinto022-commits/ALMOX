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
.tabela { width:100%; border-collapse:collapse; font-size:12px; display:block; overflow-x:auto; white-space:nowrap; }
.tabela th { background:#1a252f; color:#fff; padding:10px 6px; border:2px solid #000; text-align:center; font-family:Arial Black; font-size:11px; position:sticky; top:0; }
.tabela td { padding:8px 5px; border:1.5px solid #000; text-align:center; background:#fff; color:#000; font-weight:700; font-size:12px; }
.lote { background:#00ff66!important; font-size:14px; border:3px solid #000!important; }
.val { background:#ffff00!important; border:2px solid #000!important; }
.fab { background:#a0d8ff!important; }
.saldo-pos { background:#7fff7f!important; }
.saldo-zero { background:#ff6666!important; color:white!important; }
.fundo-verde { background:#A8C5A2; border-left:6px solid #000; padding:20px 10px 20px 0; margin:15px 0; border:3px solid #000; }
.barra { height:54px; margin:16px 0; border:2.5px solid #000; display:flex; align-items:center; padding-left:12px; font-family:Arial Black; font-size:12px; box-shadow:4px 4px 0 #000; }
.azul { background:#6FA8DC; }.branca { background:#FFFFFF; }.cinza { background:#8A8A8A; color:#fff; }
.card { border:3px solid #000; border-radius:12px; padding:12px; text-align:center; background:white; box-shadow:5px 5px 0 #000; }
</style>
<div class="wm"><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span><span>REFORMA DE FORNOS</span><span>REFORMA DE FORNOS</span></div>
<div class="top">🔥 REFORMA DE FORNOS 🔥</div>
""", unsafe_allow_html=True)

def carregar_seguro(caminho):
    if not os.path.exists(caminho): return []
    try:
        df=pd.read_csv(caminho).fillna("")
        df.columns=[str(c).upper().strip() for c in df.columns]
        # garante todas colunas
        for col in ["ID","DESCRICAO","MARCA","LOTE","FABRICACAO","TEMPO_VALIDADE","VALIDO_ATE","QTD_PALETE","ENTRADA","TOTAL","DATA_CADASTRO","ENTRADAS","SAIDAS","SALDO"]:
            if col not in df.columns: df[col]=""
        df["TOTAL"]=pd.to_numeric(df["TOTAL"], errors='coerce').fillna(0)
        return df.to_dict('records')
    except:
        try: os.remove(caminho)
        except: pass
        return []

if 'cad' not in st.session_state: st.session_state.cad=carregar_seguro(ARQ_CAD)
if 'mov' not in st.session_state: st.session_state.mov=carregar_seguro(ARQ_MOV)
if 'id_sel' not in st.session_state: st.session_state.id_sel=None

def calcular_valido_ate(fab_str, tempo_meses):
    try:
        fab=datetime.strptime(fab_str, "%d/%m/%Y")
        valido=fab + relativedelta(months=int(tempo_meses))
        return valido.strftime("%d/%m/%Y")
    except: return "00/00/0000"

def get_saldos_completos():
    saldos={}
    for r in st.session_state.get('cad',[]):
        lote=str(r.get('LOTE','')).strip()
        if not lote: continue
        if lote not in saldos:
            saldos[lote]=r.copy()
            saldos[lote]['ENTRADAS']=float(r.get('TOTAL',0) or 0)
            saldos[lote]['SAIDAS']=0
            saldos[lote]['SALDO']=float(r.get('TOTAL',0) or 0)
        else:
            saldos[lote]['ENTRADAS']=float(saldos[lote].get('ENTRADAS',0))+float(r.get('TOTAL',0) or 0)
            saldos[lote]['SALDO']=float(saldos[lote].get('SALDO',0))+float(r.get('TOTAL',0) or 0)
    for m in st.session_state.get('mov',[]):
        lote=str(m.get('LOTE','')).strip()
        if lote in saldos:
            try:
                qtd=float(m.get('QTD',0) or 0)
                if str(m.get('TIPO','')).upper()=="ENTRADA":
                    saldos[lote]['ENTRADAS']=float(saldos[lote].get('ENTRADAS',0))+qtd
                    saldos[lote]['SALDO']=float(saldos[lote].get('SALDO',0))+qtd
                else:
                    saldos[lote]['SAIDAS']=float(saldos[lote].get('SAIDAS',0))+qtd
                    saldos[lote]['SALDO']=float(saldos[lote].get('SALDO',0))-qtd
            except: pass
    return saldos

st.markdown("<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00; font-family:Arial Black;'>🔥 REFORMA DE FORNOS - CONTROLE COMPLETO REFRATÁRIOS 🔥</h1>", unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5=st.tabs(["📝 CADASTRO COMPLETO","🔄 ENTRADA/SAIDA","📦 ESTOQUE COMPLETO COM TODAS INFOS","📊 LOTES DO PRODUTO - BARRAS VALIDADE","📈 GRAFICOS"])

with tab1:
    st.markdown("#### CADASTRO COM DATA FABRICAÇÃO, TEMPO VALIDADE, VÁLIDO ATÉ")
    with st.form("cad", clear_on_submit=True):
        c1,c2,c3,c4=st.columns(4)
        with c1:
            id_in=st.text_input("ID*","1")
            desc_in=st.text_input("DESCRIÇÃO*","CIMENTO FONDU")
            marca_in=st.text_input("MARCA*","FONDU")
            lote_in=st.text_input("LOTE*","999999999")
        with c2:
            fab_in=st.date_input("DATA FABRICAÇÃO*", value=date.today())
            tempo_in=st.number_input("TEMPO VALIDADE (MESES)*", value=12, min_value=1, max_value=60)
            qtd_in=st.number_input("QTD/PALETE", value=1250.0)
            ent_in=st.number_input("ENTRADA PALETES", value=11.0)
        with c3:
            st.info(f"VÁLIDO ATÉ será calculado automaticamente")
            unidade_in=st.text_input("UNIDADE","KG")
            local_in=st.text_input("LOCAL FORNO","FORNO 1")
            obs_in=st.text_input("OBS","REFORMA")
        with c4:
            total_prev=float(qtd_in)*float(ent_in)
            st.metric("TOTAL CALCULADO", f"{total_prev:,.0f} KG")
            data_cad=date.today()
            st.write(f"DATA CADASTRO: {data_cad.strftime('%d/%m/%Y')}")
        if st.form_submit_button("💾 CADASTRAR PRODUTO COMPLETO", type="primary", use_container_width=True):
            fab_str=fab_in.strftime("%d/%m/%Y")
            valido_ate=calcular_valido_ate(fab_str, tempo_in)
            total=float(qtd_in)*float(ent_in)
            st.session_state.cad.append({
                "ID":str(id_in).strip(),"DESCRICAO":str(desc_in).upper().strip(),"MARCA":str(marca_in).upper().strip(),
                "LOTE":str(lote_in).strip(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(tempo_in),"VALIDO_ATE":valido_ate,
                "QTD_PALETE":float(qtd_in),"ENTRADA":float(ent_in),"TOTAL":float(total),
                "UNIDADE":unidade_in,"LOCAL":local_in,"OBS":obs_in,"DATA_CADASTRO":data_cad.strftime("%d/%m/%Y")
            })
            pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
            st.success(f"✅ LOTE {lote_in} | FAB {fab_str} | VALIDO ATÉ {valido_ate} | TOTAL {total:.0f}"); st.rerun()

with tab2:
    st.markdown("### 🔄 MOVIMENTAÇÃO - ENTRADA E SAÍDA DE MATERIAL")
    if not st.session_state.get('cad'): st.warning("Cadastre primeiro")
    else:
        c1,c2,c3,c4=st.columns(4)
        with c1: lote_mov=st.selectbox("LOTE*", options=[str(r.get('LOTE','')) for r in st.session_state.cad if r.get('LOTE')])
        with c2: tipo_mov=st.selectbox("TIPO MOVIMENTAÇÃO*", ["SAIDA","ENTRADA"])
        with c3: qtd_mov=st.number_input("QTD KG*", value=100.0, min_value=1.0)
        with c4: motivo=st.text_input("MOTIVO","REFORMA FORNO 2 - CONSUMO")
        if st.button("✅ REGISTRAR ENTRADA/SAIDA", type="primary", use_container_width=True):
            st.session_state.mov.append({"LOTE":str(lote_mov),"TIPO":tipo_mov,"QTD":float(qtd_mov),"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now().strftime("%H:%M")})
            pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
            st.success(f"{tipo_mov} {qtd_mov} KG LOTE {lote_mov}"); st.rerun()
        if st.session_state.get('mov'):
            st.markdown("#### HISTORICO MOVIMENTAÇÕES")
            st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

with tab3:
    st.markdown("### 📦 ESTOQUE COMPLETO - TODAS AS INFORMAÇÕES DO PRODUTO")
    if not st.session_state.get('cad'): st.warning("Sem cadastro")
    else:
        saldos=get_saldos_completos()
        total_geral=sum([float(v.get('SALDO',0) or 0) for v in saldos.values()])
        c1,c2,c3,c4=st.columns(4)
        c1.markdown(f"<div class='card'><h4>📦 SALDO TOTAL</h4><h2 style='color:#ff4e00;'>{total_geral:,.0f} KG</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='card'><h4>🔢 LOTES</h4><h2>{len(saldos)}</h2></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='card'><h4>📥 TOTAL ENTRADAS</h4><h2 style='color:green;'>{sum([float(v.get('ENTRADAS',0) or 0) for v in saldos.values()]):,.0f}</h2></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='card'><h4>📤 TOTAL SAIDAS</h4><h2 style='color:red;'>{sum([float(v.get('SAIDAS',0) or 0) for v in saldos.values()]):,.0f}</h2></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # TABELA COMPLETA COM TODAS AS INFOS
        html="""<table class="tabela"><tr>
        <th>ID</th><th>DESCRIÇÃO</th><th>MARCA</th><th>LOTE</th>
        <th>FABRICAÇÃO</th><th>TEMPO VALIDADE</th><th>VÁLIDO ATÉ</th>
        <th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL INICIAL</th>
        <th>ENTRADAS</th><th>SAÍDAS</th><th>SALDO ATUAL</th><th>DATA CADASTRO</th><th>STATUS</th></tr>"""
        for lote,r in saldos.items():
            saldo=float(r.get('SALDO',0) or 0)
            html+=f"""<tr>
            <td><b>{r.get('ID','')}</b></td><td>{r.get('DESCRICAO','')}</td><td>{r.get('MARCA','')}</td><td class='lote'>{lote}</td>
            <td class='fab'><b>{r.get('FABRICACAO','')}</b></td><td><b>{r.get('TEMPO_VALIDADE','')} MESES</b></td><td class='val'><b>{r.get('VALIDO_ATE','')}</b></td>
            <td>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td><b>{float(r.get('TOTAL',0) or 0):,.0f}</b></td>
            <td style='background:#a0ffa0;'><b>{float(r.get('ENTRADAS',0) or 0):,.0f}</b></td>
            <td style='background:#ffb0b0;'><b>{float(r.get('SAIDAS',0) or 0):,.0f}</b></td>
            <td class={'saldo�' if saldo>0 else 'saldo-zero'}><b>{saldo:,.0f}</b></td>
            <td>{r.get('DATA_CADASTRO','')}</td>
            <td class={'saldo-pos' if saldo>0 else 'saldo-zero'}><b>{'✅ OK' if saldo>0 else '⛔ ZERADO'}</b></td></tr>"""
        html+="</table>"
        st.markdown(html, unsafe_allow_html=True)

with tab4:
    st.markdown("### 📊 TODOS OS LOTES DO PRODUTO - GRAFICO DE BARRAS VALIDADE")
    if not st.session_state.get('cad'): st.warning("Cadastre")
    else:
        mapa={}
        for r in st.session_state.cad:
            idk=str(r.get('ID','?')).strip()
            if idk not in mapa: mapa[idk]={"ID":idk,"DESCRICAO":r.get('DESCRICAO',''),"QTD":0}
            mapa[idk]["QTD"]+=1
        cols=st.columns(4)
        for idx,(idk,info) in enumerate(mapa.items()):
            with cols[idx%4]:
                if st.button(f"ID {info['ID']} - {info['DESCRICAO']} ({info['QTD']} LOTES)", key=f"ver_{idk}_{idx}", use_container_width=True, type="primary"):
                    st.session_state.id_sel=idk
        if st.session_state.get('id_sel'):
            id_sel=str(st.session_state.id_sel)
            lotes=[r for r in st.session_state.cad if str(r.get('ID'))==id_sel]
            saldos=get_saldos_completos()
            st.success(f"PRODUTO ID {id_sel} - {lotes[0].get('DESCRICAO')} - {len(lotes)} LOTES")

            # TABELA COMPLETA DO PRODUTO
            html="""<table class="tabela"><tr><th>LOTE</th><th>FABRICAÇÃO</th><th>TEMPO</th><th>VÁLIDO ATÉ</th><th>TOTAL</th><th>ENTRADAS</th><th>SAÍDAS</th><th>SALDO</th></tr>"""
            for r in sorted(lotes, key=lambda x: str(x.get('LOTE',''))):
                lote=str(r.get('LOTE',''))
                s=saldos.get(lote,{})
                html+=f"<tr><td class='lote'>{lote}</td><td class='fab'>{r.get('FABRICACAO','')}</td><td>{r.get('TEMPO_VALIDADE','')}M</td><td class='val'><b>{r.get('VALIDO_ATE','')}</b></td><td>{float(r.get('TOTAL',0) or 0):,.0f}</td><td style='background:#a0ffa0;'>{float(s.get('ENTRADAS',0) or 0):,.0f}</td><td style='background:#ffb0b0;'>{float(s.get('SAIDAS',0) or 0):,.0f}</td><td style='background:#7fff7f;'><b>{float(s.get('SALDO',0) or 0):,.0f}</b></td></tr>"
            html+="</table>"
            st.markdown(html, unsafe_allow_html=True)

            # GRAFICO DE BARRAS VALIDADE FORMATO FOTO
            st.markdown('<div style="background:#000; color:#fff; padding:8px; text-align:center; font-family:Arial Black; margin-top:20px; border:3px solid #00ff66;">📊 GRAFICO DE BARRAS - VALIDADE - FUNDO VERDE FORMATO FOTO</div><div class="fundo-verde">', unsafe_allow_html=True)
            max_t=max([float(r.get('TOTAL',0) or 0) for r in lotes]) or 1
            for i,r in enumerate(sorted(lotes, key=lambda x: str(x.get('LOTE','')))):
                prop=30+(float(r.get('TOTAL',0) or 0)/max_t*65)
                cor=["azul","branca","cinza","branca"][i%4]
                st.markdown(f'<div class="barra {cor}" style="width:{prop:.1f}%;">LOTE {r.get("LOTE")} | FAB {r.get("FABRICACAO")} | VALIDO ATÉ {r.get("VALIDO_ATE")} | {float(r.get("TOTAL",0) or 0):,.0f} KG</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # GRAFICO PLOTLY BARRAS VALIDADE
            try:
                dfp=pd.DataFrame(lotes)
                if "TOTAL" in dfp.columns:
                    dfp["TOTAL_NUM"]=pd.to_numeric(dfp["TOTAL"], errors='coerce').fillna(0)
                    fig=go.Figure(go.Bar(x=dfp["TOTAL_NUM"], y=[f"LOTE {l} - VAL {v}" for l,v in zip(dfp["LOTE"].astype(str), dfp["VALIDO_ATE"].astype(str))], orientation='h', marker=dict(color=["#6FA8DC","#FFFFFF","#8A8A8A","#EFEFEF"]*10, line=dict(color='black',width=2)), text=[f"{x:,.0f} KG" for x in dfp["TOTAL_NUM"]], textposition='outside'))
                    fig.update_layout(plot_bgcolor='#A8C5A2', paper_bgcolor='#A8C5A2', height=350+len(dfp)*50, title=f"GRAFICO BARRAS VALIDADE - ID {id_sel}")
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Grafico erro: {e}")

with tab5:
    st.markdown("### 📈 GRAFICOS GERAIS")
    if not st.session_state.get('cad'): st.warning("Sem dados")
    else:
        try:
            df=pd.DataFrame(st.session_state.cad)
            if "TOTAL" in df.columns:
                df["TOTAL_NUM"]=pd.to_numeric(df["TOTAL"], errors='coerce').fillna(0)
                c1,c2=st.columns(2)
                with c1:
                    fig1=px.bar(df, x='DESCRICAO', y='TOTAL_NUM', color='ID', title="ESTOQUE POR PRODUTO")
                    st.plotly_chart(fig1, use_container_width=True)
                with c2:
                    fig2=px.pie(df, values='TOTAL_NUM', names='DESCRICAO', title="DISTRIBUIÇÃO")
                    st.plotly_chart(fig2, use_container_width=True)
                fig3=px.bar(df, x='LOTE', y='TOTAL_NUM', color='VALIDO_ATE', title="LOTES X VÁLIDO ATÉ - BARRAS")
                fig3.update_layout(plot_bgcolor='#A8C5A2')
                st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"Erro graficos: {e}")
