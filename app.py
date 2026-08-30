import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta, date
import plotly.express as px

st.set_page_config(page_title="REFORMA FIFO", layout="wide")
fuso = timezone(timedelta(hours=-3))

ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_EMAILS = "emails.csv"
LOCAIS = ["GALPAO","SALA ANEXA","OFICINA"]
TIPOS = ["PALETE","CAIXA","SACO","FARDO","BAG","TAMBOR","UNIDADE"]

def sf(v,d=0.0):
    try: return float(str(v).replace(",",".")) if str(v).strip()!="" else float(d)
    except: return float(d)

def carregar(p):
    if not os.path.exists(p): return []
    try: df=pd.read_csv(p,dtype=str,encoding='utf-8').fillna("")
    except: df=pd.read_csv(p,dtype=str,encoding='latin-1').fillna("")
    df.columns=[str(c).upper().strip() for c in df.columns]
    return df.to_dict('records')

def salvar():
    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False,encoding='utf-8')
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False,encoding='utf-8')

def get_saldos():
    saldos={}; carac={}
    for r in st.session_state.cad:
        idp=str(r.get('ID','')).upper().strip(); desc=str(r.get('DESCRICAO','')).upper().strip()
        if not idp or not desc: continue
        k=f"{idp}__{desc}__{str(r.get('MARCA','')).upper()}"
        if k not in carac:
            carac[k]={'ID':idp,'DESCRICAO':desc,'POSICAO':int(sf(r.get('POSICAO',0))),'MARCA':str(r.get('MARCA','')).upper(),'QTD':sf(r.get('QTD_POR_EMBALAGEM',1250)),'FAB':str(r.get('DATA_FABRICACAO',''))}
    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip(); desc=str(m.get('DESCRICAO','')).upper()
            if not idp: continue
            c=None
            for v in carac.values():
                if v['ID']==idp and v['DESCRICAO']==desc: c=v; break
            if not c:
                for v in carac.values():
                    if v['ID']==idp: c=v; break
            if not c: continue
            chave=f"{idp}__{desc}__{c['POSICAO']}__{c['MARCA']}"
            if chave not in saldos:
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'POSICAO':c['POSICAO'],'MARCA':c['MARCA'],'SALDO':0}
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=sf(m.get('TOTAL_QTD',0))
            else: saldos[chave]['SALDO']-=sf(m.get('TOTAL_QTD',0))
        except: continue
    return saldos, carac

def verifica_fifo():
    saldos, carac = get_saldos()
    avisos=[]
    # Agrupa por ID
    ids = set([v['ID'] for v in carac.values()])
    for id_ in ids:
        lista_pos = [v for v in carac.values() if v['ID']==id_]
        lista_pos = sorted(lista_pos, key=lambda x: x['POSICAO'])
        saldos_id = [s for s in saldos.values() if s['ID']==id_]
        # verifica se pos 1 zerou
        pos1 = [s for s in saldos_id if s['POSICAO']==1]
        saldo_pos1 = sum([s['SALDO'] for s in pos1]) if pos1 else 0

        # se tem cadastro pos 1 mas saldo 0 ou não tem saldo
        tem_pos1_cad = any([c['POSICAO']==1 for c in lista_pos])
        if tem_pos1_cad and saldo_pos1 <= 0:
            # acha proxima pos com saldo >0
            proximas = sorted([s for s in saldos_id if s['SALDO']>0], key=lambda x: x['POSICAO'])
            if proximas:
                prox = proximas[0]
                avisos.append(f"ID {id_} - POSIÇÃO 1 ZEROU! Próximo é POS {prox['POSICAO']} - {prox['DESCRICAO']} {prox['MARCA']} com {prox['SALDO']:,.0f}")
                # PASSA PROXIMO PARA NUMERO 1
                for j, r in enumerate(st.session_state.cad):
                    if str(r.get('ID','')).upper()==id_ and str(r.get('DESCRICAO','')).upper()==prox['DESCRICAO'] and int(sf(r.get('POSICAO',0)))==prox['POSICAO']:
                        st.session_state.cad[j]['POSICAO']=1
                        # o antigo pos 1 vira 9999 (fim da fila)
                        for k, r2 in enumerate(st.session_state.cad):
                            if str(r2.get('ID','')).upper()==id_ and int(sf(r2.get('POSICAO',0)))==1 and j!=k:
                                # se ainda tem outro com pos 1 (antigo zerado), manda pro fim
                                if sum([s['SALDO'] for s in saldos_id if s['DESCRICAO']==r2.get('DESCRICAO') and s['MARCA']==r2.get('MARCA')])<=0:
                                    st.session_state.cad[k]['POSICAO']=999
                salvar()
            else:
                if tem_pos1_cad:
                    avisos.append(f"🚨 ID {id_} - POSIÇÃO 1 ZEROU E NÃO TEM PRÓXIMO! REABASTECER!")

    return avisos

