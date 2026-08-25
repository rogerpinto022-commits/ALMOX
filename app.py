import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ = "cadastro_refratario.csv"

# CSS COM DESTAQUE MAXIMO E MARCA D'AGUA
st.markdown("""
<style>
.block-container { z-index:2; position:relative; }
.wm { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; opacity:0.12; pointer-events:none; display:flex; flex-wrap:wrap; gap:80px; justify-content:center; align-content:center; }
.wm span { font-size:30px; font-weight:900; color:#ff4e00; transform:rotate(-30deg); border:3px solid #ff4e00; padding:8px 14px; border-radius:10px; }
.top { position:fixed; top:10px; right:15px; z-index:9999; background:linear-gradient(90deg,#ff4e00,#ff0000); color:#fff; font-weight:900; padding:6px 16px; border-radius:20px; border:2px solid #000; font-size:13px; }
.tabela { width:100%; border-collapse:collapse; font-family:Arial Black; font-size:14px; }
.tabela th { background:#1a252f; color:#fff; padding:12px 8px; border:2px solid #000; text-align:center; }
.tabela td { padding:10px 6px; border:1.5px solid #000; text-align:center; background:#fff; color:#000; font-weight:700; }
.lote { background:#00ff66!important; font-size:16px; border:3px solid #000!important; }
.fundo-verde { background:#A8C5A2; border-left:5px solid #000; padding:25px 15px 25px 0; margin:20px 0; }
.barra { height:52px; margin:16px 0; border:2.5px solid #000; display:flex; align-items:center; padding-left:15px; font-family:Arial Black; font-size:14px; box-shadow:3px 3px 0 #000; }
.azul { background:#6FA8DC; }
.branca { background:#FFFFFF; }
.cinza { background:#8A8A8A; color:white; }
</style>
<div class="wm"><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span><span>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</span></div>
<div class="top">🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</div>
""", unsafe_allow_html=True)

def carregar():
    if not os.path.exists(ARQ): return []
    try:
        df = pd.read_csv(ARQ)
        # limpa
        df = df.fillna("")
        return df.to_dict('records')
    except:
        try: os.remove(ARQ)
        except: pass
        return []

if 'cad' not in st.session_state:
    st.session_state.cad = carregar()
    st.session_state.id_sel = None
    st.session_state.ver_tab = False

st.markdown("<h1 style='text-align:center; background:linear-gradient(90deg,#000,#ff4e00); color:white; padding:20px; border-radius:15px; border:3px solid #ff4e00;'>🔥 REFORMA DE FORNOS - MATERIAIS REFRATARIOS 🔥</h1>", unsafe_allow_html=True)

t1,t2 = st.tabs(["📝 CADASTRO","📊 CLIQUE NO PRODUTO -> VER TODOS OS LOTES (FORMATO FOTO)"])

with t1:
    with st.form("f", clear_on_submit=True):
        a,b,c = st.columns(3)
        with a:
            id_in = st.text_input("ID DO PRODUTO *", "1")
            desc_in = st.text_input("DESCRIÇÃO *", "CIMENTO FONDU")
            marca_in = st.text_input("MARCA", "FONDU")
        with b:
            lote_in = st.text_input("LOTE *", "9999999999")
            val_in = st.text_input("VALIDADE", "00/00/0000")
            qtd_in = st.number_input("QTD POR PALETE", value=1250.0, step=10.0)
        with c:
            ent_in = st.number_input("ENTRADA (PALETES)", value=11.0, step=1.0)
            data_in = st.date_input("DATA", value=date.today())
        if st.form_submit_button("💾 SALVAR LOTE", type="primary", use_container_width=True):
            if id_in and desc_in and lote_in:
                total = float(qtd_in) * float(ent_in)
                st.session_state.cad.append({
                    "ID": str(id_in).strip(),
                    "DESCRICAO": str(desc_in).upper().strip(),
                    "MARCA": str(marca_in).upper().strip(),
                    "LOTE": str(lote_in).strip(),
                    "VALIDADE": str(val_in).strip(),
                    "QTD_PALETE": float(qtd_in),
                    "ENTRADA": float(ent_in),
                    "TOTAL": float(total),
                    "DATA": data_in.strftime("%d/%m/%Y")
                })
                pd.DataFrame(st.session_state.cad).to_csv(ARQ, index=False)
                st.success(f"LOTE {lote_in} SALVO!"); st.rerun()
            else:
                st.error("Preencha ID, DESCRIÇÃO e LOTE")

    if st.session_state.cad:
        if st.button("👁️ VER TABELA COMPLETA" if not st.session_state.ver_tab else "🙈 ESCONDER TABELA", type="secondary"):
            st.session_state.ver_tab = not st.session_state.ver_tab
            st.rerun()
        if st.session_state.ver_tab:
            html = '<table class="tabela"><tr><th>ID</th><th>DESCRIÇÃO</th><th>MARCA</th><th>LOTE</th><th>VALIDADE</th><th>QTD/PAL</th><th>ENTRADA</th><th>TOTAL</th><th>DATA</th></tr>'
            for r in st.session_state.cad:
                html += f"<tr><td><b>{r.get('ID','')}</b></td><td>{r.get('DESCRICAO','')}</td><td>{r.get('MARCA','')}</td><td class='lote'>{r.get('LOTE','')}</td><td><b>{r.get('VALIDADE','')}</b></td><td>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td><b>{r.get('TOTAL','')}</b></td><td>{r.get('DATA','')}</td></tr>"
            html += '</table>'
            st.markdown(html, unsafe_allow_html=True)
            st.write("")
            for i in range(len(st.session_state.cad)-1, -1, -1):
                r = st.session_state.cad[i]
                c1,c2 = st.columns([4,1])
                c1.write(f"**ID {r.get('ID')}** - {r.get('DESCRICAO')} - **LOTE {r.get('LOTE')}**")
                if c2.button("🗑️", key=f"del_{i}_{r.get('LOTE')}"):
                    st.session_state.cad.pop(i)
                    if st.session_state.cad: pd.DataFrame(st.session_state.cad).to_csv(ARQ, index=False)
                    else:
                        if os.path.exists(ARQ): os.remove(ARQ)
                    st.rerun()

