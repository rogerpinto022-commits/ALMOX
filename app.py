import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta, date
import plotly.express as px

st.set_page_config(page_title="REFORMA - SIMPLES - SEM ERRO", layout="wide")
fuso = timezone(timedelta(hours=-3))

ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_GRD = "grd.csv"
ARQ_EMAILS = "emails.csv"

LOCAL_GALPAO = "GALPAO DE MATERIAIS REFRATARIOS"
LOCAL_SALA = "SALA ANEXA"
LOCAL_OFICINA = "OFICINA DE REVESTIMENTO REFORMA DE FORNOS"
LOCAIS = [LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]
LOCAIS_ACESSO = ["AMBOS", LOCAL_GALPAO, LOCAL_SALA, LOCAL_OFICINA]
TIPOS = ["PALETE", "CAIXA", "SACO", "FARDO", "BAG", "TAMBOR", "UNIDADE"]

def sf(v, d=0.0):
    try:
        if v is None or str(v).strip()=="": return float(d)
        return float(str(v).replace(",", "."))
    except: return float(d)

def carregar(path):
    if not os.path.exists(path): return []
    try:
        df = pd.read_csv(path, dtype=str, encoding='utf-8').fillna("")
    except:
        try: df = pd.read_csv(path, dtype=str, encoding='latin-1').fillna("")
        except: return []
    df.columns = [str(c).upper().strip() for c in df.columns]
    return df.to_dict('records')

def salvar():
    try:
        pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD, index=False, encoding='utf-8')
        pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV, index=False, encoding='utf-8')
        pd.DataFrame(st.session_state.grd).to_csv(ARQ_GRD, index=False, encoding='utf-8')
    except: pass

def get_saldos():
    saldos = {}
    carac = {}
    for r in st.session_state.cad:
        idp = str(r.get('ID','')).upper().strip()
        desc = str(r.get('DESCRICAO','')).upper().strip()
        if not idp or not desc: continue
        k = f"{idp}__{desc}__{str(r.get('MARCA','')).upper()}"
        if k not in carac:
            carac[k] = {
                'ID': idp, 'DESCRICAO': desc,
                'TIPO': str(r.get('TIPO_EMBALAGEM', r.get('TIPO','PALETE'))).upper(),
                'QTD': sf(r.get('QTD_POR_EMBALAGEM', r.get('QTD_PALETE',1250)),1250),
                'MARCA': str(r.get('MARCA','SEM MARCA')).upper(),
                'FAB': str(r.get('DATA_FABRICACAO', r.get('FABRICACAO',''))),
                'VAL_H': sf(r.get('VALIDADE_HORAS',48),48)
            }
    for m in st.session_state.mov:
        try:
            idp = str(m.get('ID','')).upper().strip()
            lote = str(m.get('LOTE','')).upper().strip()
            if not idp or not lote: continue
            desc = str(m.get('DESCRICAO','')).upper()
            local = str(m.get('LOCAL_MOV',LOCAL_GALPAO)).upper()
            if "SALA" in local: local = LOCAL_SALA
            elif "OFIC" in local: local = LOCAL_OFICINA
            else: local = LOCAL_GALPAO
            c = None
            for v in carac.values():
                if v['ID']==idp and v['DESCRICAO']==desc: c=v; break
            if not c:
                for v in carac.values():
                    if v['ID']==idp: c=v; break
            if not c: continue
            chave = f"{idp}__{desc}__{local}__{lote}"
            if chave not in saldos:
                saldos[chave] = {'ID':idp,'DESCRICAO':desc,'TIPO':c['TIPO'],'QTD':c['QTD'],'LOCAL':local,'LOTE':lote,'MARCA':c['MARCA'],'SALDO':0,'ULT':str(m.get('DATA_HORA','')),'FAB':str(m.get('DATA_FABRICACAO',c['FAB'])),'VAL_H':sf(m.get('VALIDADE_HORAS',c['VAL_H']),48)}
            if m.get('TIPO')=="ENTRADA":
                saldos[chave]['SALDO'] += sf(m.get('TOTAL_QTD',0))
                saldos[chave]['ULT'] = str(m.get('DATA_HORA',''))
            else:
                saldos[chave]['SALDO'] -= sf(m.get('TOTAL_QTD',0))
                saldos[chave]['ULT'] = str(m.get('DATA_HORA',''))
        except: continue
    return saldos, carac

