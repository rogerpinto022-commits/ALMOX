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

def carregar_e_corrigir():
    """ESPECIALISTA: Corrige qualquer CSV com qualquer nome de coluna"""
    lista=[]
    if os.path.exists(ARQ_CAD):
        try:
            df=pd.read_csv(ARQ_CAD)
            # 1. Normaliza nomes: tira acento, maiusculo, tira espaços
            df.columns=[str(c).upper().strip().replace("Ç","C").replace("Ã","A").replace("Á","A").replace("É","E").replace("/","_").replace(" ","_") for c in df.columns]
            # 2. Garante colunas padrão
            for col in ["ID","DESCRICAO","MARCA","LOTE","VALIDADE","QTD_PALETE","ENTRADA","TOTAL","UNIDADE","DATA"]:
                if col not in df.columns:
                    # tenta achar similar
                    if col=="QTD_PALETE" and "QTD" in "".join(df.columns):
                        for c in df.columns:
                            if "QTD" in c: df["QTD_PALETE"]=pd.to_numeric(df[c], errors='coerce').fillna(1250); break
                    elif col=="TOTAL" and "QTD_PALETE" in df.columns and "ENTRADA" in df.columns:
                        df["TOTAL"]=pd.to_numeric(df["QTD_PALETE"],errors='coerce').fillna(0) * pd.to_numeric(df["ENTRADA"],errors='coerce').fillna(0)
                    else:
                        df[col]=0 if col in ["QTD_PALETE","ENTRADA","TOTAL"] else ""
            # 3. Converte numérico
            for c in ["QTD_PALETE","ENTRADA","TOTAL"]:
                df[c]=pd.to_numeric(df[c], errors='coerce').fillna(0)
            # 4. Se TOTAL ainda 0, calcula
            df.loc[df["TOTAL"]==0, "TOTAL"] = df["QTD_PALETE"] * df["ENTRADA"]
            lista=df.to_dict('records')
        except Exception as e:
            st.error(f"CSV corrompido, vou zerar: {e}")
            if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
    return lista

if 'iniciado' not in st.session_state:
    st.session_state.cadastro=carregar_e_corrigir()
    st.session_state.iniciado=True
    st.session_state.mostrar_tabela=False
    st.session_state.id_selecionado=None

st.title("🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS")
tab1,tab2,tab3 = st.tabs(["📝 CADASTRO","📦 TABELA","📊 TODOS LOTES DO PRODUTO"])

