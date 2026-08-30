import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
import plotly.express as px

st.set_page_config(page_title="REFORMA DE FORNOS - MATERIAIS REFRATARIOS", layout="wide")
fuso = timezone(timedelta(hours=-3))

ARQ_CAD = "cadastro_refratario.csv"
ARQ_MOV = "movimentacao.csv"
ARQ_EMAILS = "emails.csv"

def sf(v,d=0.0):
    try: return float(str(v).replace(",",".")) if str(v).strip()!="" else float(d)
    except: return float(d)

def carregar(p):
    if not os.path.exists(p): return []
    try: df=pd.read_csv(p,dtype=str,encoding='utf-8').fillna("")
    except: df=pd.read_csv(p,dtype=str,encoding='latin-1').fillna("")
    df.columns=[str(c).upper().strip() for c in df.columns]
    if 'POSICAO' not in df.columns: df['POSICAO']=range(1,len(df)+1)
    if 'ORDEM' not in df.columns: df['ORDEM']=df['POSICAO']
    if 'LOTE' not in df.columns: df['LOTE']=''
    return df.to_dict('records')

def carregar_emails():
    if not os.path.exists(ARQ_EMAILS):
        df=pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","NOME":"ADMIN","STATUS":"LIBERADO","CADASTRO":"SIM","ENTRADA":"SIM","SAIDA":"SIM","ESTOQUE":"SIM","GRAFICO":"SIM","HISTORICO":"SIM","ADMIN":"SIM"}])
        df.to_csv(ARQ_EMAILS,index=False,encoding='utf-8')
        return df
    try: df=pd.read_csv(ARQ_EMAILS,dtype=str,encoding='utf-8').fillna("")
    except: df=pd.read_csv(ARQ_EMAILS,dtype=str,encoding='latin-1').fillna("")
    df.columns=[c.upper().strip() for c in df.columns]
    mask_admin = df["EMAIL"].str.lower()=="admin@admin.com"
    if mask_admin.any():
        df.loc[mask_admin, "STATUS"]="LIBERADO"
        df.loc[mask_admin, "SENHA"]="admin"
        df.loc[mask_admin, "ADMIN"]="SIM"
    else:
        novo_admin=pd.DataFrame([{"EMAIL":"admin@admin.com","SENHA":"admin","NOME":"ADMIN","STATUS":"LIBERADO","CADASTRO":"SIM","ENTRADA":"SIM","SAIDA":"SIM","ESTOQUE":"SIM","GRAFICO":"SIM","HISTORICO":"SIM","ADMIN":"SIM"}])
        df=pd.concat([df,novo_admin],ignore_index=True)
    df.to_csv(ARQ_EMAILS,index=False,encoding='utf-8')
    return df

def salvar():
    pd.DataFrame(st.session_state.cad).to_csv(ARQ_CAD,index=False,encoding='utf-8')
    pd.DataFrame(st.session_state.mov).to_csv(ARQ_MOV,index=False,encoding='utf-8')

def get_saldos_ordinal():
    saldos={}
    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip()
            desc=str(m.get('DESCRICAO','')).upper().strip()
            lote=str(m.get('LOTE','SEM LOTE')).upper().strip()
            ordem=int(sf(m.get('ORDEM', m.get('POSICAO',1)),1))
            if not idp or not lote: continue
            chave=f"{idp}__{desc}__{lote}__{ordem}"
            if chave not in saldos:
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'LOTE':lote,'ORDEM':ordem,'POSICAO':ordem,'MARCA':str(m.get('MARCA','')), 'SALDO':0, 'QTD_EMB':sf(m.get('QTD_POR_EMBALAGEM',1250))}
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=sf(m.get('TOTAL_QTD',0))
            else: saldos[chave]['SALDO']-=sf(m.get('TOTAL_QTD',0))
        except: continue
    return saldos

