import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go
import os

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"

st.markdown("""
<style>
.watermark-container { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; pointer-events:none; display:flex; flex-wrap:wrap; justify-content:center; align-content:center; gap:90px; opacity:0.13; }
.watermark-item { font-size:26px; font-weight:900; color:#ff4e00; transform:rotate(-30deg); border:3px solid #ff4e00; padding:6px 14px; border-radius:8px; }
.watermark-top { position:fixed; top:8px; right:18px; font-size:12px; font-weight:900; color:#fff; z-index:9999; pointer-events:none; background:linear-gradient(90deg,#ff4e00,#ff0000); padding:6px 14px; border-radius:20px; border:2px solid #000; }
.block-container { position:relative; z-index:1; }
.tabela-ref { width:100%; border-collapse:collapse; font-size:13px; }
.tabela-ref th { background:#2f3d4a; color:white; padding:8px; border:1px solid #000; text-align:center; }
.tabela-ref td { padding:6px; border:1px solid #999; text-align:center; background:white; }
.lote-verde { background:#7fff7f!important; font-weight:900; }
.qtd-cinza { background:#e0e0e0!important; }
</style>
<div class="watermark-container">
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
</div>
<div class="watermark-top">🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</div>
""", unsafe_allow_html=True)

def carregar():
    lista=[]
    if os.path.exists(ARQ_CAD):
        try:
            df=pd.read_csv(ARQ_CAD)
            # NORMALIZA COLUNAS - REMOVE ACENTO E DEIXA MAIUSCULO
            df.columns=[c.upper().replace("Ç","C").replace("Ã","A").replace("Á","A") for c in df.columns]
            # Renomeia para padrão
            mapa={"DESCRICAO":"DESCRICAO","MARCA":"MARCA","LOTE":"LOTE","VALIDADE":"VALIDADE","QTD/PALETE":"QTD_PALETE","QTD_PALETE":"QTD_PALETE","ENTRADA":"ENTRADA","TOTAL":"TOTAL","IDADE":"UNIDADE","UNIDADE":"UNIDADE","DATA":"DATA","ID":"ID"}
            df.rename(columns=mapa, inplace=True)
            lista=df.to_dict('records')
        except Exception as e:
            st.error(f"Erro ao carregar CSV: {e}")
    return lista

if 'iniciado' not in st.session_state:
    st.session_state.cadastro=carregar()
    st.session_state.iniciado=True
    st.session_state.mostrar_tabela=False
    st.session_state.produto_clicado=None

st.title("🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS")
tab1,tab2,tab3 = st.tabs(["📝 CADASTRO","📦 TABELA PADRÃO FOTO","📊 GRÁFICO FORMATO FOTO"])

