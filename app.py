import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta, date
import plotly.express as px

st.set_page_config(page_title="REFORMA", layout="wide")
fuso = timezone(timedelta(hours=-3))
ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_GRD = "grd.csv"
ARQ_EMAILS = "emails.csv"
LOCAIS = ["GALPAO DE MATERIAIS REFRATARIOS","SALA ANEXA","OFICINA DE REVESTIMENTO REFORMA DE FORNOS"]
TIPOS = ["PALETE","CAIXA","SACO","FARDO","BAG","TAMBOR","UNIDADE"]

def sf(v,d=0.0):
    try: return float(str(v).replace(",",".")) if str(v).strip()!="" else float(d)
    except: return float(d)

def carregar(p):
    if not os.path.exists(p): return []
    try: df=pd.read_csv(p,dtype=str,encoding='utf-8').fillna("")
    except:
        try: df=pd.read_csv(p,dtype=str,encoding='latin-1').fillna("")
        except: return []
    df.columns=[str(c).upper().strip() for c in df.columns]
    return df.to_dict('records')

def salvar():
    try:
        pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False,encoding='utf-8')
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False,encoding='utf-8')
        pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD,index=False,encoding='utf-8')
    except: pass

def get_saldos():
    saldos={}; carac={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper().strip(); desc=str(r.get('DESCRICAO','')).upper().strip()
        if not idp or not desc: continue
        k=f"{idp}__{desc}__{str(r.get('MARCA','')).upper()}"
        if k not in carac:
            vh=sf(r.get('VALIDADE_HORAS',0),0); vd=sf(r.get('VALIDADE_DIAS',0),0)
            if vd==0 and vh>0: vd=vh/24.0
            if vd==0: vd=30
            carac[k]={'ID':idp,'DESCRICAO':desc,'TIPO':str(r.get('TIPO_EMBALAGEM',r.get('TIPO','PALETE'))).upper(),'QTD':sf(r.get('QTD_POR_EMBALAGEM',r.get('QTD_PALETE',1250)),1250),'MARCA':str(r.get('MARCA','')).upper(),'FAB':str(r.get('DATA_FABRICACAO',r.get('FABRICACAO',''))),'VAL':vd}
    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip(); lote=str(m.get('LOTE','')).upper().strip()
            if not idp or not lote: continue
            desc=str(m.get('DESCRICAO','')).upper()
            local=str(m.get('LOCAL_MOV',LOCAIS[0])).upper()
            if "SALA" in local: local=LOCAIS[1]
            elif "OFIC" in local: local=LOCAIS[2]
            else: local=LOCAIS[0]
            c=None
            for v in carac.values():
                if v['ID']==idp and v['DESCRICAO']==desc: c=v; break
            if not c:
                for v in carac.values():
                    if v['ID']==idp: c=v; break
            if not c: continue
            chave=f"{idp}__{desc}__{local}__{lote}"
            if chave not in saldos:
                vm=sf(m.get('VALIDADE_DIAS',0),0)
                if vm==0:
                    vh=sf(m.get('VALIDADE_HORAS',0),0); vm=vh/24.0 if vh>0 else c['VAL']
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'TIPO':c['TIPO'],'QTD':c['QTD'],'LOCAL':local,'LOTE':lote,'MARCA':c['MARCA'],'SALDO':0,'ULT':str(m.get('DATA_HORA','')),'FAB':str(m.get('DATA_FABRICACAO',c['FAB'])),'VAL':vm,'DATA_VAL':str(m.get('DATA_VALIDADE',''))}
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=sf(m.get('TOTAL_QTD',0)); saldos[chave]['ULT']=str(m.get('DATA_HORA',''))
            else: saldos[chave]['SALDO']-=sf(m.get('TOTAL_QTD',0)); saldos[chave]['ULT']=str(m.get('DATA_HORA',''))
        except: continue
    return saldos,carac

if 'ok' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD); st.session_state.mov=carregar(ARQ_MOV); st.session_state.grd=carregar(ARQ_GRD); st.session_state.ok=True
if 'tempo' not in st.session_state: st.session_state.tempo=2
if not os.path.exists(ARQ_EMAILS): pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'log' not in st.session_state: st.session_state.log=False
if 'user' not in st.session_state: st.session_state.user=None