def reorganiza_fifo_pos1(id_):
    saldos = get_saldos_ordinal()
    lotes_com_saldo = [s for s in saldos.values() if s['ID']==id_ and s['SALDO']>0]
    lotes_com_saldo = sorted(lotes_com_saldo, key=lambda x: x['ORDEM'])
    if not lotes_com_saldo: return None
    if any(s['ORDEM']==1 for s in lotes_com_saldo): return lotes_com_saldo[0]
    mapa_nova_ordem = {}
    for idx, lote_info in enumerate(lotes_com_saldo, start=1):
        mapa_nova_ordem[lote_info['LOTE']] = idx
    for j in range(len(st.session_state.mov)):
        if str(st.session_state.mov[j].get('ID','')).upper()==id_:
            lote_mov=str(st.session_state.mov[j].get('LOTE','')).upper()
            if lote_mov in mapa_nova_ordem:
                st.session_state.mov[j]['ORDEM']=mapa_nova_ordem[lote_mov]
                st.session_state.mov[j]['POSICAO']=mapa_nova_ordem[lote_mov]
    salvar()
    lotes_com_saldo = sorted([s for s in get_saldos_ordinal().values() if s['ID']==id_ and s['SALDO']>0], key=lambda x: x['ORDEM'])
    return lotes_com_saldo[0] if lotes_com_saldo else None

def tem_permissao(func):
    user = st.session_state.get('user',{})
    if not user: return False
    if str(user.get('EMAIL','')).lower()=="admin@admin.com": return True
    if str(user.get('ADMIN','')).upper()=='SIM': return True
    return str(user.get(func,'')).upper()=='SIM'

if 'ok' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD)
    st.session_state.mov=carregar(ARQ_MOV)
    st.session_state.ok=True
if 'log' not in st.session_state: st.session_state.log=False
if 'user' not in st.session_state: st.session_state.user=None

if not st.session_state.log:
    st.markdown("<h1 style='text-align:center;'>REFORMA DE FORNOS - MATERIAIS REFRATARIOS</h1>", unsafe_allow_html=True)
    df_emails=carregar_emails()
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("ENTRAR",type="primary", use_container_width=True):
        e_low=e.lower().strip()
        if e_low=="admin@admin.com" and str(s)=="admin":
            st.session_state.log=True
            st.session_state.user={"EMAIL":"admin@admin.com","SENHA":"admin","NOME":"ADMIN","STATUS":"LIBERADO","CADASTRO":"SIM","ENTRADA":"SIM","SAIDA":"SIM","ESTOQUE":"SIM","GRAFICO":"SIM","HISTORICO":"SIM","ADMIN":"SIM"}
            st.rerun()
        u=df_emails[(df_emails["EMAIL"].str.lower()==e_low) & (df_emails["SENHA"].astype(str)==str(s)) & (df_emails["STATUS"].str.upper()=="LIBERADO")]
        if not u.empty:
            st.session_state.log=True
            st.session_state.user=u.iloc[0].to_dict()
            st.rerun()
        else: st.error("Acesso negado")
    st.stop()

user=st.session_state.user
agora=datetime.now(fuso)

saldos_geral = get_saldos_ordinal()
for id_ in set([s['ID'] for s in saldos_geral.values()]):
    lotes_id = [s for s in saldos_geral.values() if s['ID']==id_ and s['SALDO']>0]
    lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
    if lotes_id and not any(s['ORDEM']==1 for s in lotes_id):
        reorganiza_fifo_pos1(id_)

st.sidebar.markdown("### REFORMA DE FORNOS")
st.sidebar.markdown("**MATERIAIS REFRATARIOS**")
st.sidebar.write(f"👤 {user.get('NOME')}")
if st.sidebar.button("Sair"): salvar(); st.session_state.log=False; st.session_state.user=None; st.rerun()

abas_disponiveis=[]
mapa_abas={"CADASTRO":"CADASTRO","ENTRADA / SAIDA FIFO":"ENTRADA","ESTOQUE":"ESTOQUE","GRAFICO POS 1":"GRAFICO","HISTORICO":"HISTORICO","USUARIOS":"ADMIN"}
for nome_aba, permissao in mapa_abas.items():
    if nome_aba=="ENTRADA / SAIDA FIFO":
        if tem_permissao("ENTRADA") or tem_permissao("SAIDA"): abas_disponiveis.append(nome_aba)
    else:
        if tem_permissao(permissao): abas_disponiveis.append(nome_aba)

