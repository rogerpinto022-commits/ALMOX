import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"

st.markdown("""
<style>
.block-container { z-index:2; position:relative; }
.wm { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; opacity:0.11; pointer-events:none; display:flex; flex-wrap:wrap; gap:80px; justify-content:center; align-content:center; }
.wm span { font-size:30px; font-weight:900; color:#ff4e00; transform:rotate(-30deg); border:3px solid #ff4e00; padding:8px 14px; border-radius:10px; }
.top { position:fixed; top:10px; right:15px; z-index:9999; background:linear-gradient(90deg,#ff4e00,#ff0000); color:#fff; font-weight:900; padding:6px 16px; border-radius:20px; border:2px solid #000; }
.tabela { width:100%; border-collapse:collapse; font-size:13px; }
.tabela th { background:#1a252f; color:#fff; padding:11px 6px; border:2px solid #000; text-align:center; font-family:Arial Black; }
.tabela td { padding:9px 5px; border:1.5px solid #000; text-align:center; background:#fff; color:#000; font-weight:700; }
.lote { background:#00ff66!important; font-size:15px; border:3px solid #000!important; }
.fundo-verde { background:#A8C5A2; border-left:6px solid #000; padding:25px 10px 25px 0; margin:15px 0; border:3px solid #000; }
.barra { height:54px; margin:18px 0; border:2.5px solid #000; display:flex; align-items:center; padding-left:14px; font-family:Arial Black; font-size:13px; box-shadow:4px 4px 0 #000; }
.azul { background:#6FA8DC; }
.branca { background:#FFFFFF; }
.cinza { background:#8A8A8A; color:#fff; }
.card { border:3px solid #000; border-radius:12px; padding:15px; text-align:center; background:white; box-shadow:5px 5px 0 #000; }
</style>
<div class="wm"><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span><span>REFORMA DE FORNOS</span></div>
<div class="top">🔥 REFORMA DE FORNOS 🔥</div>
""", unsafe_allow_html=True)

def carregar_seguro(caminho):
    if not os.path.exists(caminho): return []
    try:
        df = pd.read_csv(caminho)
        # CORRIGE COLUNAS - CRIA TOTAL SE NÃO EXISTIR
        df.columns = [str(c).upper().strip() for c in df.columns]
        # normaliza nomes parecidos
        col_map = {}
        for c in df.columns:
            if "DESCRI" in c: col_map[c]="DESCRICAO"
            if "QTD" in c and "PAL" in c: col_map[c]="QTD_PALETE"
            if c=="TOTAL" or "TOTAL" in c: col_map[c]="TOTAL"
        df = df.rename(columns=col_map)
        if "TOTAL" not in df.columns:
            if "QTD_PALETE" in df.columns and "ENTRADA" in df.columns:
                df["TOTAL"] = pd.to_numeric(df["QTD_PALETE"], errors='coerce').fillna(0) * pd.to_numeric(df["ENTRADA"], errors='coerce').fillna(0)
            else:
                df["TOTAL"] = 0
        if "QTD_PALETE" not in df.columns: df["QTD_PALETE"]=1250
        if "ENTRADA" not in df.columns: df["ENTRADA"]=1
        if "LOTE" not in df.columns: df["LOTE"]="SEM LOTE"
        if "VALIDADE" not in df.columns: df["VALIDADE"]="00/00/0000"
        if "ID" not in df.columns: df["ID"]="1"
        if "DESCRICAO" not in df.columns: df["DESCRICAO"]="PRODUTO"
        df["TOTAL"] = pd.to_numeric(df["TOTAL"], errors='coerce').fillna(0)
        return df.fillna("").to_dict('records')
    except Exception as e:
        try: os.remove(caminho)
        except: pass
        return []

# INICIALIZAÇAO BLINDADA
if 'cad' not in st.session_state: st.session_state.cad = carregar_seguro(ARQ_CAD)
if 'mov' not in st.session_state: st.session_state.mov = carregar_seguro(ARQ_MOV)
if 'id_sel' not in st.session_state: st.session_state.id_sel = None

def garantir_total(df):
    """PERICIA: garante que df tem TOTAL_NUM sem KeyError"""
    if df.empty: return df
    if "TOTAL" in df.columns:
        df["TOTAL_NUM"] = pd.to_numeric(df["TOTAL"], errors='coerce').fillna(0)
    elif "QTD_PALETE" in df.columns and "ENTRADA" in df.columns:
        df["TOTAL_NUM"] = pd.to_numeric(df["QTD_PALETE"], errors='coerce').fillna(0) * pd.to_numeric(df["ENTRADA"], errors='coerce').fillna(0)
    else:
        df["TOTAL_NUM"] = 0
    return df