if 'ok' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD)
    st.session_state.mov=carregar(ARQ_MOV)
    st.session_state.ok=True
if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'log' not in st.session_state: st.session_state.log=False

if not st.session_state.log:
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        df_e=pd.read_csv(ARQ_EMAILS,dtype=str).fillna("")
        u=df_e[(df_e["EMAIL"].str.lower()==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s))]
        if not u.empty: st.session_state.log=True; st.rerun()
    st.stop()

# VERIFICA FIFO TODA VEZ QUE ABRE
avisos_fifo = verifica_fifo()
if avisos_fifo:
    for av in avisos_fifo:
        st.warning(av)
        st.toast(av)

agora=datetime.now(fuso)
st.sidebar.write(f"CAD:{len(st.session_state.cad)} MOV:{len(st.session_state.mov)}")
if st.sidebar.button("Sair"): salvar(); st.session_state.log=False; st.rerun()

tabs=st.tabs(["CADASTRO","ENTRADA / SAIDA - FIFO","ESTOQUE FIFO","GRAFICO","HISTORICO"])
tab_cad, tab_mov, tab_est, tab_graf, tab_hist = tabs

with tab_cad:
    st.subheader("CADASTRO COM POSIÇÃO - FIFO")
    id_in=st.text_input("ID", placeholder="Ex: 7", key="id_cad")
    with st.form("form_cad"):
        c1,c2,c3=st.columns([1,3,1])
        with c1: id_f=st.text_input("ID", value=id_in.upper() if id_in else "")
        with c2: desc=st.text_input("DESCRIÇÃO")
        with c3: pos=st.number_input("POSIÇÃO", min_value=1, max_value=9999, value=1, step=1)
        c4,c5=st.columns(2)
        with c4: marca=st.text_input("MARCA")
        with c5: qtd=st.number_input("QTD/EMB", value=1250.0)
        if st.form_submit_button("CADASTRAR", type="primary", use_container_width=True):
            if id_f and desc:
                st.session_state.cad.append({"ID":id_f.upper().strip(),"POSICAO":pos,"DESCRICAO":desc.upper(),"MARCA":marca.upper() or "SEM MARCA","QTD_POR_EMBALAGEM":qtd,"DATA_FABRICACAO":date.today().strftime("%d/%m/%Y")})
                salvar(); st.rerun()

    if st.session_state.cad:
        df = pd.DataFrame(st.session_state.cad)
        df['POSICAO']=df['POSICAO'].apply(lambda x: int(sf(x,0)))
        df=df.sort_values(['ID','POSICAO'])

        filtro1 = st.checkbox("✅ SÓ DESCRIÇÃO COM 1 NA FRENTE", value=False)
        if filtro1:
            df = df[df['DESCRICAO'].astype(str).str.startswith('1')]
            st.info(f"{len(df)} materiais com 1 na frente - SELECIONADOS")

        st.dataframe(df, use_container_width=True, height=300)

        st.markdown("### LIXEIRINHA 🗑️ - FIFO ATUALIZA")
        for i, reg in enumerate(df.itertuples()):
            c1,c2,c3,c4,c5,c6 = st.columns([0.5,1,3,1,1,0.8])
            c1.write(f"{reg.POSICAO}")
            c2.write(f"{reg.ID}")
            c3.write(f"{reg.DESCRICAO}")
            c4.write(f"{reg.MARCA}")
            c5.write(f"{reg.QTD_POR_EMBALAGEM}")
            if c6.button("🗑️", key=f"del_{i}_{reg.Index}"):
                st.session_state.cad.pop(reg.Index)
                salvar(); st.rerun()

