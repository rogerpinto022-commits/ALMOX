import streamlit as st
import pandas as pd
from datetime import date
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
/* GRAFICO IGUAL FOTO */
.grafico-fundo { background:#A8C5A2; padding:20px 20px 20px 0; border-left:3px solid #000; margin-top:20px; }
.barra { height:42px; margin:18px 0; border:1.5px solid #000; display:flex; align-items:center; padding-left:10px; font-weight:900; font-family:Arial; font-size:13px; color:#000; }
.barra-azul { background:#6FA8DC; width:95%; }
.barra-branca { background:#FFFFFF; }
.barra-cinza { background:#8A8A8A; }
</style>
<div class="watermark-container">
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
            df.columns=[str(c).upper().strip().replace("Ç","C").replace("/","_") for c in df.columns]
            for c in ["TOTAL","QTD_PALETE","ENTRADA"]:
                if c in df.columns: df[c]=pd.to_numeric(df[c], errors='coerce').fillna(0)
            if "TOTAL" in df.columns: df.loc[df["TOTAL"]==0,"TOTAL"]=df.get("QTD_PALETE",0)*df.get("ENTRADA",0)
            lista=df.to_dict('records')
        except: pass
    return lista

if 'iniciado' not in st.session_state:
    st.session_state.cadastro=carregar()
    st.session_state.iniciado=True
    st.session_state.id_selecionado=None

st.title("🔥 REFORMA DE FORNOS")
tab1,tab2=st.tabs(["📝 CADASTRO","📊 PRODUTO -> TODOS OS LOTES (FORMATO FOTO)"])

with tab1:
    with st.form("cad",clear_on_submit=True):
        c1,c2,c3=st.columns(3)
        with c1: id_p=st.text_input("ID","1"); desc=st.text_input("DESCRICAO","CIMENTO"); marca=st.text_input("MARCA","FONDU")
        with c2: lote=st.text_input("LOTE","99999999999"); validade=st.text_input("VALIDADE","00/00/0000"); qtd=st.number_input("QTD/PALETE",value=1250.0)
        with c3: entrada=st.number_input("ENTRADA",value=11.0); data=st.date_input("DATA",value=date.today())
        if st.form_submit_button("💾 SALVAR",type="primary"):
            total=qtd*entrada
            st.session_state.cadastro.append({"ID":str(id_p),"DESCRICAO":desc.upper(),"MARCA":marca.upper(),"LOTE":str(lote),"VALIDADE":validade,"QTD_PALETE":qtd,"ENTRADA":entrada,"TOTAL":total,"DATA":data.strftime("%d/%m/%Y")})
            pd.DataFrame(st.session_state.cadastro).to_csv(ARQ_CAD,index=False); st.rerun()

with tab2:
    if not st.session_state.cadastro:
        st.warning("Cadastre")
    else:
        df=pd.DataFrame(st.session_state.cadastro)
        produtos=df.drop_duplicates(subset=['ID'])[['ID','DESCRICAO']]

        st.markdown("### CLIQUE NO PRODUTO:")
        cols=st.columns(4)
        for i,(_,r) in enumerate(produtos.iterrows()):
            qtd_lotes=len(df[df['ID'].astype(str)==str(r['ID'])])
            with cols[i%4]:
                if st.button(f"ID {r['ID']} - {r['DESCRICAO']} ({qtd_lotes} LOTES)", key=f"p_{r['ID']}_{i}", use_container_width=True):
                    st.session_state.id_selecionado=str(r['ID'])

        if st.session_state.id_selecionado:
            id_sel=st.session_state.id_selecionado
            df_f=df[df['ID'].astype(str)==id_sel].copy()
            df_f=df_f.sort_values(by='LOTE')

            st.success(f"PRODUTO ID {id_sel} - {df_f.iloc[0]['DESCRICAO']} - {len(df_f)} LOTES")

            # TABELA SIMPLES DOS LOTES
            st.markdown(f"""
            <table class="tabela-ref">
            <tr><th>LOTE</th><th>VALIDADE</th><th>TOTAL</th></tr>
            {''.join([f"<tr><td class='lote-verde'>{r['LOTE']}</td><td>{r['VALIDADE']}</td><td>{r['TOTAL']}</td></tr>" for _,r in df_f.iterrows()])}
            </table>
            """, unsafe_allow_html=True)

            # GRAFICO EXATO IGUAL SUA FOTO - HTML PURO
            st.markdown(f"<div class='grafico-fundo'>", unsafe_allow_html=True)
            cores=[("barra-azul","95%"),("barra-branca","55%"),("barra-cinza","48%"),("barra-branca","32%")]
            for idx, (_,r) in enumerate(df_f.iterrows()):
                cor, larg = cores[idx % len(cores)]
                # largura proporcional ao TOTAL para parecer validade
                prop = 30 + (float(r['TOTAL']) / float(df_f['TOTAL'].max()) * 65) if df_f['TOTAL'].max()>0 else 50
                st.markdown(f"""
                <div class="barra {cor}" style="width:{prop}%;">
                    LOTE {r['LOTE']} | VALIDADE {r['VALIDADE']} | TOTAL {r['TOTAL']:.0f}
                </div>
                """, unsafe_allow_html=True)
            st.markdown(f"</div>", unsafe_allow_html=True)
            st.caption("Formato igual sua foto: fundo verde #A8C5A2, barra azul em cima, brancas e cinza, borda preta, risco preto na esquerda")