with t2:
    if not st.session_state.cad:
        st.warning("⚠️ Nenhum lote cadastrado. Vá na aba CADASTRO")
    else:
        # PEGA PRODUTOS ÚNICOS SEM USAR PANDAS PERIGOSO
        mapa_prod = {}
        for r in st.session_state.cad:
            idk = str(r.get('ID','?')).strip()
            if idk not in mapa_prod:
                mapa_prod[idk] = {"ID": idk, "DESCRICAO": r.get('DESCRICAO',''), "MARCA": r.get('MARCA',''), "QTD_LOTES":0}
            mapa_prod[idk]["QTD_LOTES"] += 1

        st.markdown(f"### 📦 {len(mapa_prod)} PRODUTOS CADASTRADOS - CLIQUE PARA VER TODOS OS LOTES:")

        cols = st.columns(3)
        for idx, (idk, info) in enumerate(mapa_prod.items()):
            with cols[idx % 3]:
                # DESTAQUE VISUAL
                st.markdown(f"""
                <div style="border:3px solid #000; background:#fff7e6; padding:8px; border-radius:10px; text-align:center; margin-bottom:5px;">
                <b style="font-size:18px;">ID {info['ID']}</b><br>
                <b>{info['DESCRICAO']}</b><br>
                <span style="background:#00ff66; padding:2px 8px; border:2px solid #000; font-weight:900;">{info['QTD_LOTES']} LOTES</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"VER LOTES ID {idk}", key=f"ver_{idk}_{idx}", use_container_width=True, type="primary"):
                    st.session_state.id_sel = idk

        if st.session_state.id_sel:
            id_sel = str(st.session_state.id_sel)
            lotes_do_produto = [r for r in st.session_state.cad if str(r.get('ID')) == id_sel]

            if not lotes_do_produto:
                st.error("Nenhum lote")
            else:
                desc = lotes_do_produto[0].get('DESCRICAO','')
                st.markdown(f"""
                <div style="background:linear-gradient(90deg,#1a252f,#2f3d4a); color:white; padding:18px; border-radius:12px; border:3px solid #ff4e00; text-align:center; margin:20px 0;">
                <h2 style="margin:0;">🔥 PRODUTO ID {id_sel} - {desc} 🔥</h2>
                <h3 style="margin:5px 0; color:#00ff66;">{len(lotes_do_produto)} LOTES CADASTRADOS</h3>
                </div>
                """, unsafe_allow_html=True)

                # TABELA SÓ DESSE PRODUTO COM DESTAQUE
                html = '<table class="tabela"><tr><th style="background:#ff4e00;">LOTE</th><th>VALIDADE</th><th>QTD/PAL</th><th>ENTRADA</th><th>TOTAL</th><th>DATA</th></tr>'
                for r in sorted(lotes_do_produto, key=lambda x: x.get('LOTE','')):
                    html += f"<tr><td class='lote'>{r.get('LOTE','')}</td><td style='font-size:16px; background:#ffff00;'><b>{r.get('VALIDADE','')}</b></td><td>{r.get('QTD_PALETE','')}</td><td>{r.get('ENTRADA','')}</td><td style='font-size:16px;'><b>{r.get('TOTAL','')}</b></td><td>{r.get('DATA','')}</td></tr>"
                html += '</table>'
                st.markdown(html, unsafe_allow_html=True)

                # GRAFICO EXATO IGUAL SUA FOTO - TODOS OS LOTES DO PRODUTO
                st.markdown(f"""
                <div style="background:#000; color:#00ff66; padding:10px; font-family:Arial Black; text-align:center; margin-top:25px; border:3px solid #00ff66;">
                📊 GRAFICO FORMATO DA FOTO - TODOS OS LOTES DO PRODUTO ID {id_sel} - FUNDO VERDE
                </div>
                <div class="fundo-verde">
                """, unsafe_allow_html=True)

                # Calcula maior total para proporção
                max_total = max([float(r.get('TOTAL',0)) for r in lotes_do_produto]) or 1

                for i, r in enumerate(sorted(lotes_do_produto, key=lambda x: str(x.get('LOTE')))):
                    total = float(r.get('TOTAL',0))
                    prop = 25 + (total / max_total * 70) # 25% a 95% igual foto
                    cor_classe = ["azul","branca","cinza","branca"][i % 4]

                    st.markdown(f"""
                    <div class="barra {cor_classe}" style="width:{prop:.1f}%;">
                        🔥 LOTE {r.get('LOTE','')} | VALIDADE {r.get('VALIDADE','')} | {total:,.0f} KILOS | {r.get('ENTRADA','')} PALETES
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
                st.info("✅ FORMATO IGUAL SUA FOTO: fundo verde #A8C5A2, barra azul comprida em cima, brancas e cinza, borda preta grossa, risco preto na esquerda. Cada barra = 1 LOTE do produto clicado")
        else:
            st.info("👆 CLIQUE EM UM PRODUTO ACIMA PARA VER TODOS OS LOTES DELE NO FORMATO DA FOTO")