tabs=st.tabs(abas_disponiveis)
tab_dict={nome: tab for nome, tab in zip(abas_disponiveis, tabs)}

if "CADASTRO" in tab_dict:
    with tab_dict["CADASTRO"]:
        st.subheader("CADASTRO - COM EXCLUIR")
        id_in=st.text_input("ID", key="id_cad")
        with st.form("form_cad"):
            c1,c2=st.columns([1,3])
            with c1: id_f=st.text_input("ID", value=id_in.upper() if id_in else "")
            with c2: desc=st.text_input("DESCRIÇÃO")
            c3,c4=st.columns(2)
            with c3: marca=st.text_input("MARCA")
            with c4: qtd=st.number_input("QTD/EMB", value=1250.0)
            if st.form_submit_button("CADASTRAR", type="primary", use_container_width=True):
                if id_f and desc:
                    max_pos=0
                    for r in st.session_state.cad:
                        if str(r.get('ID','')).upper()==id_f.upper().strip():
                            max_pos=max(max_pos, int(sf(r.get('POSICAO',0),0)))
                    for m in st.session_state.mov:
                        if str(m.get('ID','')).upper()==id_f.upper().strip():
                            max_pos=max(max_pos, int(sf(m.get('ORDEM',0),0)))
                    nova_pos=max_pos+1 if max_pos>0 else 1
                    st.session_state.cad.append({"ID":id_f.upper().strip(),"POSICAO":nova_pos,"ORDEM":nova_pos,"DESCRICAO":desc.upper(),"MARCA":marca.upper() or "SEM MARCA","QTD_POR_EMBALAGEM":qtd,"LOTE":""})
                    salvar(); st.success(f"POS {nova_pos}"); st.rerun()
        if st.session_state.cad:
            df=pd.DataFrame(st.session_state.cad)
            df['POSICAO']=df['POSICAO'].apply(lambda x: int(sf(x,1)))
            df=df.sort_values(['ID','POSICAO']).reset_index(drop=True)
            st.dataframe(df, use_container_width=True, height=250)
            st.markdown("#### 🗑️ EXCLUIR CADASTRO")
            for i_row, row in df.iterrows():
                c1,c2,c3,c4,c5,c6 = st.columns([0.8,1,3,1.5,1,0.8])
                c1.write(f"POS {row.get('POSICAO',1)}"); c2.write(f"{row.get('ID','')}"); c3.write(f"{row.get('DESCRICAO','')}"); c4.write(f"{row.get('MARCA','')}"); c5.write(f"{row.get('QTD_POR_EMBALAGEM','')}")
                if c6.button("🗑️", key=f"del_cad_{i_row}_{row.get('ID')}_{row.get('POSICAO')}_{i_row}"):
                    id_remove=str(row.get('ID','')).upper(); desc_remove=str(row.get('DESCRICAO','')).upper(); pos_remove=int(sf(row.get('POSICAO',0)))
                    for j in range(len(st.session_state.cad)-1,-1,-1):
                        rj=st.session_state.cad[j]
                        if str(rj.get('ID','')).upper()==id_remove and str(rj.get('DESCRICAO','')).upper()==desc_remove and int(sf(rj.get('POSICAO',0)))==pos_remove:
                            st.session_state.cad.pop(j); break
                    salvar(); st.rerun()