if not st.session_state.log:
    st.title("REFORMA")
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS,dtype=str).fillna(""); df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
        u=df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
        if not u.empty: st.session_state.log=True; st.session_state.user=u.iloc[0].to_dict(); st.rerun()
        else: st.error("Invalido")
    st.stop()

agora=datetime.now(fuso)
st.sidebar.write(f"{st.session_state.user.get('NOME')} | CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
if st.sidebar.button("Sair"): salvar(); st.session_state.log=False; st.rerun()

tabs=st.tabs(["CADASTRO","ENTRADA / SAIDA","ESTOQUE","GRAFICO QTD","HISTORICO"])
tab_cad, tab_mov, tab_est, tab_graf, tab_hist = tabs

with tab_cad:
    st.subheader("CADASTRO")
    id_in=st.text_input("ID", placeholder="Ex: 15", key="id_cad")
    with st.form("form_cad"):
        c1,c2=st.columns([1,3])
        with c1: id_f=st.text_input("ID", value=id_in.upper() if id_in else "", key="idf")
        with c2: desc=st.text_input("DESCRIÇÃO", key="desc")
        c3,c4,c5=st.columns(3)
        with c3: tipo=st.selectbox("EMB", TIPOS, key="tipo")
        with c4: qtd=st.number_input("QTD/EMB", min_value=0.1, value=1250.0, key="qtd")
        with c5: marca=st.text_input("MARCA", key="marca")
        cf1,cf2=st.columns(2)
        with cf1: data_fab=st.date_input("FABRICAÇÃO", value=date.today(), key="dfab")
        with cf2:
            val_dias=st.number_input("VALIDADE DIAS", min_value=1, max_value=3650, value=30, step=1, key="val")
            data_val=data_fab + timedelta(days=val_dias)
            st.caption(f"{data_val.strftime('%d/%m/%Y')} = {val_dias} dias")
        if st.form_submit_button("CADASTRAR", type="primary", use_container_width=True):
            if id_f and desc:
                st.session_state.cad.append({"ID":id_f.upper().strip(),"DESCRICAO":desc.upper(),"TIPO_EMBALAGEM":tipo.upper(),"QTD_POR_EMBALAGEM":qtd,"MARCA":marca.upper() if marca else "SEM MARCA","DATA_FABRICACAO":data_fab.strftime("%d/%m/%Y"),"VALIDADE_DIAS":val_dias,"DATA_VALIDADE":data_val.strftime("%d/%m/%Y")})
                salvar(); st.rerun()
    if st.session_state.cad:
        st.dataframe(pd.DataFrame(st.session_state.cad), use_container_width=True, height=250)

with tab_mov:
    st.subheader("ENTRADA / SAIDA")
    id_mov=st.text_input("ID", placeholder="Digite ID + ENTER", key="id_mov")
    mats=[]
    if id_mov:
        up=id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==up and str(r.get('DESCRICAO','')).strip()!="":
                vh=sf(r.get('VALIDADE_HORAS',0),0); vd=sf(r.get('VALIDADE_DIAS',0),0)
                if vd==0 and vh>0: vd=vh/24.0
                if vd==0: vd=30
                mats.append({'DESCRICAO':str(r.get('DESCRICAO','')).upper(),'MARCA':str(r.get('MARCA','')).upper(),'TIPO':str(r.get('TIPO_EMBALAGEM',r.get('TIPO','PALETE'))).upper(),'QTD':sf(r.get('QTD_POR_EMBALAGEM',r.get('QTD_PALETE',1250)),1250),'FAB':str(r.get('DATA_FABRICACAO',r.get('FABRICACAO',''))),'VAL':vd})

    if id_mov and not mats:
        st.error(f"ID {id_mov.upper()} não cadastrado")
    elif mats:
        if len(mats)>1:
            ops=[f"{m['DESCRICAO']} - {m['MARCA']}" for m in mats]
            sel=st.selectbox("Material", ops, key="selmat")
            mat=mats[ops.index(sel)]
        else:
            mat=mats[0]
        saldos,_=get_saldos()
        saldo_id=sum([v['SALDO'] for v in saldos.values() if v['ID']==id_mov.upper()])
        st.caption(f"{mat['DESCRICAO']} | {mat['TIPO']} {mat['QTD']:,.0f} | Estoque {saldo_id:,.0f}")

        with st.expander("LOTE / LOCAL / FAB / VAL", expanded=False):
            lotes=list(set([v['LOTE'] for v in saldos.values() if v['ID']==id_mov.upper() and v['DESCRICAO']==mat['DESCRICAO'] and v['SALDO']>0]))
            c1,c2,c3,c4=st.columns(4)
            with c1:
                if lotes:
                    sel_lote=st.selectbox("LOTE", lotes+["NOVO"], key="lote")
                    lote_final=st.text_input("NOVO LOTE", key="lote_novo") if sel_lote=="NOVO" else sel_lote
                else:
                    lote_final=st.text_input("LOTE", key="lote2")
            with c2: local_final=st.selectbox("LOCAL", LOCAIS, key="local")
            with c3: data_fab_mov=st.date_input("FAB", value=date.today(), key="dfab_mov")
            with c4:
                val_mov=st.number_input("VAL DIAS", min_value=1, max_value=3650, value=int(mat['VAL']), key="val_mov")
                data_val_mov=data_fab_mov + timedelta(days=val_mov)

        col_e,col_s,col_t=st.columns(3)
        with col_e:
            qtd_e=st.number_input("ENTRADA", min_value=0.0, value=0.0, step=1.0, key="qe")
            tot_e=qtd_e*mat['QTD']
        with col_s:
            qtd_s=st.number_input("SAIDA", min_value=0.0, value=0.0, step=1.0, key="qs")
            tot_s=qtd_s*mat['QTD']
        with col_t:
            if qtd_e>0: st.metric("TOTAL", f"{saldo_id+tot_e:,.0f}")
            elif qtd_s>0: st.metric("TOTAL", f"{saldo_id-tot_s:,.0f}")
            else: st.metric("TOTAL", f"{saldo_id:,.0f}")
            if 'data_val_mov' in locals(): st.caption(f"{data_fab_mov.strftime('%d/%m/%Y')} -> {data_val_mov.strftime('%d/%m/%Y')} | {val_mov}d")

        if qtd_e>0 or qtd_s>0:
            if not lote_final or str(lote_final).strip()=="": st.error("LOTE obrigatório")
            elif qtd_e>0 and qtd_s>0: st.warning("Só ENTRADA ou SAIDA")
            elif qtd_e>0:
                if st.button(f"CONFIRMAR ENTRADA {tot_e:,.0f}", type="primary", use_container_width=True):
                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    st.session_state.mov.append({"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_e,"TOTAL_QTD":tot_e,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO'],"QTD_POR_EMBALAGEM":mat['QTD'],"LOCAL_MOV":local_final,"TIPO":"ENTRADA","DATA_FABRICACAO":data_fab_mov.strftime("%d/%m/%Y"),"DATA_VALIDADE":data_val_mov.strftime("%d/%m/%Y"),"VALIDADE_DIAS":val_mov})
                    salvar(); st.rerun()
            elif qtd_s>0:
                if st.button(f"CONFIRMAR SAIDA {tot_s:,.0f}", type="primary", use_container_width=True):
                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    st.session_state.mov.append({"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],"PALETES":qtd_s,"TOTAL_QTD":tot_s,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,"TIPO_EMBALAGEM":mat['TIPO'],"QTD_POR_EMBALAGEM":mat['QTD'],"LOCAL_MOV":local_final,"TIPO":"SAIDA","DATA_FABRICACAO":data_fab_mov.strftime("%d/%m/%Y"),"DATA_VALIDADE":data_val_mov.strftime("%d/%m/%Y"),"VALIDADE_DIAS":val_mov})
                    salvar(); st.rerun()

with tab_est:
    st.subheader("ESTOQUE")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        totais={}
        for v in lista: totais[v['ID']]=totais.get(v['ID'],0)+v['SALDO']
        df['TOTAL_GERAL_ID']=df['ID'].apply(lambda x: totais.get(x,0))
        st.dataframe(df, use_container_width=True, height=500)
        st.metric("TOTAL GERAL", f"{df['SALDO'].sum():,.0f}")

with tab_graf:
    st.subheader("GRAFICO - QTD - NAO %")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista:
        st.info("Sem estoque")
    else:
        df=pd.DataFrame(lista)
        # Agrupa por ID + MARCA - QTD absoluta
        df_g=df.groupby(['ID','DESCRICAO','MARCA','TIPO'], as_index=False)['SALDO'].sum()

        # Texto em QTD absoluta - NAO %
        df_g['TEXTO_QTD']=df_g.apply(lambda r: f"{r['MARCA']}<br>{r['SALDO']:,.0f}", axis=1)
        df_g['QTD_LABEL']=df_g['SALDO'].apply(lambda x: f"{x:,.0f}")

        # GRAFICO 1 - COR POR ID - QTD
        fig1=px.bar(
            df_g,
            x='ID',
            y='SALDO',
            color='ID',
            text='QTD_LABEL',
            hover_data=['DESCRICAO','MARCA','TIPO','SALDO'],
            title=f"QTD POR ID - COR DIFERENTE POR ID - TOTAL {df_g['SALDO'].sum():,.0f} - {agora.strftime('%d/%m/%Y %H:%M:%S')}"
        )
        fig1.update_traces(textposition='outside')
        fig1.update_layout(yaxis_title="QTD", xaxis_title="ID", showlegend=True)
        st.plotly_chart(fig1, use_container_width=True)

        # GRAFICO 2 - COR POR MARCA - QTD - BARRAS EMPILHADAS POR ID
        fig2=px.bar(
            df_g,
            x='ID',
            y='SALDO',
            color='MARCA',
            text='TEXTO_QTD',
            barmode='stack',
            hover_data=['DESCRICAO','MARCA','SALDO','TIPO'],
            title=f"QTD POR ID E MARCA - EMPILHADO - MOSTRA MARCA E QTD - TOTAL {df_g['SALDO'].sum():,.0f}"
        )
        fig2.update_traces(textposition='inside')
        fig2.update_layout(yaxis_title="QTD", xaxis_title="ID")
        st.plotly_chart(fig2, use_container_width=True)

        # GRAFICO 3 - MARCA DETALHADO - QTD
        fig3=px.bar(
            df_g,
            x='MARCA',
            y='SALDO',
            color='ID',
            text='QTD_LABEL',
            barmode='group',
            hover_data=['DESCRICAO','ID','SALDO'],
            title=f"QTD POR MARCA - AGRUPADO POR ID - {df_g['SALDO'].sum():,.0f}"
        )
        fig3.update_traces(textposition='outside')
        fig3.update_layout(yaxis_title="QTD", xaxis_title="MARCA")
        st.plotly_chart(fig3, use_container_width=True)

        # TABELA - ID + MARCA + QTD + TOTAL
        st.markdown("ID | MARCA | QTD | TOTAL GERAL")
        df_tab=df_g[['ID','DESCRICAO','MARCA','TIPO','SALDO']].sort_values(by=['ID','MARCA']).copy()

        # Totais por ID
        totais_id=df_g.groupby('ID', as_index=False)['SALDO'].sum().rename(columns={'SALDO':'TOTAL_ID'})
        st.dataframe(df_tab, use_container_width=True)
        st.dataframe(totais_id, use_container_width=True)

        c1,c2,c3=st.columns(3)
        with c1: st.metric("TOTAL GERAL QTD", f"{df_g['SALDO'].sum():,.0f}")
        with c2: st.metric("IDs", f"{df_g['ID'].nunique()}")
        with c3: st.metric("MARCAS", f"{df_g['MARCA'].nunique()}")

with tab_hist:
    st.subheader("HISTORICO")
    if st.session_state.mov: st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

st.caption(f"{agora.strftime('%d/%m/%Y %H:%M:%S')} BRASILIA | CAD {len(st.session_state.cad)} MOV {len(st.session_state.mov)}")