with tab1:
    with st.form("cad",clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1: id_p=st.text_input("ID","1"); desc=st.text_input("DESCRICAO","CIMENTO"); marca=st.text_input("MARCA","FONDU")
        with c2: lote=st.text_input("LOTE","99999999999"); validade=st.text_input("VALIDADE","00/00/0000"); qtd_pal=st.number_input("QTD/PALETE",value=1250.0)
        with c3: entrada=st.number_input("ENTRADA",value=11.0); unidade=st.text_input("UNIDADE","KILOS"); data=st.date_input("DATA",value=date.today())
        if st.form_submit_button("💾 SALVAR",type="primary"):
            total=float(qtd_pal)*float(entrada)
            st.session_state.cadastro.append({"ID":str(id_p).strip(),"DESCRICAO":str(desc).upper().strip(),"MARCA":str(marca).upper().strip(),"LOTE":str(lote).strip(),"VALIDADE":str(validade),"QTD_PALETE":float(qtd_pal),"ENTRADA":float(entrada),"TOTAL":float(total),"UNIDADE":str(unidade),"DATA":data.strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.success("Salvo!"); st.rerun()
    if st.button("🗑️ ZERAR TUDO (apaga CSV corrompido)"):
        st.session_state.cadastro=[]
        if os.path.exists(ARQ_CAD): os.remove(ARQ_CAD)
        st.rerun()

with tab2:
    if not st.session_state.cadastro:
        st.info("Sem dados")
    else:
        if st.button("👁️ VER TABELA" if not st.session_state.mostrar_tabela else "🙈 ESCONDER", type="primary", key="btn_tab"):
            st.session_state.mostrar_tabela=not st.session_state.mostrar_tabela; st.rerun()
        if st.session_state.mostrar_tabela:
            html='<table class="tabela-ref"><tr><th>ID</th><th>DESCRIÇÃO</th><th>MARCA</th><th>LOTE</th><th>VALIDADE</th><th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL</th><th>UNIDADE</th><th>DATA</th></tr>'
            for r in st.session_state.cadastro:
                html+=f"<tr><td>{r.get('ID','')}</td><td>{r.get('DESCRICAO','')}</td><td>{r.get('MARCA','')}</td><td class='lote-verde'>{r.get('LOTE','')}</td><td>{r.get('VALIDADE','')}</td><td class='qtd-cinza'>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td>{r.get('TOTAL','')}</td><td>{r.get('UNIDADE','')}</td><td>{r.get('DATA','')}</td></tr>"
            html+='</table>'
            st.markdown(html,unsafe_allow_html=True)

with tab3:
    st.markdown("### CLIQUE NO PRODUTO PARA VER TODOS OS LOTES")
    if not st.session_state.cadastro:
        st.warning("Cadastre primeiro")
    else:
        df=pd.DataFrame(st.session_state.cadastro)
        # Garante colunas numéricas
        for c in ["TOTAL","QTD_PALETE","ENTRADA"]:
            df[c]=pd.to_numeric(df[c], errors='coerce').fillna(0)

        produtos_unicos = df.drop_duplicates(subset=['ID']).copy()

        st.write(f"**{len(produtos_unicos)} produtos - CLIQUE:**")
        cols=st.columns(3)
        for i, (_, row) in enumerate(produtos_unicos.iterrows()):
            id_prod=str(row.get('ID','?'))
            desc_prod=str(row.get('DESCRICAO','?'))
            qtd_lotes=len(df[df['ID'].astype(str)==id_prod])
            with cols[i%3]:
                if st.button(f"📦 ID {id_prod} - {desc_prod}\n{qtd_lotes} lotes", key=f"prod_{id_prod}_{i}", use_container_width=True):
                    st.session_state.id_selecionado=id_prod

        if st.session_state.id_selecionado:
            id_sel=str(st.session_state.id_selecionado)
            df_filtrado=df[df['ID'].astype(str)==id_sel].copy()

            if df_filtrado.empty:
                st.error("Nenhum lote")
            else:
                # CORREÇÃO TOTAL SE VAZIO
                df_filtrado["TOTAL"]=df_filtrado["TOTAL"].fillna(0)
                df_filtrado.loc[df_filtrado["TOTAL"]==0, "TOTAL"] = df_filtrado["QTD_PALETE"] * df_filtrado["ENTRADA"]

                desc_sel=df_filtrado.iloc[0].get('DESCRICAO','')
                st.success(f"### PRODUTO ID {id_sel} - {desc_sel} | {len(df_filtrado)} LOTES")

                # TABELA LOTES
                html='<table class="tabela-ref"><tr><th>LOTE</th><th>MARCA</th><th>VALIDADE</th><th>QTD/PALETE</th><th>ENTRADA</th><th>TOTAL</th><th>DATA</th></tr>'
                for _, r in df_filtrado.iterrows():
                    html+=f"<tr><td class='lote-verde'>{r.get('LOTE','')}</td><td>{r.get('MARCA','')}</td><td>{r.get('VALIDADE','')}</td><td class='qtd-cinza'>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td>{r.get('TOTAL','')}</td><td>{r.get('DATA','')}</td></tr>"
                html+='</table>'
                st.markdown(html,unsafe_allow_html=True)

                # GRÁFICO FORMATO FOTO VERDE - BLINDADO
                try:
                    labels = df_filtrado['LOTE'].astype(str).tolist()
                    valores = pd.to_numeric(df_filtrado['TOTAL'], errors='coerce').fillna(0).tolist()

                    cores_base = ["#6FA8DC", "#FFFFFF", "#808080", "#EFEFEF"]
                    cores = [cores_base[i % len(cores_base)] for i in range(len(labels))]

                    fig = go.Figure(go.Bar(
                        x=valores,
                        y=[f"LOTE {str(l)} | VAL {str(v)}" for l, v in zip(df_filtrado['LOTE'].astype(str), df_filtrado['VALIDADE'].astype(str))],
                        orientation='h',
                        marker=dict(color=cores, line=dict(color='black', width=1.5)),
                        text=[f"{float(v):,.0f} | L:{l}" for v, l in zip(valores, labels)],
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>TOTAL: %{x}<extra></extra>'
                    ))
                    fig.update_layout(
                        plot_bgcolor='#A8D5A2', paper_bgcolor='#A8D5A2',
                        title=f"TODOS OS LOTES - ID {id_sel} - {desc_sel}",
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=False, linecolor='black', linewidth=2),
                        height= 120 + len(labels)*65,
                        margin=dict(l=220, r=100, t=60, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro gráfico: {e}")
                    st.dataframe(df_filtrado)
        else:
            st.info("👆 Clique em um produto acima")
