import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
import plotly.express as px

st.set_page_config(page_title="FIFO ORDINAL - GRAFICO 1-ID 2-TODOS", layout="wide")
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
    for col in ["EMAIL","SENHA","NOME","STATUS","CADASTRO","ENTRADA","SAIDA","ESTOQUE","GRAFICO","HISTORICO","ADMIN"]:
        if col not in df.columns: df[col]="SIM" if col not in ["EMAIL","SENHA","NOME"] else ""
    for i in range(len(df)):
        if str(df.loc[i,"EMAIL"]).lower()=="admin@admin.com":
            for c in ["STATUS","CADASTRO","ENTRADA","SAIDA","ESTOQUE","GRAFICO","HISTORICO","ADMIN"]:
                df.loc[i,c]="LIBERADO" if c=="STATUS" else "SIM"
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
    tem_ordem1 = any(s['ORDEM']==1 for s in lotes_com_saldo)
    if tem_ordem1: return lotes_com_saldo[0]
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
    st.title("LOGIN - FIFO ORDINAL")
    df_emails=carregar_emails()
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        u=df_emails[(df_emails["EMAIL"].str.lower()==e.lower().strip()) & (df_emails["SENHA"].astype(str)==str(s)) & (df_emails["STATUS"].str.upper()=="LIBERADO")]
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
    if lotes_id:
        tem_ordem1 = any(s['ORDEM']==1 for s in lotes_id)
        if not tem_ordem1:
            reorganiza_fifo_pos1(id_)

st.sidebar.write(f"👤 {user.get('NOME')} - {user.get('EMAIL')}")
if str(user.get('EMAIL','')).lower()=="admin@admin.com": st.sidebar.success("👑 ADMIN TOTAL")
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
            if st.form_submit_button("CADASTRAR - PRÓXIMA POS", type="primary", use_container_width=True):
                if id_f and desc:
                    max_pos=0
                    for r in st.session_state.cad:
                        if str(r.get('ID','')).upper()==id_f.upper().strip():
                            max_pos=max(max_pos, int(sf(r.get('POSICAO',0),0)))
                    for m in st.session_state.mov:
                        if str(m.get('ID','')).upper()==id_f.upper().strip():
                            max_pos=max(max_pos, int(sf(m.get('ORDEM',0),0)))
                    nova_pos=max_pos+1
                    if max_pos==0: nova_pos=1
                    st.session_state.cad.append({"ID":id_f.upper().strip(),"POSICAO":nova_pos,"ORDEM":nova_pos,"DESCRICAO":desc.upper(),"MARCA":marca.upper() or "SEM MARCA","QTD_POR_EMBALAGEM":qtd,"LOTE":""})
                    salvar(); st.success(f"POS {nova_pos}"); st.rerun()
        if st.session_state.cad:
            df=pd.DataFrame(st.session_state.cad)
            df['POSICAO']=df['POSICAO'].apply(lambda x: int(sf(x,1)))
            df=df.sort_values(['ID','POSICAO'])
            st.dataframe(df, use_container_width=True, height=300)
            st.divider()
            st.markdown("#### 🗑️ EXCLUIR CADASTRO")
            for idx_df, row in df.iterrows():
                c1,c2,c3,c4,c5,c6 = st.columns([0.8,1,3,1.5,1,0.8])
                c1.write(f"POS {row.get('POSICAO',1)}"); c2.write(f"{row.get('ID','')}"); c3.write(f"{row.get('DESCRICAO','')}"); c4.write(f"{row.get('MARCA','')}"); c5.write(f"{row.get('QTD_POR_EMBALAGEM','')}")
                if c6.button("🗑️", key=f"del_cad_{idx_df}_{row.get('ID')}_{row.get('POSICAO')}_{row.get('DESCRICAO')}"):
                    id_remove=str(row.get('ID','')).upper(); desc_remove=str(row.get('DESCRICAO','')).upper(); pos_remove=int(sf(row.get('POSICAO',0)))
                    for j in range(len(st.session_state.cad)-1,-1,-1):
                        rj=st.session_state.cad[j]
                        if str(rj.get('ID','')).upper()==id_remove and str(rj.get('DESCRICAO','')).upper()==desc_remove and int(sf(rj.get('POSICAO',0)))==pos_remove:
                            st.session_state.cad.pop(j); break
                    salvar()
                    cad_id_restante=[r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_remove]
                    cad_id_restante=sorted(cad_id_restante, key=lambda x: int(sf(x.get('POSICAO',999))))
                    for new_idx, r in enumerate(cad_id_restante, start=1):
                        for j in range(len(st.session_state.cad)):
                            if st.session_state.cad[j] is r:
                                st.session_state.cad[j]['POSICAO']=new_idx; st.session_state.cad[j]['ORDEM']=new_idx
                    salvar(); st.rerun()