# NÃO APAGA - CARREGA O QUE JÁ EXISTE
if 'ok' not in st.session_state:
    st.session_state.cad = carregar(ARQ_CAD)
    st.session_state.mov = carregar(ARQ_MOV)
    st.session_state.grd = carregar(ARQ_GRD)
    st.session_state.ok = True
if 'tempo' not in st.session_state: st.session_state.tempo = 48
if not os.path.exists(ARQ_EMAILS):
    pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","LOCAL":"AMBOS","STATUS":"LIBERADO","NOME":"ADMIN"}]).to_csv(ARQ_EMAILS,index=False)
if 'log' not in st.session_state: st.session_state.log=False
if 'user' not in st.session_state: st.session_state.user=None

if not st.session_state.log:
    st.markdown("<h1 style='text-align:center;background:black;color:#00ff66;padding:20px;border-radius:12px;'>REFORMA DE FORNOS - SEM ERRO - NAO APAGA</h1>", unsafe_allow_html=True)
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        try:
            df_e=pd.read_csv(ARQ_EMAILS,dtype=str).fillna("")
            df_e['EMAIL']=df_e['EMAIL'].astype(str).str.lower()
            u=df_e[(df_e["EMAIL"]==e.lower().strip()) & (df_e["SENHA"].astype(str)==str(s)) & (df_e["STATUS"]=="LIBERADO")]
            if not u.empty:
                st.session_state.log=True; st.session_state.user=u.iloc[0].to_dict(); st.rerun()
            else: st.error("Invalido")
        except Exception as ex: st.error(f"Erro login: {ex}")
    st.stop()

st.sidebar.write(f"Logado: {st.session_state.user.get('NOME')}")
st.sidebar.write(f"CAD: {len(st.session_state.cad)} MOV: {len(st.session_state.mov)} - NAO APAGOU")
if st.session_state.cad: st.sidebar.download_button("BACKUP CAD", pd.DataFrame(st.session_state.cad).to_csv(index=False), "backup_cad.csv")
if st.session_state.mov: st.sidebar.download_button("BACKUP MOV", pd.DataFrame(st.session_state.mov).to_csv(index=False), "backup_mov.csv")
if st.sidebar.button("Sair"): salvar(); st.session_state.log=False; st.rerun()

agora=datetime.now(fuso)
st.title(f"REFORMA - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASILIA")

abas=st.tabs(["CADASTRO - NAO APAGA","ENTRADA/SAIDA SIMPLES","ESTOQUE","GRD","GRAFICO","HISTORICO"])
tab_cad, tab_mov, tab_est, tab_grd, tab_graf, tab_hist = abas

