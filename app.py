import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

st.set_page_config(page_title="REFORMA DE FORNOS", layout="wide", page_icon="🔥")
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"

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
        valido=fab + relativedelta(months=int(safe_float(tempo_meses,12)))
        return valido.strftime("%d/%m/%Y")
    except: return "00/00/0000"

def get_saldos_completos():
    saldos={}
    for r in st.session_state.get('lista_cadastro',[]):
        lote=str(r.get('LOTE','')).strip()
        if not lote: continue
        qtd_palete=safe_float(r.get('QTD_PALETE',0),0)
        entrada_pal=safe_float(r.get('ENTRADA',0),0)
        total=safe_float(r.get('TOTAL',0),0)
        if total==0: total=qtd_palete*entrada_pal
        unidade=str(r.get('UNIDADE','KG')).upper().strip() or "KG"
        if lote not in saldos:
            saldos[lote]=r.copy()
            saldos[lote]['UNIDADE']=unidade
            saldos[lote]['ENTRADAS_PALETES']=entrada_pal
            saldos[lote]['SAIDAS_PALETES']=0
            saldos[lote]['ENTRADAS_QTD']=total
            saldos[lote]['SAIDAS_QTD']=0
            saldos[lote]['SALDO_PALETES']=entrada_pal
            saldos[lote]['SALDO_QTD']=total
            saldos[lote]['QTD_PALETE_BASE']=qtd_palete
        else:
            saldos[lote]['ENTRADAS_PALETES']=safe_float(saldos[lote].get('ENTRADAS_PALETES',0))+entrada_pal
            saldos[lote]['ENTRADAS_QTD']=safe_float(saldos[lote].get('ENTRADAS_QTD',0))+total
            saldos[lote]['SALDO_PALETES']=safe_float(saldos[lote].get('SALDO_PALETES',0))+entrada_pal
            saldos[lote]['SALDO_QTD']=safe_float(saldos[lote].get('SALDO_QTD',0))+total
    for m in st.session_state.get('lista_mov',[]):
        lote=str(m.get('LOTE','')).strip()
        if lote in saldos:
            paletes=safe_float(m.get('PALETES',0),0)
            qtd=safe_float(m.get('TOTAL_QTD',0),0)
            if str(m.get('TIPO','')).upper()=="ENTRADA":
                saldos[lote]['ENTRADAS_PALETES']=safe_float(saldos[lote].get('ENTRADAS_PALETES',0))+paletes
                saldos[lote]['ENTRADAS_QTD']=safe_float(saldos[lote].get('ENTRADAS_QTD',0))+qtd
                saldos[lote]['SALDO_PALETES']=safe_float(saldos[lote].get('SALDO_PALETES',0))+paletes
                saldos[lote]['SALDO_QTD']=safe_float(saldos[lote].get('SALDO_QTD',0))+qtd
            else:
                saldos[lote]['SAIDAS_PALETES']=safe_float(saldos[lote].get('SAIDAS_PALETES',0))+paletes
                saldos[lote]['SAIDAS_QTD']=safe_float(saldos[lote].get('SAIDAS_QTD',0))+qtd
                saldos[lote]['SALDO_PALETES']=safe_float(saldos[lote].get('SALDO_PALETES',0))-paletes
                saldos[lote]['SALDO_QTD']=safe_float(saldos[lote].get('SALDO_QTD',0))-qtd
    return saldos