if "ENTRADA / SAIDA FIFO" in tab_dict:
    with tab_dict["ENTRADA / SAIDA FIFO"]:
        st.subheader("FIFO ORDINAL - POS 1 É O QUE SAI")
        id_mov=st.text_input("ID FIFO", key="id_mov", placeholder="Digite ID")
        if id_mov:
            id_mov=id_mov.upper().strip()
            saldos = get_saldos_ordinal()
            lotes_com_saldo = [s for s in saldos.values() if s['ID']==id_mov and s['SALDO']>0]
            lotes_com_saldo = sorted(lotes_com_saldo, key=lambda x: x['ORDEM'])
            if lotes_com_saldo:
                st.markdown(f"### FILA ORDINAL ID {id_mov}")
                for s in lotes_com_saldo:
                    if s['ORDEM']==1: st.success(f"⭐ POS 1 - LOTE {s['LOTE']} - {s['SALDO']:,.0f}")
                    else: st.write(f"POS {s['ORDEM']} - LOTE {s['LOTE']} - {s['SALDO']:,.0f}")
                if tem_permissao("SAIDA"):
                    pos1 = [s for s in lotes_com_saldo if s['ORDEM']==1]
                    if pos1:
                        lote_pos1=pos1[0]
                        qtd_s=st.number_input(f"SAIDA PALETES POS 1 LOTE {lote_pos1['LOTE']}", min_value=0.0, value=0.0, step=1.0, key="qs")
                        if qtd_s>0:
                            tot = qtd_s * lote_pos1['QTD_EMB']
                            if tot > lote_pos1['SALDO']: st.error(f"Saldo insuficiente! Tem {lote_pos1['SALDO']:,.0f}")
                            else:
                                if st.button(f"CONFIRMAR SAIDA POS 1 LOTE {lote_pos1['LOTE']} - {tot:,.0f}", type="primary", use_container_width=True):
                                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                                    st.session_state.mov.append({"ID":id_mov,"DESCRICAO":lote_pos1['DESCRICAO'],"POSICAO":1,"ORDEM":1,"LOTE":lote_pos1['LOTE'],"MARCA":lote_pos1['MARCA'],"PALETES":qtd_s,"TOTAL_QTD":tot,"DATA_HORA":agora_str,"TIPO":"SAIDA","QTD_POR_EMBALAGEM":lote_pos1['QTD_EMB']})
                                    salvar()
                                    if lote_pos1['SALDO']-tot<=0:
                                        st.warning(f"🚨 POS 1 LOTE {lote_pos1['LOTE']} ZEROU! Próximo vira POS 1")
                                        reorganiza_fifo_pos1(id_mov)
                                    st.rerun()
            if tem_permissao("ENTRADA"):
                st.divider()
                st.markdown("#### ENTRADA - NOVA POSIÇÃO ORDINAL")
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
                        nova_ordem=max_ordem+1
                        if max_ordem==0: nova_ordem=1
                        st.info(f"LOTE {lote_e.upper()} vai para POS {nova_ordem}")
                        if st.button(f"ENTRADA POS {nova_ordem} LOTE {lote_e.upper()} - {qtd_e*sf(mat.get('QTD_POR_EMBALAGEM',1250)):,.0f}", use_container_width=True):
                            agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                            st.session_state.mov.append({"ID":id_mov,"DESCRICAO":mat['DESCRICAO'],"POSICAO":nova_ordem,"ORDEM":nova_ordem,"LOTE":lote_e.upper(),"MARCA":mat.get('MARCA',''),"PALETES":qtd_e,"TOTAL_QTD":qtd_e*sf(mat.get('QTD_POR_EMBALAGEM',1250)),"DATA_HORA":agora_str,"TIPO":"ENTRADA","QTD_POR_EMBALAGEM":sf(mat.get('QTD_POR_EMBALAGEM',1250))})
                            salvar(); st.success(f"POS {nova_ordem}"); st.rerun()