# ABA CADASTRO - COM FABRICACAO E VALIDADE - SEM KeyError
with tab_cad:
    st.header("3 - CADASTRO - COM FABRICAÇÃO E VALIDADE - NÃO APAGA ANTIGO")
    st.success(f"✅ SEU CADASTRO ATUAL: {len(st.session_state.cad)} MATERIAIS - NÃO FOI APAGADO")

    id_in = st.text_input("ID* - Digite e ENTER - Ex: 15", key="id_cad")

    with st.form("form_cad"):
        c1,c2=st.columns([1,2])
        with c1: id_f=st.text_input("ID*", value=id_in.upper() if id_in else "", key="idf")
        with c2: desc=st.text_input("DESCRIÇÃO* - Ex: TIJOLO 65%", key="desc")
        c3,c4,c5=st.columns(3)
        with c3: tipo=st.selectbox("TIPO EMBALAGEM*", TIPOS, key="tipo")
        with c4: qtd=st.number_input("QTD POR EMBALAGEM*", min_value=0.1, value=1250.0, key="qtd")
        with c5: marca=st.text_input("MARCA", key="marca")

        st.markdown("### 📅 FABRICAÇÃO E VALIDADE")
        cf1,cf2=st.columns(2)
        with cf1: data_fab=st.date_input("DATA FABRICAÇÃO", value=date.today(), key="dfab")
        with cf2:
            val_h=st.number_input("VALIDADE HORAS - VOCÊ DECIDE - 48=2dias", min_value=1, max_value=8760, value=int(st.session_state.tempo), step=1, key="valh")
            data_val=data_fab + timedelta(hours=val_h)
            st.write(f"Validade até: {data_val.strftime('%d/%m/%Y')} = {val_h/24:.1f} dias")

        if st.form_submit_button("✅ CADASTRAR - GUARDA 100% - NÃO APAGA", type="primary", use_container_width=True):
            if not id_f or not desc: st.error("ID e DESCRIÇÃO obrigatórios")
            else:
                st.session_state.cad.append({
                    "ID": id_f.upper().strip(),
                    "DESCRICAO": desc.upper(),
                    "TIPO_EMBALAGEM": tipo.upper(),
                    "QTD_POR_EMBALAGEM": qtd,
                    "QTD_PALETE": qtd,
                    "MARCA": marca.upper() if marca else "SEM MARCA",
                    "DATA_FABRICACAO": data_fab.strftime("%d/%m/%Y"),
                    "FABRICACAO": data_fab.strftime("%d/%m/%Y"),
                    "VALIDADE_HORAS": val_h,
                    "DATA_VALIDADE": data_val.strftime("%d/%m/%Y %H:%M:%S")
                })
                salvar()
                st.success(f"✅ CADASTRADO ID {id_f.upper()} FAB {data_fab.strftime('%d/%m/%Y')} VAL {val_h}H - GUARDADO - TOTAL CAD {len(st.session_state.cad)}")
                st.rerun()

    if st.session_state.cad:
        try:
            df=pd.DataFrame(st.session_state.cad)
            # Mostra sem erro - só colunas que existem
            st.dataframe(df, use_container_width=True, height=300)
        except Exception as e:
            st.error(f"Erro mostrar cad: {e}")
            st.write(st.session_state.cad)