with tab1:
    with st.form("cad",clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1: id_p=st.text_input("ID","1"); desc=st.text_input("DESCRICAO","CIMENTO"); marca=st.text_input("MARCA","FONDU")
        with c2: lote=st.text_input("LOTE","99999999999"); validade=st.text_input("VALIDADE","00/00/0000"); qtd_pal=st.number_input("QTD/PALETE",value=1250)
        with c3: entrada=st.number_input("ENTRADA",value=11); unidade=st.text_input("UNIDADE","KILOS"); data=st.date_input("DATA",value=date.today())
        if st.form_submit_button("💾 SALVAR",type="primary"):
            total=qtd_pal*entrada
            # SALVA SEMPRE SEM ACENTO PARA NAO QUEBRAR
            st.session_state.cadastro.append({"ID":str(id_p),"DESCRICAO":desc.upper(),"MARCA":marca.upper(),"LOTE":str(lote),"VALIDADE":validade,"QTD_PALETE":qtd_pal,"ENTRADA":entrada,"TOTAL":total,"UNIDADE":unidade,"DATA":data.strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.rerun()

with tab2:
    if not st.session_state.cadastro:
        st.info("Sem dados")
    else:
        df=pd.DataFrame(st.session_state.cadastro)
        if st.button("👁️ VER TABELA COMPLETA" if not st.session_state.mostrar_tabela else "🙈 ESCONDER", type="primary"):
            st.session_state.mostrar_tabela=not st.session_state.mostrar_tabela; st.rerun()
        if st.session_state.mostrar_tabela:
            html='<table class="tabela-ref"><tr><th>ID</th><th>DESCRIÇÃO</th><th>MARCA</th><th>LOTE</th><th>VALIDADE</th><th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL</th><th>IDADE DE MEDI</th><th>DATA</th></tr>'
            for r in st.session_state.cadastro:
                # usa.get para nunca dar KeyError
                html+=f"<tr><td>{r.get('ID','')}</td><td>{r.get('DESCRICAO','')}</td><td>{r.get('MARCA','')}</td><td class='lote-verde'>{r.get('LOTE','')}</td><td>{r.get('VALIDADE','')}</td><td class='qtd-cinza'>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td>{r.get('TOTAL','')}</td><td>{r.get('UNIDADE','')}</td><td>{r.get('DATA','')}</td></tr>"
            html+='</table>'
            st.markdown(html,unsafe_allow_html=True)
            st.write("---")
            for idx in range(len(st.session_state.cadastro)-1,-1,-1):
                r=st.session_state.cadastro[idx]
                a,b=st.columns([4,1])
                a.write(f"{r.get('ID')} - {r.get('DESCRICAO')} - LOTE {r.get('LOTE')}")
                if b.button("🗑️ Excluir", key=f"del_{idx}_{r.get('LOTE','')}"):
                    st.session_state.cadastro.pop(idx)
                    if st.session_state.cadastro: pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False)
                    else:
                        if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
                    st.rerun()

with tab3:
    st.markdown("### Clique no produto para ver gráfico formato da sua foto (fundo verde)")
    if not st.session_state.cadastro:
        st.warning("Cadastre primeiro")
    else:
        cols=st.columns(3)
        for i, r in enumerate(st.session_state.cadastro):
            # BLINDADO - sem row['DESCRIÇÃO'], usa.get
            id_v = r.get('ID','?')
            desc_v = r.get('DESCRICAO','?')
            lote_v = r.get('LOTE','?')
            with cols[i%3]:
                if st.button(f"{id_v} - {desc_v}\nL:{lote_v}", key=f"prod_{i}_{lote_v}", use_container_width=True):
                    st.session_state.produto_clicado = r

        if st.session_state.produto_clicado:
            p=st.session_state.produto_clicado
            st.success(f"Selecionado: {p.get('DESCRICAO')} | {p.get('MARCA')} | LOTE {p.get('LOTE')} | VAL {p.get('VALIDADE')}")

            # GRAFICO NO FORMATO DA FOTO
            labels = [f"LOTE {p.get('LOTE')}", f"QTD/PAL {p.get('QTD_PALETE')}", f"ENTRADA {p.get('ENTRADA')}", f"TOTAL {p.get('TOTAL')}"]
            valores = [float(p.get('TOTAL',0)), float(p.get('QTD_PALETE',0))*10, float(p.get('ENTRADA',0))*100, float(p.get('TOTAL',0))*0.4]
            cores = ["#6FA8DC", "#FFFFFF", "#808080", "#FFFFFF"]

            fig = go.Figure(go.Bar(
                x=valores, y=labels, orientation='h',
                marker=dict(color=cores, line=dict(color='black', width=1)),
                text=[f"{v:,.0f}" for v in valores], textposition='outside'
            ))
            fig.update_layout(
                plot_bgcolor='#A8D5A2', paper_bgcolor='#A8D5A2',
                title=f"VALIDADE - {p.get('DESCRICAO')} | LOTE {p.get('LOTE')} | VALIDADE {p.get('VALIDADE')}",
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, linecolor='black', linewidth=2),
                height=350, margin=dict(l=150, r=40, t=60, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("👆 Clique em um produto acima")
