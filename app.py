import streamlit as st
import pandas as pd
from datetime import date
import plotly.graph_objects as go
import os

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao_refratario.csv"

# MARCA D'ÁGUA
st.markdown("""
<style>
.watermark-container { position: fixed; top:0; left:0; width:100%; height:100%; z-index:0; pointer-events:none; display:flex; flex-wrap:wrap; justify-content:center; align-content:center; gap:90px; opacity:0.13; }
.watermark-item { font-size:28px; font-weight:900; color:#ff4e00; transform:rotate(-30deg); border:3px solid #ff4e00; padding:6px 14px; border-radius:8px; }
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
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATARIOS</div>
</div>
<div class="watermark-top">🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</div>
""", unsafe_allow_html=True)

def carregar():
    c=[]
    if os.path.exists(ARQ_CAD):
        try: c=pd.read_csv(ARQ_CAD).to_dict('records')
        except: pass
    return c

if 'iniciado' not in st.session_state:
    st.session_state.cadastro=carregar()
    st.session_state.iniciado=True
    st.session_state.mostrar_tabela=False
    st.session_state.produto_clicado=None

st.title("🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS")

tab1,tab2,tab3 = st.tabs(["📝 CADASTRO","📦 TABELA PADRÃO FOTO","📊 GRÁFICO FORMATO DA FOTO"])

with tab1:
    with st.form("cad",clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1: id_p=st.text_input("ID","1"); desc=st.text_input("DESCRIÇÃO","CIMENTO"); marca=st.text_input("MARCA","FONDU")
        with c2: lote=st.text_input("LOTE","99999999999"); validade=st.text_input("VALIDADE","00/00/0000"); qtd_pal=st.number_input("QTD/PALETE",value=1250)
        with c3: entrada=st.number_input("ENTRADA",value=11); unidade=st.text_input("UNIDADE","KILOS"); data=st.date_input("DATA",value=date.today())
        if st.form_submit_button("💾 SALVAR",type="primary"):
            total=qtd_pal*entrada
            st.session_state.cadastro.append({"ID":id_p,"DESCRIÇÃO":desc.upper(),"MARCA":marca.upper(),"LOTE":lote,"VALIDADE":validade,"QTD/PALETE":qtd_pal,"ENTRADA":entrada,"TOTAL":total,"IDADE":unidade,"DATA":data.strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.rerun()

with tab2:
    if st.session_state.cadastro:
        df=pd.DataFrame(st.session_state.cadastro)
        if st.button("👁️ VER TABELA COMPLETA" if not st.session_state.mostrar_tabela else "🙈 ESCONDER", type="primary"):
            st.session_state.mostrar_tabela=not st.session_state.mostrar_tabela; st.rerun()
        if st.session_state.mostrar_tabela:
            html='<table class="tabela-ref"><tr><th>ID</th><th>DESCRIÇÃO</th><th>MARCA</th><th>LOTE</th><th>VALIDADE</th><th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL</th><th>IDADE DE MEDI</th><th>DATA</th></tr>'
            for _,r in df.iterrows():
                html+=f"<tr><td>{r['ID']}</td><td>{r['DESCRIÇÃO']}</td><td>{r['MARCA']}</td><td class='lote-verde'>{r['LOTE']}</td><td>{r['VALIDADE']}</td><td class='qtd-cinza'>{r['QTD/PALETE']}</td><td>{r['ENTRADA']}</td><td>{r['TOTAL']}</td><td>{r['IDADE']}</td><td>{r['DATA']}</td></tr>"
            html+='</table>'
            st.markdown(html,unsafe_allow_html=True)

with tab3:
    st.markdown("### Clique no produto para ver a validade no formato da sua foto")
    if not st.session_state.cadastro:
        st.warning("Cadastre primeiro")
    else:
        df=pd.DataFrame(st.session_state.cadastro)
        # LISTA DE PRODUTOS CLICÁVEIS
        st.write("**PRODUTOS CADASTRADOS - CLIQUE:**")
        cols=st.columns(4)
        for i, (idx,row) in enumerate(df.iterrows()):
            with cols[i%4]:
                if st.button(f"{row['ID']} - {row['DESCRIÇÃO']}\nL:{row['LOTE']}", key=f"prod_{idx}_{row['LOTE']}", use_container_width=True):
                    st.session_state.produto_clicado = row.to_dict()
        
        # GRÁFICO NO FORMATO DA SUA FOTO - SÓ APARECE QUANDO CLICA
        if st.session_state.produto_clicado:
            p=st.session_state.produto_clicado
            st.success(f"Selecionado: {p['DESCRIÇÃO']} - {p['MARCA']} - LOTE {p['LOTE']}")
            
            # DADOS PARA GRÁFICO FORMATO DA FOTO (4 barras)
            lotes_relacionados = df[df['ID']==p['ID']] if 'ID' in df else df
            if len(lotes_relacionados) > 4: lotes_relacionados = lotes_relacionados.head(4)
            
            # Se só tem 1 produto, cria 4 barras de exemplo com validade
            if len(lotes_relacionados)==1:
                labels = [f"LOTE {p['LOTE']}", "VALIDADE", "DIAS", "TOTAL"]
                valores = [int(p['TOTAL']), int(p['QTD/PALETE']), int(p['ENTRADA'])*10, int(p['TOTAL'])*0.3]
            else:
                labels = lotes_relacionados['LOTE'].astype(str).tolist()
                valores = lotes_relacionados['TOTAL'].astype(float).tolist()

            # CORES IGUAIS DA SUA FOTO: azul, branco, cinza, branco
            cores = ["#6FA8DC", "#FFFFFF", "#808080", "#FFFFFF", "#6FA8DC", "#FFFFFF"]
            cores = cores[:len(labels)]

            fig = go.Figure(go.Bar(
                x=valores,
                y=labels,
                orientation='h',
                marker=dict(color=cores, line=dict(color='black', width=1)),
                text=[f"{v:,.0f}" for v in valores],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Qtd: %{x}<br>Val: '+str(p['VALIDADE'])+'<extra></extra>'
            ))

            fig.update_layout(
                plot_bgcolor='#A8D5A2',  # FUNDO VERDE IGUAL SUA FOTO
                paper_bgcolor='#A8D5A2',
                title=f"VALIDADE - {p['DESCRIÇÃO']} | LOTE {p['LOTE']} | VAL: {p['VALIDADE']}",
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, linecolor='black', linewidth=2),
                height=350,
                margin=dict(l=120, r=50, t=50, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"🔵 Azul = Total {p['TOTAL']} | ⚪ Branco = QTD/Palete {p['QTD/PALETE']} | ⚫ Cinza = Entrada {p['ENTRADA']} | Validade {p['VALIDADE']}")
        else:
            st.info("👆 Clique em um produto acima para gerar o gráfico no formato verde com barras azul/branco/cinza")
