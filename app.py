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
            df.columns=[c.upper().replace("Ç","C").replace("Ã","A") for c in df.columns]
            lista=df.to_dict('records')
        except: pass
    return lista

if 'iniciado' not in st.session_state:
    st.session_state.cadastro=carregar()
    st.session_state.iniciado=True
    st.session_state.mostrar_tabela=False
    st.session_state.id_selecionado=None

st.title("🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS")
tab1,tab2,tab3 = st.tabs(["📝 CADASTRO","📦 TABELA","📊 LOTES POR PRODUTO"])

with tab1:
    with st.form("cad",clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1: id_p=st.text_input("ID","1"); desc=st.text_input("DESCRICAO","CIMENTO"); marca=st.text_input("MARCA","FONDU")
        with c2: lote=st.text_input("LOTE","99999999999"); validade=st.text_input("VALIDADE","00/00/0000"); qtd_pal=st.number_input("QTD/PALETE",value=1250)
        with c3: entrada=st.number_input("ENTRADA",value=11); unidade=st.text_input("UNIDADE","KILOS"); data=st.date_input("DATA",value=date.today())
        if st.form_submit_button("💾 SALVAR",type="primary"):
            total=qtd_pal*entrada
            st.session_state.cadastro.append({"ID":str(id_p).strip(),"DESCRICAO":desc.upper().strip(),"MARCA":marca.upper().strip(),"LOTE":str(lote).strip(),"VALIDADE":validade,"QTD_PALETE":qtd_pal,"ENTRADA":entrada,"TOTAL":total,"UNIDADE":unidade,"DATA":data.strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.rerun()

with tab2:
    if st.session_state.cadastro:
        if st.button("👁️ VER TABELA COMPLETA" if not st.session_state.mostrar_tabela else "🙈 ESCONDER", type="primary"):
            st.session_state.mostrar_tabela=not st.session_state.mostrar_tabela; st.rerun()
        if st.session_state.mostrar_tabela:
            html='<table class="tabela-ref"><tr><th>ID</th><th>DESCRIÇÃO</th><th>MARCA</th><th>LOTE</th><th>VALIDADE</th><th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL</th><th>UNIDADE</th><th>DATA</th></tr>'
            for r in st.session_state.cadastro:
                html+=f"<tr><td>{r.get('ID','')}</td><td>{r.get('DESCRICAO','')}</td><td>{r.get('MARCA','')}</td><td class='lote-verde'>{r.get('LOTE','')}</td><td>{r.get('VALIDADE','')}</td><td class='qtd-cinza'>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td>{r.get('TOTAL','')}</td><td>{r.get('UNIDADE','')}</td><td>{r.get('DATA','')}</td></tr>"
            html+='</table>'
            st.markdown(html,unsafe_allow_html=True)

# ===== ABA QUE VOCÊ QUER - TODOS LOTES DO PRODUTO =====
with tab3:
    st.markdown("### Clique no produto e veja TODOS OS LOTES dele")
    if not st.session_state.cadastro:
        st.warning("Cadastre primeiro")
    else:
        df=pd.DataFrame(st.session_state.cadastro)
        # LISTA ÚNICA DE PRODUTOS (ID + DESCRICAO)
        produtos_unicos = df.drop_duplicates(subset=['ID','DESCRICAO'])[['ID','DESCRICAO','MARCA']]

        st.write(f"**{len(produtos_unicos)} produtos cadastrados - CLIQUE PARA VER LOTES:**")
        cols=st.columns(3)
        for i, (_, row) in enumerate(produtos_unicos.iterrows()):
            id_prod = str(row['ID'])
            desc_prod = str(row['DESCRICAO'])
            marca_prod = str(row['MARCA'])
            qtd_lotes = len(df[df['ID']==id_prod])
            with cols[i%3]:
                if st.button(f"📦 ID {id_prod} - {desc_prod}\n{marca_prod} | {qtd_lotes} lotes", key=f"prod_{id_prod}_{i}", use_container_width=True):
                    st.session_state.id_selecionado = id_prod

        # MOSTRA TODOS OS LOTES DO PRODUTO SELECIONADO
        if st.session_state.id_selecionado:
            id_sel = st.session_state.id_selecionado
            df_filtrado = df[df['ID'].astype(str)==str(id_sel)].copy()

            if df_filtrado.empty:
                st.error("Nenhum lote para esse ID")
            else:
                desc_sel = df_filtrado.iloc[0].get('DESCRICAO','')
                st.success(f"### PRODUTO: ID {id_sel} - {desc_sel} | {len(df_filtrado)} LOTES CADASTRADOS")

                # TABELA DE TODOS OS LOTES DESSE PRODUTO
                html='<table class="tabela-ref"><tr><th>LOTE</th><th>MARCA</th><th>VALIDADE</th><th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL</th><th>DATA</th></tr>'
                for _, r in df_filtrado.iterrows():
                    html+=f"<tr><td class='lote-verde'>{r.get('LOTE','')}</td><td>{r.get('MARCA','')}</td><td>{r.get('VALIDADE','')}</td><td class='qtd-cinza'>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td>{r.get('TOTAL','')}</td><td>{r.get('DATA','')}</td></tr>"
                html+='</table>'
                st.markdown(html,unsafe_allow_html=True)

                # GRÁFICO FORMATO DA SUA FOTO - FUNDO VERDE - TODOS LOTES
                st.markdown("#### 📊 Gráfico no formato da foto - Todos lotes do produto")

                labels = df_filtrado['LOTE'].astype(str).tolist()
                valores = df_filtrado['TOTAL'].astype(float).tolist()

                # CORES ALTERNADAS IGUAL FOTO: azul, branco, cinza, branco...
                cores_base = ["#6FA8DC", "#FFFFFF", "#808080", "#EFEFEF"]
                cores = [cores_base[i % len(cores_base)] for i in range(len(labels))]

                fig = go.Figure(go.Bar(
                    x=valores,
                    y=[f"LOTE {l} | VAL {v}" for l, v in zip(df_filtrado['LOTE'], df_filtrado['VALIDADE'])],
                    orientation='h',
                    marker=dict(color=cores, line=dict(color='black', width=1.5)),
                    text=[f"{v:,.0f} | L:{l}" for v, l in zip(valores, labels)],
                    textposition='outside',
                    textfont=dict(size=12, color='black', family='Arial Black'),
                    hovertemplate='<b>LOTE %{y}</b><br>TOTAL: %{x:,.0f}<br>QTD/PAL: %{customdata[0]}<br>ENTRADA: %{customdata[1]}<br>VALIDADE: %{customdata[2]}<extra></extra>',
                    customdata=df_filtrado[['QTD_PALETE','ENTRADA','VALIDADE']].values
                ))

                fig.update_layout(
                    plot_bgcolor='#A8D5A2',
                    paper_bgcolor='#A8D5A2',
                    title=f"TODOS OS LOTES - ID {id_sel} - {desc_sel} - FORMATO FOTO VERDE",
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, linecolor='black', linewidth=2, tickfont=dict(size=13, color='black', family='Arial Black')),
                    height= 120 + len(labels)*60,
                    margin=dict(l=220, r=100, t=60, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption("🔵 Azul/⚪ Branco/⚫ Cinza = lotes | Fundo verde igual sua foto | Passe mouse para ver validade, QTD/PALETE e ENTRADA")
        else:
            st.info("👆 Clique em um produto acima para ver TODOS OS LOTES dele no gráfico verde")