st.markdown("""
<style>
.tabela { width:100%; border-collapse:collapse; font-size:11px; display:block; overflow-x:auto; }
.tabela th { background:#1a252f; color:#fff; padding:10px 5px; border:2px solid #000; text-align:center; font-family:Arial Black; font-size:10px; }
.tabela td { padding:8px 5px; border:1.5px solid #000; text-align:center; background:#fff; color:#000; font-weight:700; font-size:11px; }
.lote { background:#00ff66!important; border:3px solid #000!important; }
.val { background:#ffff00!important; border:2px solid #000!important; }
.fab { background:#a0d8ff!important; }
.fundo-verde { background:#A8C5A2; border-left:6px solid #000; padding:20px 10px 20px 0; margin:15px 0; border:3px solid #000; }
.barra { height:54px; margin:16px 0; border:2.5px solid #000; display:flex; align-items:center; padding-left:12px; font-family:Arial Black; font-size:11px; box-shadow:4px 4px 0 #000; }
.azul { background:#6FA8DC; }.branca { background:#FFFFFF; }.cinza { background:#8A8A8A; color:#fff; }
.card { border:3px solid #000; border-radius:12px; padding:12px; text-align:center; background:white; box-shadow:5px 5px 0 #000; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; background:#000; color:#00ff66; padding:18px; border-radius:12px; border:4px solid #ff4e00; font-family:Arial Black;'>🔥 REFORMA DE FORNOS - UNIDADE DINÂMICA 🔥</h1>", unsafe_allow_html=True)

tab1,tab2,tab3,tab4,tab5=st.tabs(["📝 CADASTRO","🔄 ENTRADA/SAIDA POR PALETES","📦 ESTOQUE","📊 LOTES - BARRAS VALIDADE","📈 GRAFICOS"])

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
            tempo_in=st.number_input("TEMPO VALIDADE MESES*", value=12, min_value=1)
            unidade_in=st.selectbox("UNIDADE*",["KG","UNIDADE","SACO","BLOCO","TIJOLO","LATA","CAIXA","METRO","LITRO"], index=0)
            qtd_in=st.number_input(f"QTD POR PALETE* (em {unidade_in})", value=1250.0)
        with c3:
            ent_in=st.number_input("QTD PALETES ENTRADA*", value=11.0)
            total_prev=safe_float(qtd_in)*safe_float(ent_in)
            st.metric(f"TOTAL EM {unidade_in}", f"{total_prev:,.0f} {unidade_in}")
            st.metric("TOTAL PALETES", f"{safe_float(ent_in):.1f}")
        if st.form_submit_button("💾 CADASTRAR", type="primary", use_container_width=True):
            fab_str=fab_in.strftime("%d/%m/%Y")
            valido_ate=calcular_valido_ate(fab_str, tempo_in)
            total=safe_float(qtd_in)*safe_float(ent_in)
            st.session_state.lista_cadastro.append({
                "ID":str(id_in).strip(),"DESCRICAO":str(desc_in).upper().strip(),"MARCA":str(marca_in).upper().strip(),
                "LOTE":str(lote_in).strip(),"FABRICACAO":fab_str,"TEMPO_VALIDADE":int(safe_float(tempo_in,12)),"VALIDO_ATE":valido_ate,
                "QTD_PALETE":safe_float(qtd_in),"ENTRADA":safe_float(ent_in),"TOTAL":total,"UNIDADE":str(unidade_in).upper(),
                "DATA_CADASTRO":date.today().strftime("%d/%m/%Y")
            })
            pd.DataFrame(st.session_state.lista_cadastro).to_csv(ARQ_CAD,index=False)
            st.success(f"✅ LOTE {lote_in} - {ent_in:.1f} PALETES = {total:.0f} {unidade_in}"); st.rerun()

with tab2:
    st.markdown("### 🔄 MOVIMENTAÇÃO POR PALETES - UNIDADE DO CADASTRO")
    if not st.session_state.get('lista_cadastro'):
        st.warning("Cadastre primeiro")
    else:
        lotes_disponiveis=[str(r.get('LOTE','')) for r in st.session_state.lista_cadastro if r.get('LOTE')]
        c1,c2,c3=st.columns(3)
        with c1:
            lote_mov=st.selectbox("LOTE*", options=lotes_disponiveis, key="sel_lote_mov")
            qtd_por_palete_base=1250
            unidade_base="KG"
            for r in st.session_state.lista_cadastro:
                if str(r.get('LOTE'))==str(lote_mov):
                    qtd_por_palete_base=safe_float(r.get('QTD_PALETE',1250),1250)
                    unidade_base=str(r.get('UNIDADE','KG')).upper() or "KG"
                    break
            st.info(f"QTD/PALETE: {qtd_por_palete_base:.0f} {unidade_base}")
        with c2:
            tipo_mov=st.selectbox("TIPO*", ["SAIDA","ENTRADA"], key="sel_tipo_mov")
            paletes_mov=st.number_input("QTD PALETES*", value=1.0, min_value=0.1, step=0.5, key="num_paletes_mov")
            total_qtd_mov=safe_float(paletes_mov)*safe_float(qtd_por_palete_base)
            st.metric(f"TOTAL EM {unidade_base}", f"{total_qtd_mov:,.0f} {unidade_base}")
        with c3:
            motivo=st.text_input("MOTIVO*","REFORMA FORNO", key="txt_motivo")
            saldos=get_saldos_completos()
            saldo_atual=saldos.get(str(lote_mov),{})
            if saldo_atual:
                unid=saldo_atual.get('UNIDADE','KG')
                st.metric(f"SALDO PALETES", f"{safe_float(saldo_atual.get('SALDO_PALETES',0)):.1f}")
                st.metric(f"SALDO {unid}", f"{safe_float(saldo_atual.get('SALDO_QTD',0)):,.0f} {unid}")
        if st.button(f"✅ REGISTRAR", type="primary", use_container_width=True, key="btn_reg_mov"):
            if tipo_mov=="SAIDA" and saldo_atual and safe_float(saldo_atual.get('SALDO_PALETES',0))<safe_float(paletes_mov):
                st.error(f"⛔ SALDO INSUFICIENTE! Saldo: {safe_float(saldo_atual.get('SALDO_PALETES',0)):.1f} PALETES")
            else:
                st.session_state.lista_mov.append({
                    "LOTE":str(lote_mov),"TIPO":tipo_mov,"PALETES":safe_float(paletes_mov),"QTD_POR_PALETE":safe_float(qtd_por_palete_base),
                    "TOTAL_QTD":safe_float(total_qtd_mov),"UNIDADE":unidade_base,"MOTIVO":motivo,"DATA":date.today().strftime("%d/%m/%Y"),"HORA":datetime.now().strftime("%H:%M")
                })
                pd.DataFrame(st.session_state.lista_mov).to_csv(ARQ_MOV,index=False)
                st.success(f"✅ {tipo_mov} {paletes_mov:.1f} PALETES = {total_qtd_mov:,.0f} {unidade_base}"); st.rerun()
        if st.session_state.get('lista_mov'):
            st.dataframe(pd.DataFrame(st.session_state.lista_mov), use_container_width=True)

with tab3:
    st.markdown("### 📦 ESTOQUE - UNIDADE DINÂMICA")
    if not st.session_state.get('lista_cadastro'): st.warning("Sem cadastro")
    else:
        saldos=get_saldos_completos()
        html="""<table class="tabela"><tr><th>ID</th><th>DESCRIÇÃO</th><th>LOTE</th><th>FAB</th><th>VÁLIDO ATÉ</th><th>UNIDADE</th><th>QTD/PAL</th><th>ENT PAL</th><th>SAI PAL</th><th>SALDO PAL</th><th>ENT QTD</th><th>SAI QTD</th><th>SALDO QTD</th><th>STATUS</th></tr>"""
        for lote,r in saldos.items():
            saldo_qtd=safe_float(r.get('SALDO_QTD',0))
            saldo_pal=safe_float(r.get('SALDO_PALETES',0))
            unidade=str(r.get('UNIDADE','KG')).upper()
            qtd_base=safe_float(r.get('QTD_PALETE_BASE',0) or r.get('QTD_PALETE',0),0)
            html+=f"<tr><td><b>{r.get('ID','')}</b></td><td>{r.get('DESCRICAO','')}</td><td class='lote'>{lote}</td><td class='fab'><b>{r.get('FABRICACAO','')}</b></td><td class='val'><b>{r.get('VALIDO_ATE','')}</b></td><td style='background:#ffcc99;'><b>{unidade}</b></td><td>{qtd_base:,.0f}</td><td style='background:#a0ffa0;'>{safe_float(r.get('ENTRADAS_PALETES',0)):.1f}</td><td style='background:#ffb0b0;'>{safe_float(r.get('SAIDAS_PALETES',0)):.1f}</td><td style='background:#7fff7f;'><b>{saldo_pal:.1f}</b></td><td style='background:#a0ffa0;'>{safe_float(r.get('ENTRADAS_QTD',0)):,.0f}</td><td style='background:#ffb0b0;'>{safe_float(r.get('SAIDAS_QTD',0)):,.0f}</td><td style='background:#7fff7f;'><b>{saldo_qtd:,.0f} {unidade}</b></td><td>{'✅ OK' if saldo_qtd>0 else '⛔ ZERADO'}</td></tr>"
        html+="</table>"
        st.markdown(html, unsafe_allow_html=True)

with tab4:
    st.markdown("### 📊 LOTES - BARRAS VALIDADE")
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
            st.markdown('<div style="background:#000; color:#fff; padding:8px; text-align:center; font-family:Arial Black; margin-top:20px; border:3px solid #00ff66;">📊 GRAFICO DE BARRAS - VALIDADE - FUNDO VERDE</div><div class="fundo-verde">', unsafe_allow_html=True)
            max_t=max([safe_float(saldos.get(str(r.get('LOTE')),{}).get('SALDO_QTD',0)) for r in lotes]) or 1
            for i,r in enumerate(sorted(lotes, key=lambda x: str(x.get('LOTE','')))):
                lote=str(r.get('LOTE')); saldo_qtd=safe_float(saldos.get(lote,{}).get('SALDO_QTD',0)); unidade=str(saldos.get(lote,{}).get('UNIDADE','KG'))
                prop=30+(saldo_qtd/max_t*65) if max_t>0 else 50
                cor=["azul","branca","cinza","branca"][i%4]
                saldo_pal=safe_float(saldos.get(lote,{}).get('SALDO_PALETES',0))
                st.markdown(f'<div class="barra {cor}" style="width:{prop:.1f}%;">LOTE {r.get("LOTE")} | VÁLIDO ATÉ {r.get("VALIDO_ATE")} | SALDO {saldo_qtd:,.0f} {unidade} ({saldo_pal:.1f} PAL)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown("### 📈 GRAFICOS - UNIDADE DINÂMICA")
    if not st.session_state.get('lista_cadastro'):
        st.warning("Sem dados")
    else:
        try:
            saldos=get_saldos_completos()
            if not saldos:
                st.warning("Sem saldo")
            else:
                lista=[]
                for lote,d in saldos.items():
                    # garante campos basicos
                    desc=str(d.get('DESCRICAO','SEM DESC')).strip() or "SEM DESC"
                    idv=str(d.get('ID','?')).strip() or "?"
                    lista.append({
                        "LOTE": str(lote),
                        "DESCRICAO": desc,
                        "ID": idv,
                        "VALIDO_ATE": str(d.get('VALIDO_ATE','00/00/0000')),
                        "UNIDADE": str(d.get('UNIDADE','KG')),
                        "SALDO_QTD": safe_float(d.get('SALDO_QTD',0)),
                        "SALDO_PAL": safe_float(d.get('SALDO_PALETES',0))
                    })
                df=pd.DataFrame(lista)
                df=df[df["SALDO_QTD"]>0]
                if df.empty:
                    st.info("Sem saldo positivo para grafico")
                else:
                    c1,c2=st.columns(2)
                    with c1:
                        fig1=px.bar(df, x='DESCRICAO', y='SALDO_QTD', color='ID', title="SALDO POR PRODUTO (NA UNIDADE CADASTRADA)", text='UNIDADE')
                        fig1.update_traces(textposition='outside')
                        st.plotly_chart(fig1, use_container_width=True)
                    with c2:
                        fig2=px.bar(df, x='LOTE', y='SALDO_PAL', color='VALIDO_ATE', title="SALDO PALETES X VALIDADE")
                        fig2.update_layout(plot_bgcolor='#A8C5A2')
                        st.plotly_chart(fig2, use_container_width=True)
                    fig3=px.bar(df, x='LOTE', y='SALDO_QTD', color='VALIDO_ATE', title="SALDO NA UNIDADE CADASTRADA X VALIDADE")
                    fig3.update_layout(plot_bgcolor='#A8C5A2')
                    st.plotly_chart(fig3, use_container_width=True)
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro grafico: {e}")
            st.info("Mostrando tabela bruta para debug")
            try:
                saldos=get_saldos_completos()
                st.dataframe(pd.DataFrame(list(saldos.values())))
            except Exception as e2:
                st.error(f"Erro tabela: {e2}")