if "ENTRADA / SAIDA FIFO" in tab_dict:
    with tab_dict["ENTRADA / SAIDA FIFO"]:
        st.subheader("FIFO ORDINAL")
        id_mov=st.text_input("ID FIFO", key="id_mov", placeholder="Digite ID")
        if id_mov:
            id_mov=id_mov.upper().strip()
            saldos = get_saldos_ordinal()
            lotes_com_saldo = sorted([s for s in saldos.values() if s['ID']==id_mov and s['SALDO']>0], key=lambda x: x['ORDEM'])
            if lotes_com_saldo:
                st.markdown(f"### FILA ID {id_mov}")
                for idx_s, s in enumerate(lotes_com_saldo):
                    c1,c2,c3 = st.columns([4,1,0.6])
                    if s['ORDEM']==1: c1.success(f"⭐ POS {s['ORDEM']} - LOTE {s['LOTE']} - {s['SALDO']:,.0f}")
                    else: c1.write(f"POS {s['ORDEM']} - LOTE {s['LOTE']} - {s['SALDO']:,.0f}")
                    c2.write(f"{s['DESCRICAO'][:20]}")
                    if c3.button("🗑️", key=f"del_fila_{id_mov}_{s['LOTE']}_{idx_s}_{s['ORDEM']}_{idx_s}"):
                        st.session_state.mov = [m for m in st.session_state.mov if not (str(m.get('ID','')).upper()==s['ID'] and str(m.get('LOTE','')).upper()==s['LOTE'])]
                        salvar(); reorganiza_fifo_pos1(id_mov); st.rerun()
                if tem_permissao("SAIDA"):
                    pos1 = [s for s in lotes_com_saldo if s['ORDEM']==1]
                    if pos1:
                        lote_pos1=pos1[0]
                        qtd_s=st.number_input(f"SAIDA POS 1 LOTE {lote_pos1['LOTE']}", min_value=0.0, value=0.0, step=1.0, key="qs")
                        if qtd_s>0:
                            tot = qtd_s * lote_pos1['QTD_EMB']
                            if tot > lote_pos1['SALDO']: st.error(f"Saldo insuficiente! Tem {lote_pos1['SALDO']:,.0f}")
                            else:
                                if st.button(f"SAIDA POS 1 {tot:,.0f}", type="primary", use_container_width=True):
                                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                                    st.session_state.mov.append({"ID":id_mov,"DESCRICAO":lote_pos1['DESCRICAO'],"POSICAO":1,"ORDEM":1,"LOTE":lote_pos1['LOTE'],"MARCA":lote_pos1['MARCA'],"PALETES":qtd_s,"TOTAL_QTD":tot,"DATA_HORA":agora_str,"TIPO":"SAIDA","QTD_POR_EMBALAGEM":lote_pos1['QTD_EMB']})
                                    salvar()
                                    if lote_pos1['SALDO']-tot<=0: reorganiza_fifo_pos1(id_mov)
                                    st.rerun()
            if tem_permissao("ENTRADA"):
                st.divider()
                cad_id = [r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_mov]
                if cad_id:
                    ops=[f"{c['DESCRICAO']} - {c.get('MARCA','')}" for c in cad_id]
                    sel=st.selectbox("Material", ops, key="selmat")
                    mat=cad_id[ops.index(sel)]
                    c1,c2=st.columns(2)
                    with c1: lote_e=st.text_input("LOTE NOVO", key="lote_e")
                    with c2: qtd_e=st.number_input("PALETES", min_value=0.0, value=0.0, step=1.0, key="qe")
                    if qtd_e>0 and lote_e:
                        max_ordem=0
                        for m in st.session_state.mov:
                            if str(m.get('ID','')).upper()==id_mov:
                                max_ordem=max(max_ordem, int(sf(m.get('ORDEM',0),0)))
                        nova_ordem=max_ordem+1 if max_ordem>0 else 1
                        if st.button(f"ENTRADA POS {nova_ordem} LOTE {lote_e.upper()}", use_container_width=True):
                            agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                            st.session_state.mov.append({"ID":id_mov,"DESCRICAO":mat['DESCRICAO'],"POSICAO":nova_ordem,"ORDEM":nova_ordem,"LOTE":lote_e.upper(),"MARCA":mat.get('MARCA',''),"PALETES":qtd_e,"TOTAL_QTD":qtd_e*sf(mat.get('QTD_POR_EMBALAGEM',1250)),"DATA_HORA":agora_str,"TIPO":"ENTRADA","QTD_POR_EMBALAGEM":sf(mat.get('QTD_POR_EMBALAGEM',1250))})
                            salvar(); st.rerun()