if "ESTOQUE" in tab_dict:
    with tab_dict["ESTOQUE"]:
        st.subheader("ESTOQUE ORDINAL")
        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]
        if lista:
            df=pd.DataFrame(lista).sort_values(['ID','ORDEM'])
            st.dataframe(df[['ORDEM','POSICAO','ID','LOTE','DESCRICAO','SALDO']], use_container_width=True, height=500)

if "GRAFICO POS 1" in tab_dict:
    with tab_dict["GRAFICO POS 1"]:
        st.subheader("📊 GRAFICO POSIÇÃO DOS MATERIAIS")
        opcao_graf = st.radio("SELEÇÃO:", ["1 - ID", "2 - TODOS"], horizontal=True, key="op_graf")
        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]
        if not lista:
            st.info("Sem estoque")
        else:
            if opcao_graf == "1 - ID":
                id_graf=st.text_input("DIGITE A ID", key="id_graf", placeholder="Ex: 7 e ENTER")
                if id_graf:
                    id_graf=id_graf.upper().strip()
                    lotes_id = [s for s in lista if s['ID']==id_graf]
                    lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
                    if not lotes_id:
                        st.error(f"ID {id_graf} sem estoque")
                    else:
                        pos1 = lotes_id[0]
                        st.markdown(f"## ⭐ ID {id_graf} - POS 1 LOTE {pos1['LOTE']} - {pos1['SALDO']:,.0f}")
                        df_pos1=pd.DataFrame([pos1])
                        df_pos1['TEXTO']=f"LOTE {pos1['LOTE']} | {pos1['SALDO']:,.0f}"
                        df_pos1['LABEL']=f"ID {id_graf} - POS 1"
                        fig=px.bar(df_pos1, x='SALDO', y='LABEL', color='LOTE', text='TEXTO', orientation='h', title=f"ID {id_graf} - POS 1 LOTE {pos1['LOTE']}")
                        fig.update_traces(textposition='outside', textfont=dict(size=20))
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                        st.divider()
                        df_fila=pd.DataFrame(lotes_id)
                        df_fila['LABEL']=df_fila.apply(lambda r: f"POS {r['ORDEM']} - LOTE {r['LOTE']}", axis=1)
                        df_fila['TEXTO']=df_fila.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                        df_fila['COR']=df_fila.apply(lambda r: "⭐ POS 1" if r['ORDEM']==1 else f"POS {r['ORDEM']}", axis=1)
                        fig2=px.bar(df_fila, x='SALDO', y='LABEL', color='COR', text='TEXTO', orientation='h', title=f"ID {id_graf} - FILA ORDINAL", color_discrete_map={"⭐ POS 1":"green"})
                        fig2.update_traces(textposition='outside')
                        fig2.update_layout(height=350 + len(df_fila)*35)
                        st.plotly_chart(fig2, use_container_width=True)
            else:
                st.markdown("### 📊 TODOS OS IDS - POSIÇÃO ATUAL")
                pos1_todos=[]
                filas_todas=[]
                for id_ in sorted(set([s['ID'] for s in lista])):
                    lotes_id = [s for s in lista if s['ID']==id_]
                    lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
                    if lotes_id:
                        pos1_todos.append(lotes_id[0])
                        for l in lotes_id:
                            filas_todas.append(l)
                if pos1_todos:
                    st.markdown("#### ⭐ POS 1 DE TODOS OS IDS - A USAR AGORA")
                    df_all_pos1=pd.DataFrame(pos1_todos)
                    df_all_pos1['LABEL']=df_all_pos1.apply(lambda r: f"ID {r['ID']} - LOTE {r['LOTE']}", axis=1)
                    df_all_pos1['TEXTO']=df_all_pos1.apply(lambda r: f"ID {r['ID']} LOTE {r['LOTE']} {r['SALDO']:,.0f}", axis=1)
                    df_all_pos1 = df_all_pos1.sort_values('ID')
                    fig_all=px.bar(df_all_pos1, x='SALDO', y='LABEL', color='ID', text='TEXTO', orientation='h', title="TODOS IDS - POS 1")
                    fig_all.update_traces(textposition='outside')
                    fig_all.update_layout(height=400 + len(df_all_pos1)*35)
                    st.plotly_chart(fig_all, use_container_width=True)
                    st.divider()
                    st.markdown("#### 📦 TODAS POSIÇÕES ORDINAIS - TODOS IDS")
                    df_todas=pd.DataFrame(filas_todas)
                    df_todas['LABEL']=df_todas.apply(lambda r: f"ID {r['ID']} POS {r['ORDEM']} LOTE {r['LOTE']}", axis=1)
                    df_todas['TEXTO']=df_todas.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                    df_todas['COR']=df_todas.apply(lambda r: "⭐ POS 1" if r['ORDEM']==1 else f"POS {r['ORDEM']}", axis=1)
                    df_todas = df_todas.sort_values(['ID','ORDEM'])
                    fig_todas=px.bar(df_todas, x='SALDO', y='LABEL', color='COR', text='TEXTO', orientation='h', title="TODOS IDS - TODAS POSIÇÕES", color_discrete_map={"⭐ POS 1":"green"})
                    fig_todas.update_traces(textposition='outside')
                    fig_todas.update_layout(height=500 + len(df_todas)*30, showlegend=True)
                    st.plotly_chart(fig_todas, use_container_width=True)