def get_saldos():
    saldos={}
    for r in st.session_state.get('cad',[]):
        lote=str(r.get('LOTE','')).strip()
        if not lote: continue
        if lote not in saldos: saldos[lote]=r.copy()
        else:
            try: saldos[lote]['TOTAL']=float(saldos[lote].get('TOTAL',0) or 0)+float(r.get('TOTAL',0) or 0)
            except: pass
    for m in st.session_state.get('mov',[]):
        lote=str(m.get('LOTE','')).strip()
        if lote in saldos:
            try:
                if str(m.get('TIPO','')).upper()=="ENTRADA": saldos[lote]['TOTAL']=float(saldos[lote].get('TOTAL',0) or 0)+float(m.get('QTD',0) or 0)
                else: saldos[lote]['TOTAL']=float(saldos[lote].get('TOTAL',0) or 0)-float(m.get('QTD',0) or 0)
            except: pass
    return saldos

st.markdown("<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00; font-family:Arial Black;'>🔥 REFORMA DE FORNOS - ALMOXARIFADO COMPLETO 🔥</h1>", unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5 = st.tabs(["📝 CADASTRO","🔄 ENTRADA/SAIDA","📦 SALDO ESTOQUE","📊 LOTES DO PRODUTO - BARRAS VALIDADE","📈 GRAFICOS"])

with tab1:
    with st.form("cad_form", clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1: id_in=st.text_input("ID*","1"); desc_in=st.text_input("DESCRIÇÃO*","CIMENTO FONDU"); marca_in=st.text_input("MARCA","FONDU")
        with c2: lote_in=st.text_input("LOTE*","999999999"); val_in=st.text_input("VALIDADE","00/00/0000"); qtd_in=st.number_input("QTD/PALETE",value=1250.0)
        with c3: ent_in=st.number_input("ENTRADA PALETES",value=11.0); data_in=st.date_input("DATA",value=date.today())
        if st.form_submit_button("💾 CADASTRAR", type="primary", use_container_width=True):
            total=float(qtd_in)*float(ent_in)
            st.session_state.cad.append({"ID":str(id_in).strip(),"DESCRICAO":str(desc_in).upper().strip(),"MARCA":str(marca_in).upper().strip(),"LOTE":str(lote_in).strip(),"VALIDADE":str(val_in).strip(),"QTD_PALETE":float(qtd_in),"ENTRADA":float(ent_in),"TOTAL":float(total),"DATA":data_in.strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False)
            st.success("CADASTRADO!"); st.rerun()

with tab2:
    st.markdown("### 🔄 ENTRADA E SAÍDA")
    if not st.session_state.get('cad'): st.warning("Cadastre")
    else:
        c1,c2,c3,c4=st.columns(4)
        with c1: lote_mov=st.selectbox("LOTE", options=[str(r.get('LOTE','')) for r in st.session_state.cad if r.get('LOTE')])
        with c2: tipo_mov=st.selectbox("TIPO", ["SAIDA","ENTRADA"])
        with c3: qtd_mov=st.number_input("QTD KG", value=100.0)
        with c4: obs_mov=st.text_input("OBS","REFORMA FORNO")
        if st.button("✅ REGISTRAR", type="primary", use_container_width=True):
            st.session_state.mov.append({"LOTE":str(lote_mov),"TIPO":tipo_mov,"QTD":float(qtd_mov),"OBS":obs_mov,"DATA":date.today().strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False)
            st.success("Registrado!"); st.rerun()
        if st.session_state.get('mov'):
            st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

with tab3:
    st.markdown("### 📦 SALDO EM ESTOQUE")
    if not st.session_state.get('cad'): st.warning("Sem cadastro")
    else:
        saldos=get_saldos()
        total_geral=sum([float(v.get('TOTAL',0) or 0) for v in saldos.values()])
        c1,c2,c3=st.columns(3)
        c1.markdown(f"<div class='card'><h3>📦 TOTAL</h3><h1 style='color:#ff4e00;'>{total_geral:,.0f} KG</h1></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='card'><h3>🔢 LOTES</h3><h1>{len(saldos)}</h1></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='card'><h3>📝 PRODUTOS</h3><h1>{len(set([str(r.get('ID')) for r in st.session_state.cad]))}</h1></div>", unsafe_allow_html=True)
        html='<table class="tabela" style="margin-top:20px;"><tr><th>ID</th><th>DESCRIÇÃO</th><th>LOTE</th><th>VALIDADE</th><th>SALDO ATUAL</th><th>STATUS</th></tr>'
        for lote,r in saldos.items():
            saldo=float(r.get('TOTAL',0) or 0)
            html+=f"<tr><td><b>{r.get('ID','')}</b></td><td>{r.get('DESCRICAO','')}</td><td class='lote'>{lote}</td><td style='background:yellow;'><b>{r.get('VALIDADE','')}</b></td><td style='background:#7fff7f;'><b>{saldo:,.0f}</b></td><td>{'✅ OK' if saldo>0 else '⛔ ZERADO'}</td></tr>"
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)

with tab4:
    st.markdown("### 📊 CLIQUE NO PRODUTO - TODOS LOTES - GRAFICO DE BARRAS VALIDADE")
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
            if lotes:
                st.success(f"ID {id_sel} - {lotes[0].get('DESCRICAO')} - {len(lotes)} LOTES")
                # Grafico foto verde
                st.markdown('<div style="background:#000; color:#fff; padding:8px; text-align:center; font-family:Arial Black; border:3px solid #00ff66;">📊 GRAFICO DE BARRAS - VALIDADE - FORMATO FOTO VERDE</div><div class="fundo-verde">', unsafe_allow_html=True)
                max_t=max([float(r.get('TOTAL',0) or 0) for r in lotes]) or 1
                for i,r in enumerate(sorted(lotes, key=lambda x: str(x.get('LOTE','')))):
                    prop=30+(float(r.get('TOTAL',0) or 0)/max_t*65)
                    cor=["azul","branca","cinza","branca"][i%4]
                    st.markdown(f'<div class="barra {cor}" style="width:{prop:.1f}%;">LOTE {r.get("LOTE")} | VALIDADE {r.get("VALIDADE")} | {float(r.get("TOTAL",0) or 0):,.0f} KG</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Plotly barras validade - BLINDADO
                try:
                    dfp=pd.DataFrame(lotes)
                    dfp=garantir_total(dfp)
                    if not dfp.empty and "TOTAL_NUM" in dfp.columns:
                        fig=go.Figure(go.Bar(x=dfp["TOTAL_NUM"], y=[f"LOTE {l} VAL {v}" for l,v in zip(dfp["LOTE"].astype(str), dfp["VALIDADE"].astype(str))], orientation='h', marker=dict(color=["#6FA8DC","#FFFFFF","#8A8A8A","#EFEFEF"]*10, line=dict(color='black',width=2)), text=[f"{x:,.0f}" for x in dfp["TOTAL_NUM"]], textposition='outside'))
                        fig.update_layout(plot_bgcolor='#A8C5A2', paper_bgcolor='#A8C5A2', height=300+len(dfp)*45, xaxis=dict(showgrid=False,showticklabels=False), yaxis=dict(linecolor='black',linewidth=3), title=f"VALIDADE BARRAS - ID {id_sel}")
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Grafico plotly erro: {e}")
                    st.dataframe(pd.DataFrame(lotes))

with tab5:
    st.markdown("### 📈 GRAFICOS GERAIS")
    if not st.session_state.get('cad'):
        st.warning("Sem dados")
    else:
        try:
            df=pd.DataFrame(st.session_state.cad)
            df=garantir_total(df)
            if df.empty or "TOTAL_NUM" not in df.columns:
                st.warning("Sem dados para grafico")
            else:
                c1,c2=st.columns(2)
                with c1:
                    if "DESCRICAO" in df.columns:
                        fig1=px.bar(df, x='DESCRICAO', y='TOTAL_NUM', color='ID', title="ESTOQUE POR PRODUTO")
                        st.plotly_chart(fig1, use_container_width=True)
                with c2:
                    if "DESCRICAO" in df.columns:
                        fig2=px.pie(df, values='TOTAL_NUM', names='DESCRICAO', title="DISTRIBUIÇÃO ESTOQUE")
                        st.plotly_chart(fig2, use_container_width=True)
                if "LOTE" in df.columns:
                    fig3=px.bar(df, x='LOTE', y='TOTAL_NUM', color='VALIDADE', title="GRAFICO BARRAS - LOTES X VALIDADE")
                    fig3.update_layout(plot_bgcolor='#A8C5A2')
                    st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"Erro graficos: {e}")
            st.dataframe(pd.DataFrame(st.session_state.cad))