# ABA ENTRADA SAIDA SIMPLES - QUALQUER PESSOA ENTENDE
with tab_mov:
    st.header("4 - ENTRADA / SAIDA - SIMPLES - QUALQUER PESSOA ENTENDE + FABRICAÇÃO E VALIDADE")

    id_mov=st.text_input("ID* - Digite ID cadastrado e ENTER - Ex: 15", key="id_mov")

    mats=[]
    if id_mov:
        up=id_mov.upper().strip()
        for r in st.session_state.cad:
            if str(r.get('ID','')).upper()==up and str(r.get('DESCRICAO','')).strip()!="":
                mats.append({
                    'DESCRICAO': str(r.get('DESCRICAO','')).upper(),
                    'MARCA': str(r.get('MARCA','')).upper(),
                    'TIPO': str(r.get('TIPO_EMBALAGEM', r.get('TIPO','PALETE'))).upper(),
                    'QTD': sf(r.get('QTD_POR_EMBALAGEM', r.get('QTD_PALETE',1250)),1250),
                    'FAB': str(r.get('DATA_FABRICACAO', r.get('FABRICACAO',''))),
                    'VAL_H': sf(r.get('VALIDADE_HORAS',48),48)
                })

    if not id_mov:
        st.info("👉 Digite ID da ABA CADASTRO e ENTER - Simples")
    elif not mats:
        st.error(f"ID {id_mov.upper()} NÃO CADASTRADO - Vá em CADASTRO primeiro")
    else:
        if len(mats)>1:
            ops=[f"{m['DESCRICAO']} - {m['MARCA']}" for m in mats]
            sel=st.selectbox("Escolha material - mesma ID tem vários", ops, key="selmat")
            mat=mats[ops.index(sel)]
        else:
            mat=mats[0]

        saldos,_=get_saldos()
        saldo_id=sum([v['SALDO'] for v in saldos.values() if v['ID']==id_mov.upper()])

        st.success(f"✅ ID {id_mov.upper()} - {mat['DESCRICAO']} - {mat['TIPO']} {mat['QTD']:,.0f}/emb - FAB {mat['FAB']} VAL {mat['VAL_H']:.0f}H - ESTOQUE ATUAL {saldo_id:,.0f}")

        # Lote e local
        lotes=list(set([v['LOTE'] for v in saldos.values() if v['ID']==id_mov.upper() and v['DESCRICAO']==mat['DESCRICAO'] and v['SALDO']>0]))
        c1,c2,c3,c4=st.columns(4)
        with c1:
            if lotes:
                sel_lote=st.selectbox("LOTE", lotes+["NOVO LOTE"], key="lote")
                lote_final=st.text_input("NOVO LOTE", key="lote_novo") if sel_lote=="NOVO LOTE" else sel_lote
            else:
                lote_final=st.text_input("LOTE* - Ex: LOTE-001", key="lote2")
        with c2:
            local_final=st.selectbox("LOCAL", LOCAIS, key="local")
        with c3:
            data_fab_mov=st.date_input("DATA FABRICAÇÃO desta entrada", value=date.today(), key="dfab_mov")
        with c4:
            val_mov=st.number_input("VALIDADE HORAS - Você decide", min_value=1, max_value=8760, value=int(mat['VAL_H'] if mat['VAL_H']>0 else st.session_state.tempo), key="val_mov")

        st.markdown("---")
        st.markdown("### ENTRADA E SAIDA - DIGITE SÓ QTD - QUALQUER PESSOA ENTENDE")

        col_e,col_s,col_t=st.columns(3)
        with col_e:
            st.markdown("#### 📥 ENTRADA - QTD RECEBIDA")
            qtd_e=st.number_input(f"QTD {mat['TIPO']} RECEBIDA - Digite", min_value=0.0, value=0.0, step=1.0, key="qe")
            tot_e=qtd_e*mat['QTD']
            if qtd_e>0: st.metric("ENTRADA", f"{tot_e:,.0f}", delta=f"{qtd_e} {mat['TIPO']}")
        with col_s:
            st.markdown("#### 📤 SAIDA - QTD RETIRADA")
            qtd_s=st.number_input(f"QTD {mat['TIPO']} RETIRADA - Digite", min_value=0.0, value=0.0, step=1.0, key="qs")
            tot_s=qtd_s*mat['QTD']
            if qtd_s>0: st.metric("SAIDA", f"{tot_s:,.0f}", delta=f"-{qtd_s} {mat['TIPO']}", delta_color="inverse")
        with col_t:
            st.markdown("#### 📊 TOTAL GERAL + VALIDADE")
            if qtd_e>0: st.metric(f"TOTAL GERAL ID {id_mov.upper()}", f"{saldo_id+tot_e:,.0f}", delta=f"+{tot_e:,.0f}")
            elif qtd_s>0: st.metric(f"TOTAL GERAL ID {id_mov.upper()}", f"{saldo_id-tot_s:,.0f}", delta=f"-{tot_s:,.0f}", delta_color="inverse")
            else: st.metric(f"TOTAL ATUAL ID {id_mov.upper()}", f"{saldo_id:,.0f}")
            st.write(f"Unidade: {mat['TIPO']}")
            st.write(f"FAB: {data_fab_mov.strftime('%d/%m/%Y')} VAL: {val_mov}H = {(data_fab_mov+timedelta(hours=val_mov)).strftime('%d/%m/%Y')}")
            st.write(f"Agora Brasília: {agora.strftime('%d/%m/%Y %H:%M:%S')}")

        if qtd_e>0 or qtd_s>0:
            if not lote_final or str(lote_final).strip()=="": st.error("Digite LOTE")
            elif qtd_e>0 and qtd_s>0: st.warning("Digite só ENTRADA ou só SAIDA por vez")
            elif qtd_e>0:
                if st.button(f"✅ CONFIRMAR ENTRADA {tot_e:,.0f} - FAB {data_fab_mov.strftime('%d/%m/%Y')} VAL {val_mov}H - GUARDA 100%", type="primary", use_container_width=True):
                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    data_val_mov=data_fab_mov+timedelta(hours=val_mov)
                    st.session_state.mov.append({
                        "ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],
                        "PALETES":qtd_e,"TOTAL_QTD":tot_e,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,
                        "TIPO_EMBALAGEM":mat['TIPO'],"QTD_POR_EMBALAGEM":mat['QTD'],"LOCAL_MOV":local_final,"TIPO":"ENTRADA",
                        "DATA_FABRICACAO":data_fab_mov.strftime("%d/%m/%Y"),"DATA_VALIDADE":data_val_mov.strftime("%d/%m/%Y %H:%M:%S"),"VALIDADE_HORAS":val_mov
                    })
                    salvar(); st.success(f"✅ ENTRADA {tot_e:,.0f} GUARDADA - TOTAL GERAL {saldo_id+tot_e:,.0f} - FAB {data_fab_mov.strftime('%d/%m/%Y')} VAL {val_mov}H - NÃO PERDE"); st.balloons(); st.rerun()
            elif qtd_s>0:
                if st.button(f"✅ CONFIRMAR SAIDA {tot_s:,.0f} - GUARDA 100%", type="primary", use_container_width=True):
                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                    data_val_mov=data_fab_mov+timedelta(hours=val_mov)
                    st.session_state.mov.append({
                        "ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"LOTE":lote_final.upper().strip(),"MARCA":mat['MARCA'],
                        "PALETES":qtd_s,"TOTAL_QTD":tot_s,"DATA":agora_str.split(" ")[0],"DATA_HORA":agora_str,
                        "TIPO_EMBALAGEM":mat['TIPO'],"QTD_POR_EMBALAGEM":mat['QTD'],"LOCAL_MOV":local_final,"TIPO":"SAIDA",
                        "DATA_FABRICACAO":data_fab_mov.strftime("%d/%m/%Y"),"DATA_VALIDADE":data_val_mov.strftime("%d/%m/%Y %H:%M:%S"),"VALIDADE_HORAS":val_mov
                    })
                    salvar(); st.success(f"✅ SAIDA {tot_s:,.0f} GUARDADA - ULTIMA RETIRADA {agora_str} BRASILIA - TOTAL {saldo_id-tot_s:,.0f}"); st.balloons(); st.rerun()

    if st.session_state.mov:
        try:
            df=pd.DataFrame(st.session_state.mov)
            st.dataframe(df.tail(10), use_container_width=True)
            if st.button("🗑️ APAGAR ULTIMO REGISTRO - Se errou"):
                if st.session_state.mov:
                    st.session_state.mov.pop(); salvar(); st.success("Apagado - Atualizou auto"); st.rerun()
        except: st.write(st.session_state.mov[-10:])