if "ESTOQUE" in tab_dict:
    with tab_dict["ESTOQUE"]:
        st.subheader("ESTOQUE - COM EXCLUIR LOTE")
        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]
        if lista:
            df=pd.DataFrame(lista).sort_values(['ID','ORDEM']).reset_index(drop=True)
            st.dataframe(df[['ORDEM','ID','LOTE','DESCRICAO','SALDO']], use_container_width=True, height=300)
            st.markdown("#### 🗑️ EXCLUIR LOTE")
            for idx_est, s in enumerate(sorted(lista, key=lambda x: (x['ID'], x['ORDEM']))):
                c1,c2,c3,c4,c5 = st.columns([0.6,0.8,1.2,3,0.6])
                c1.write(f"POS {s['ORDEM']}"); c2.write(f"ID {s['ID']}"); c3.write(f"LOTE {s['LOTE']}"); c4.write(f"{s['DESCRICAO']} - {s['SALDO']:,.0f}")
                if c5.button("🗑️", key=f"del_est_{idx_est}_{s['ID']}_{s['LOTE']}_{s['ORDEM']}_{idx_est}_unique"):
                    st.session_state.mov = [m for m in st.session_state.mov if not (str(m.get('ID','')).upper()==s['ID'] and str(m.get('LOTE','')).upper()==s['LOTE'])]
                    salvar(); reorganiza_fifo_pos1(s['ID']); st.rerun()

if "GRAFICO POS 1" in tab_dict:
    with tab_dict["GRAFICO POS 1"]:
        st.subheader("📊 GRAFICO - 1-ID / 2-TODOS")
        opcao_graf = st.radio("SELEÇÃO:", ["1 - ID", "2 - TODOS"], horizontal=True, key="op_graf")
        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]
        if not lista: st.info("Sem estoque")
        else:
            if opcao_graf == "1 - ID":
                id_graf=st.text_input("DIGITE A ID", key="id_graf")
                if id_graf:
                    id_graf=id_graf.upper().strip()
                    lotes_id = sorted([s for s in lista if s['ID']==id_graf], key=lambda x: x['ORDEM'])
                    if lotes_id:
                        pos1=lotes_id[0]
                        df_pos1=pd.DataFrame([pos1]); df_pos1['TEXTO']=f"LOTE {pos1['LOTE']} {pos1['SALDO']:,.0f}"; df_pos1['LABEL']=f"ID {id_graf}"
                        fig=px.bar(df_pos1, x='SALDO', y='LABEL', color='LOTE', text='TEXTO', orientation='h'); st.plotly_chart(fig, use_container_width=True)
                        df_fila=pd.DataFrame(lotes_id); df_fila['LABEL']=df_fila.apply(lambda r: f"POS {r['ORDEM']} LOTE {r['LOTE']}", axis=1); df_fila['TEXTO']=df_fila.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                        fig2=px.bar(df_fila, x='SALDO', y='LABEL', color='LABEL', text='TEXTO', orientation='h'); st.plotly_chart(fig2, use_container_width=True)
            else:
                pos1_todos=[]; filas_todas=[]
                for id_ in sorted(set([s['ID'] for s in lista])):
                    lotes_id = sorted([s for s in lista if s['ID']==id_], key=lambda x: x['ORDEM'])
                    if lotes_id:
                        pos1_todos.append(lotes_id[0])
                        filas_todas.extend(lotes_id)
                if pos1_todos:
                    df_all=pd.DataFrame(pos1_todos); df_all['LABEL']=df_all.apply(lambda r: f"ID {r['ID']} LOTE {r['LOTE']}", axis=1); df_all['TEXTO']=df_all.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                    fig_all=px.bar(df_all, x='SALDO', y='LABEL', color='ID', text='TEXTO', orientation='h', title="POS 1 TODOS IDS"); st.plotly_chart(fig_all, use_container_width=True)