with tab_mov:
    st.subheader("SAIDA FIFO - SEMPRE PEGA POSIÇÃO 1")
    id_mov=st.text_input("ID FIFO", placeholder="Digite ID", key="id_mov")
    if id_mov:
        saldos,carac = get_saldos()
        lista = [v for v in carac.values() if v['ID']==id_mov.upper()]
        lista = sorted(lista, key=lambda x: x['POSICAO'])
        saldos_id = [s for s in saldos.values() if s['ID']==id_mov.upper()]
        saldos_id = sorted(saldos_id, key=lambda x: x['POSICAO'])

        if not lista: st.error("ID não cadastrado")
        else:
            # MOSTRA FILA FIFO
            st.markdown("#### FILA FIFO")
            for s in saldos_id:
                cor = "🟢" if s['SALDO']>0 else "🔴"
                if s['POSICAO']==1: cor="⭐ POS 1"
                st.write(f"{cor} POS {s['POSICAO']} | {s['DESCRICAO']} {s['MARCA']} | SALDO {s['SALDO']:,.0f}")

            # SEMPRE USA POS 1 PARA SAIDA
            pos1_saldo = [s for s in saldos_id if s['POSICAO']==1 and s['SALDO']>0]
            if pos1_saldo:
                mat_pos1 = pos1_saldo[0]
                st.success(f"SAIDA VAI SER DA POSIÇÃO 1: {mat_pos1['DESCRICAO']} - SALDO {mat_pos1['SALDO']:,.0f}")
                mat_cad = [c for c in lista if c['POSICAO']==1 and c['DESCRICAO']==mat_pos1['DESCRICAO']][0]

                qtd_s=st.number_input("QTD PALETES SAIDA (FIFO POS 1)", min_value=0.0, value=0.0, step=1.0, key="qs")
                if qtd_s>0:
                    tot = qtd_s * mat_cad['QTD']
                    if tot > mat_pos1['SALDO']:
                        st.error(f"SALDO INSUFICIENTE POS 1! Tem {mat_pos1['SALDO']:,.0f} e quer tirar {tot:,.0f}")
                    else:
                        if st.button(f"CONFIRMAR SAIDA FIFO POS 1 - {tot:,.0f}", type="primary", use_container_width=True):
                            agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                            st.session_state.mov.append({"ID":id_mov.upper(),"DESCRICAO":mat_pos1['DESCRICAO'],"POSICAO":1,"LOTE":"FIFO","MARCA":mat_pos1['MARCA'],"PALETES":qtd_s,"TOTAL_QTD":tot,"DATA_HORA":agora_str,"TIPO":"SAIDA","QTD_POR_EMBALAGEM":mat_cad['QTD']})
                            salvar()
                            # VERIFICA SE ZEROU
                            novo_saldo = mat_pos1['SALDO'] - tot
                            if novo_saldo <= 0:
                                st.warning(f"POSIÇÃO 1 ZEROU! ID {id_mov.upper()} - {mat_pos1['DESCRICAO']} ACABOU!")
                                st.toast(f"🚨 POS 1 ZEROU! Próximo vai virar POS 1")
                            st.rerun()
            else:
                st.error("POSIÇÃO 1 ZERADA! Sistema já vai passar próximo para POS 1")
                # Força verificação
                verifica_fifo()
                st.rerun()

            st.divider()
            st.markdown("#### ENTRADA - ESCOLHE POSIÇÃO")
            mats_sorted = sorted(lista, key=lambda x: x['POSICAO'])
            ops=[f"POS {m['POSICAO']} | {m['DESCRICAO']} - {m['MARCA']}" for m in mats_sorted]
            sel=st.selectbox("Material entrada", ops, key="selmat")
            mat=mats_sorted[ops.index(sel)]
            qtd_e=st.number_input("ENTRADA PALETES", min_value=0.0, value=0.0, step=1.0, key="qe")
            if qtd_e>0 and st.button(f"ENTRADA POS {mat['POSICAO']} - {qtd_e*mat['QTD']:,.0f}", use_container_width=True):
                agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                st.session_state.mov.append({"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"POSICAO":mat['POSICAO'],"LOTE":"FIFO","MARCA":mat['MARCA'],"PALETES":qtd_e,"TOTAL_QTD":qtd_e*mat['QTD'],"DATA_HORA":agora_str,"TIPO":"ENTRADA","QTD_POR_EMBALAGEM":mat['QTD']})
                salvar(); st.rerun()

with tab_est:
    st.subheader("ESTOQUE FIFO - POS 1 É O QUE USA")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista).sort_values(['ID','POSICAO'])
        st.dataframe(df, use_container_width=True, height=500)
        # AVISO FIFO
        for id_ in df['ID'].unique():
            df_id = df[df['ID']==id_].sort_values('POSICAO')
            if not df_id.empty:
                pos1 = df_id[df_id['POSICAO']==1]
                if not pos1.empty:
                    st.success(f"ID {id_} - USANDO POS 1: {pos1.iloc[0]['DESCRICAO']} - {pos1.iloc[0]['SALDO']:,.0f}")
    else: st.info("Sem estoque")

with tab_graf:
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        df=pd.DataFrame(lista)
        df['TEXTO']=df['SALDO'].apply(lambda x: f"{x:,.0f}")
        fig=px.bar(df.sort_values('POSICAO'), x='SALDO', y='DESCRICAO', color='MARCA', text='TEXTO', orientation='h', title="FIFO por POSIÇÃO")
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

with tab_hist:
    if st.session_state.mov:
        st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

st.caption(f"{agora.strftime('%d/%m/%Y %H:%M:%S')} | FIFO ATIVO | POS 1 ZEROU = PROXIMO VIRA POS 1")