if "HISTORICO" in tab_dict:
    with tab_dict["HISTORICO"]:
        if st.session_state.mov:
            st.dataframe(pd.DataFrame(st.session_state.mov).sort_values('DATA_HORA', ascending=False), use_container_width=True)

if "USUARIOS" in tab_dict:
    with tab_dict["USUARIOS"]:
        st.subheader("👑 ADMIN")
        df_emails=carregar_emails()
        st.dataframe(df_emails, use_container_width=True, height=250)
        with st.form("form_user"):
            c1,c2,c3=st.columns(3)
            with c1: email_novo=st.text_input("Email")
            with c2: senha_novo=st.text_input("Senha")
            with c3: nome_novo=st.text_input("Nome")
            p1,p2,p3,p4,p5,p6,p7=st.columns(7)
            with p1: perm_cad=st.checkbox("CADASTRO", value=True)
            with p2: perm_ent=st.checkbox("ENTRADA", value=True)
            with p3: perm_sai=st.checkbox("SAIDA", value=True)
            with p4: perm_est=st.checkbox("ESTOQUE", value=True)
            with p5: perm_graf=st.checkbox("GRAFICO", value=True)
            with p6: perm_hist=st.checkbox("HISTORICO", value=True)
            with p7: perm_admin=st.checkbox("ADMIN", value=False)
            status_novo=st.selectbox("STATUS", ["LIBERADO","BLOQUEADO"])
            if st.form_submit_button("💾 SALVAR", type="primary", use_container_width=True):
                if email_novo and senha_novo:
                    df_emails=df_emails[df_emails["EMAIL"].str.lower()!=email_novo.lower().strip()]
                    novo=pd.DataFrame([{"EMAIL":email_novo.lower().strip(),"SENHA":senha_novo,"NOME":nome_novo.upper(),"STATUS":status_novo,"CADASTRO":"SIM" if perm_cad else "NAO","ENTRADA":"SIM" if perm_ent else "NAO","SAIDA":"SIM" if perm_sai else "NAO","ESTOQUE":"SIM" if perm_est else "NAO","GRAFICO":"SIM" if perm_graf else "NAO","HISTORICO":"SIM" if perm_hist else "NAO","ADMIN":"SIM" if perm_admin else "NAO"}])
                    df_emails=pd.concat([df_emails,novo],ignore_index=True)
                    df_emails.to_csv(ARQ_EMAILS,index=False,encoding='utf-8')
                    st.success("Salvo!"); st.rerun()

st.caption(f"{agora.strftime('%d/%m/%Y %H:%M:%S')} | GRAFICO 1-ID 2-TODOS")