if "HISTORICO" in tab_dict:
    with tab_dict["HISTORICO"]:
        st.subheader("HISTORICO - COM EXCLUIR")
        if st.session_state.mov:
            df_hist=pd.DataFrame(st.session_state.mov).sort_values('DATA_HORA', ascending=False).reset_index(drop=True)
            st.dataframe(df_hist, use_container_width=True, height=300)
            st.markdown("#### 🗑️ EXCLUIR MOVIMENTAÇÃO")
            for idx_h, row in df_hist.iterrows():
                c1,c2,c3,c4,c5,c6,c7 = st.columns([1,0.8,1,1,1,1.2,0.6])
                c1.write(f"{row.get('DATA_HORA','')[:16]}"); c2.write(f"{row.get('TIPO','')}"); c3.write(f"ID {row.get('ID','')}"); c4.write(f"LOTE {row.get('LOTE','')}"); c5.write(f"{row.get('PALETES','')} pal"); c6.write(f"{row.get('TOTAL_QTD','')}")
                if c7.button("🗑️", key=f"del_hist_{idx_h}_{row.get('ID')}_{row.get('LOTE')}_{idx_h}_h"):
                    for j in range(len(st.session_state.mov)-1,-1,-1):
                        mj=st.session_state.mov[j]
                        if str(mj.get('DATA_HORA',''))==str(row.get('DATA_HORA','')) and str(mj.get('ID',''))==str(row.get('ID','')) and str(mj.get('LOTE',''))==str(row.get('LOTE','')) and str(mj.get('TIPO',''))==str(row.get('TIPO','')):
                            st.session_state.mov.pop(j); break
                    salvar(); reorganiza_fifo_pos1(str(row.get('ID','')).upper()); st.rerun()

if "USUARIOS" in tab_dict:
    with tab_dict["USUARIOS"]:
        st.subheader("USUARIOS - COM EXCLUIR")
        df_emails=carregar_emails()
        st.dataframe(df_emails, use_container_width=True, height=250)
        for idx_u, row_u in df_emails.iterrows():
            c1,c2,c3,c4 = st.columns([3,2,1,0.6])
            c1.write(f"{row_u.get('EMAIL','')}"); c2.write(f"{row_u.get('NOME','')}"); c3.write(f"{row_u.get('STATUS','')}")
            if str(row_u.get('EMAIL','')).lower()!="admin@admin.com":
                if c4.button("🗑️", key=f"del_user_{idx_u}_{row_u.get('EMAIL')}_{idx_u}"):
                    df_emails=df_emails[df_emails["EMAIL"].str.lower()!=str(row_u.get('EMAIL','')).lower()]
                    df_emails.to_csv(ARQ_EMAILS,index=False,encoding='utf-8'); st.rerun()
        st.divider()
        with st.form("form_user"):
            c1,c2,c3=st.columns(3)
            with c1: email_novo=st.text_input("Email")
            with c2: senha_novo=st.text_input("Senha")
            with c3: nome_novo=st.text_input("Nome")
            status_novo=st.selectbox("STATUS", ["LIBERADO","BLOQUEADO"])
            if st.form_submit_button("💾 SALVAR", type="primary"):
                if email_novo and senha_novo:
                    df_emails=df_emails[df_emails["EMAIL"].str.lower()!=email_novo.lower().strip()]
                    novo=pd.DataFrame([{"EMAIL":email_novo.lower().strip(),"SENHA":senha_novo,"NOME":nome_novo.upper(),"STATUS":status_novo,"CADASTRO":"SIM","ENTRADA":"SIM","SAIDA":"SIM","ESTOQUE":"SIM","GRAFICO":"SIM","HISTORICO":"SIM","ADMIN":"NAO"}])
                    df_emails=pd.concat([df_emails,novo],ignore_index=True)
                    df_emails.to_csv(ARQ_EMAILS,index=False,encoding='utf-8'); st.rerun()

st.caption(f"{agora.strftime('%d/%m/%Y %H:%M:%S')} | REFORMA DE FORNOS - MATERIAIS REFRATARIOS")