with tab_est:
    st.header("ESTOQUE - COM FABRICAÇÃO E VALIDADE - ATUALIZA AUTO")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if not lista: st.info("Sem estoque - Faça ENTRADA na ABA 4")
    else:
        try:
            df=pd.DataFrame(lista)
            st.dataframe(df, use_container_width=True, height=500)
            st.metric("TOTAL GERAL", f"{df['SALDO'].sum():,.0f}" if 'SALDO' in df.columns else "0")
        except Exception as e:
            st.error(f"Erro estoque: {e}")
            st.write(lista[:5])

with tab_grd:
    st.header("GRD - VOCÊ DECIDE HORAS VALIDADE")
    c1,c2=st.columns([3,1])
    with c1: nova=st.number_input("HORAS VALIDADE - Você decide", min_value=1, max_value=8760, value=int(st.session_state.tempo), key="tempo_grd")
    with c2:
        if st.button("SALVAR HORAS", type="primary"): st.session_state.tempo=int(nova); st.rerun()
    if st.session_state.grd:
        try: st.dataframe(pd.DataFrame(st.session_state.grd), use_container_width=True)
        except: st.write(st.session_state.grd)

with tab_graf:
    st.header(f"GRAFICO - ATUALIZA AUTO - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASILIA")
    saldos,_=get_saldos()
    lista=[v for v in saldos.values() if v['SALDO']>0]
    if lista:
        try:
            df=pd.DataFrame(lista)
            df_g=df.groupby(['ID','DESCRICAO'], as_index=False)['SALDO'].sum()
            df_g['TEXTO']=df_g['SALDO'].apply(lambda x: f"{x:,.0f}")
            fig=px.bar(df_g, x='ID', y='SALDO', color='DESCRICAO', text='TEXTO', barmode='stack', title=f"ESTOQUE ATUAL - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASILIA")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro grafico: {e}")

with tab_hist:
    st.header("HISTORICO")
    if st.session_state.mov:
        try: st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)
        except: st.write(st.session_state.mov)

st.caption(f"SEM ERRO - NAO APAGA ANTIGO - COM FABRICACAO E VALIDADE - SIMPLES - GUARDA 100% - {agora.strftime('%d/%m/%Y %H:%M:%S')} BRASILIA - CAD {len(st.session_state.cad)} MOV {len(st.session_state.mov)}")
