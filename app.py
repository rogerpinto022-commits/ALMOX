import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
import plotly.express as px

st.set_page_config(page_title="FIFO ORDINAL POS 1", layout="wide")
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
    """FIFO ORDINAL - CADA LOTE TEM ORDEM 1,2,3 - POS 1 É O QUE SAI"""
    saldos={}
    # Agrupa por ID + DESCRICAO + LOTE + ORDEM
    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip()
            desc=str(m.get('DESCRICAO','')).upper().strip()
            lote=str(m.get('LOTE','SEM LOTE')).upper().strip()
            ordem=int(sf(m.get('ORDEM', m.get('POSICAO',1)),1))
            if not idp or not lote: continue
            chave=f"{idp}__{desc}__{lote}__{ordem}"
            if chave not in saldos:
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'LOTE':lote,'ORDEM':ordem,'POSICAO':ordem,'MARCA':str(m.get('MARCA','')), 'SALDO':0, 'PRIMEIRA_DATA':str(m.get('DATA_HORA','')), 'QTD_EMB':sf(m.get('QTD_POR_EMBALAGEM',1250))}
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=sf(m.get('TOTAL_QTD',0))
            else: saldos[chave]['SALDO']-=sf(m.get('TOTAL_QTD',0))
        except: continue
    return saldos

def reorganiza_fifo_pos1(id_):
    """QUANDO POS 1 ZERA, PROXIMO VIRA POS 1"""
    saldos = get_saldos_ordinal()
    # Pega só desse ID com saldo >0
    lotes_com_saldo = [s for s in saldos.values() if s['ID']==id_ and s['SALDO']>0]
    lotes_com_saldo = sorted(lotes_com_saldo, key=lambda x: x['ORDEM'])

    if not lotes_com_saldo:
        return None, "ID SEM ESTOQUE"

    # Se POS 1 ainda tem saldo, não faz nada
    pos1_atual = [s for s in lotes_com_saldo if s['ORDEM']==1]
    if pos1_atual and pos1_atual[0]['SALDO']>0:
        return pos1_atual[0], None

    # POS 1 ZEROU! Precisa reorganizar
    # Todos lotes com saldo, reordena para 1,2,3
    # Acha todos os movimentos desse ID e renumera ORDEM
    # Primeiro pega todos lotes únicos desse ID ordenados pela ORDEM antiga
    todos_lotes = {}
    for m in st.session_state.mov:
        if str(m.get('ID','')).upper()==id_:
            lote=str(m.get('LOTE','')).upper()
            ordem=int(sf(m.get('ORDEM',1),1))
            if lote not in todos_lotes or ordem < todos_lotes[lote]:
                todos_lotes[lote]=ordem

    lotes_ordenados = sorted(todos_lotes.items(), key=lambda x: x[1])
    # Remove o primeiro que zerou (se saldo <=0)
    # Verifica qual zerou
    saldos_zerados = [s for s in saldos.values() if s['ID']==id_ and s['SALDO']<=0]
    lotes_zerados = set([s['LOTE'] for s in saldos_zerados])

    # Filtra só lotes com saldo >0
    lotes_vivos = [l for l in lotes_ordenados if l[0] not in lotes_zerados or any([s['LOTE']==l[0] and s['SALDO']>0 for s in saldos.values()])]
    # Na verdade pega direto dos que tem saldo
    lotes_vivos = [(s['LOTE'], s['ORDEM']) for s in lotes_com_saldo]
    lotes_vivos = sorted(lotes_vivos, key=lambda x: x[1])

    # Renumera no MOV: o primeiro vivo vira ORDEM 1, segundo vira 2, etc
    mapa_nova_ordem={}
    for idx, (lote, ordem_antiga) in enumerate(lotes_vivos, start=1):
        mapa_nova_ordem[lote]=idx

    for j in range(len(st.session_state.mov)):
        if str(st.session_state.mov[j].get('ID','')).upper()==id_:
            lote_mov=str(st.session_state.mov[j].get('LOTE','')).upper()
            if lote_mov in mapa_nova_ordem:
                st.session_state.mov[j]['ORDEM']=mapa_nova_ordem[lote_mov]
                st.session_state.mov[j]['POSICAO']=mapa_nova_ordem[lote_mov]

    # Também reorganiza CAD se tiver lotes lá
    for j in range(len(st.session_state.cad)):
        if str(st.session_state.cad[j].get('ID','')).upper()==id_:
            lote_cad=str(st.session_state.cad[j].get('LOTE','')).upper() if 'LOTE' in st.session_state.cad[j] else ""
            if lote_cad in mapa_nova_ordem:
                st.session_state.cad[j]['POSICAO']=mapa_nova_ordem[lote_cad]
                st.session_state.cad[j]['ORDEM']=mapa_nova_ordem[lote_cad]

    salvar()

    novo_pos1 = lotes_com_saldo[0] if lotes_com_saldo else None
    if novo_pos1:
        # atualiza ordem para 1
        novo_pos1['ORDEM']=1
        novo_pos1['POSICAO']=1
        return novo_pos1, f"🚨 LOTE {list(lotes_zerados)[0] if lotes_zerados else ''} ZEROU! Agora POS 1 é LOTE {novo_pos1['LOTE']}"
    return None, None

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

# VERIFICA AUTOMATICAMENTE SE TEM POS 1 ZERADA AO ABRIR
saldos_geral = get_saldos_ordinal()
for id_ in set([s['ID'] for s in saldos_geral.values()]):
    lotes_id = [s for s in saldos_geral.values() if s['ID']==id_ and s['SALDO']>0]
    lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
    if lotes_id:
        # se não tem ninguém com ORDEM 1 mas tem saldo, reorganiza
        tem_ordem1 = any([s['ORDEM']==1 for s in lotes_id])
        if not tem_ordem1:
            reorganiza_fifo_pos1(id_)

saldos_geral = get_saldos_ordinal()

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
        st.subheader("CADASTRO - POSIÇÃO ORDINAL AUTOMÁTICA")
        id_in=st.text_input("ID", key="id_cad")
        with st.form("form_cad"):
            c1,c2=st.columns([1,3])
            with c1: id_f=st.text_input("ID", value=id_in.upper() if id_in else "")
            with c2: desc=st.text_input("DESCRIÇÃO")
            c3,c4=st.columns(2)
            with c3: marca=st.text_input("MARCA")
            with c4: qtd=st.number_input("QTD/EMB", value=1250.0)
            lote_cad=st.text_input("LOTE (opcional no cadastro)", placeholder="Ex: L001")
            if st.form_submit_button("CADASTRAR - VAI PARA PRÓXIMA POSIÇÃO ORDINAL", type="primary", use_container_width=True):
                if id_f and desc:
                    # ACHA MAIOR POSIÇÃO DESSE ID
                    max_pos = 0
                    for r in st.session_state.cad:
                        if str(r.get('ID','')).upper()==id_f.upper().strip():
                            max_pos = max(max_pos, int(sf(r.get('POSICAO',0),0)))
                    for m in st.session_state.mov:
                        if str(m.get('ID','')).upper()==id_f.upper().strip():
                            max_pos = max(max_pos, int(sf(m.get('ORDEM', m.get('POSICAO',0)),0)))
                    nova_pos = max_pos + 1
                    if max_pos==0: nova_pos=1
                    st.session_state.cad.append({"ID":id_f.upper().strip(),"POSICAO":nova_pos,"ORDEM":nova_pos,"DESCRICAO":desc.upper(),"MARCA":marca.upper() or "SEM MARCA","QTD_POR_EMBALAGEM":qtd,"LOTE":lote_cad.upper() if lote_cad else ""})
                    salvar()
                    st.success(f"Cadastrado na POSIÇÃO ORDINAL {nova_pos}")
                    st.rerun()
        if st.session_state.cad:
            df=pd.DataFrame(st.session_state.cad)
            df['POSICAO']=df['POSICAO'].apply(lambda x: int(sf(x,1)))
            df=df.sort_values(['ID','POSICAO'])
            st.dataframe(df, use_container_width=True, height=300)

if "ENTRADA / SAIDA FIFO" in tab_dict:
    with tab_dict["ENTRADA / SAIDA FIFO"]:
        st.subheader("FIFO ORDINAL - POS 1 É O QUE SAI")
        id_mov=st.text_input("ID FIFO", key="id_mov", placeholder="Digite ID")
        if id_mov:
            id_mov=id_mov.upper().strip()
            saldos = get_saldos_ordinal()
            lotes_id = [s for s in saldos.values() if s['ID']==id_mov]
            lotes_com_saldo = [s for s in lotes_id if s['SALDO']>0]
            lotes_com_saldo = sorted(lotes_com_saldo, key=lambda x: x['ORDEM'])

            if not lotes_id:
                # Verifica se tem cadastro
                tem_cad = any([str(r.get('ID','')).upper()==id_mov for r in st.session_state.cad])
                if not tem_cad:
                    st.error(f"ID {id_mov} não cadastrado - vá em CADASTRO")
                else:
                    st.warning(f"ID {id_mov} cadastrado mas sem entrada - faça ENTRADA abaixo")
            else:
                st.markdown(f"### FILA ORDINAL ID {id_mov}")
                for s in lotes_com_saldo:
                    if s['ORDEM']==1:
                        st.success(f"⭐ POS 1 - USAR AGORA - ORDEM {s['ORDEM']} - LOTE {s['LOTE']} - {s['DESCRICAO']} - {s['SALDO']:,.0f}")
                    else:
                        st.write(f"POS {s['ORDEM']} - LOTE {s['LOTE']} - {s['SALDO']:,.0f}")

                # SAIDA
                if tem_permissao("SAIDA"):
                    pos1 = [s for s in lotes_com_saldo if s['ORDEM']==1]
                    if pos1:
                        lote_pos1=pos1[0]
                        qtd_s=st.number_input(f"SAIDA PALETES POS 1 LOTE {lote_pos1['LOTE']}", min_value=0.0, value=0.0, step=1.0, key="qs")
                        if qtd_s>0:
                            tot = qtd_s * lote_pos1['QTD_EMB']
                            if tot > lote_pos1['SALDO']:
                                st.error(f"Saldo insuficiente! LOTE {lote_pos1['LOTE']} tem {lote_pos1['SALDO']:,.0f}")
                            else:
                                if st.button(f"CONFIRMAR SAIDA POS 1 LOTE {lote_pos1['LOTE']} - {tot:,.0f}", type="primary", use_container_width=True):
                                    agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                                    st.session_state.mov.append({"ID":id_mov,"DESCRICAO":lote_pos1['DESCRICAO'],"POSICAO":1,"ORDEM":1,"LOTE":lote_pos1['LOTE'],"MARCA":lote_pos1['MARCA'],"PALETES":qtd_s,"TOTAL_QTD":tot,"DATA_HORA":agora_str,"TIPO":"SAIDA","QTD_POR_EMBALAGEM":lote_pos1['QTD_EMB']})
                                    salvar()
                                    novo_saldo = lote_pos1['SALDO']-tot
                                    if novo_saldo<=0:
                                        st.warning(f"🚨 POS 1 LOTE {lote_pos1['LOTE']} ZEROU! Jogando próximo para POS 1...")
                                        reorganiza_fifo_pos1(id_mov)
                                    st.rerun()
                    else:
                        st.warning("POS 1 zerada - reorganizando...")
                        reorganiza_fifo_pos1(id_mov)
                        st.rerun()

            # ENTRADA - SEMPRE NOVA POSIÇÃO ORDINAL
            if tem_permissao("ENTRADA"):
                st.divider()
                st.markdown("#### ENTRADA - VAI PARA PRÓXIMA POSIÇÃO ORDINAL")
                # pega cadastro desse ID para pegar descricao/marca/qtd
                cad_id = [r for r in st.session_state.cad if str(r.get('ID','')).upper()==id_mov]
                if not cad_id:
                    st.info("Cadastre primeiro o material em CADASTRO")
                else:
                    ops=[f"{c['DESCRICAO']} - {c.get('MARCA','')}" for c in cad_id]
                    sel=st.selectbox("Material", ops, key="selmat")
                    mat=cad_id[ops.index(sel)]
                    c1,c2=st.columns(2)
                    with c1: lote_e=st.text_input("LOTE NOVO", key="lote_e", placeholder="Ex: L002")
                    with c2: qtd_e=st.number_input("PALETES ENTRADA", min_value=0.0, value=0.0, step=1.0, key="qe")
                    if qtd_e>0 and lote_e:
                        # CALCULA PRÓXIMA POSIÇÃO ORDINAL
                        max_ordem = 0
                        for m in st.session_state.mov:
                            if str(m.get('ID','')).upper()==id_mov:
                                max_ordem = max(max_ordem, int(sf(m.get('ORDEM',0),0)))
                        for r in st.session_state.cad:
                            if str(r.get('ID','')).upper()==id_mov:
                                max_ordem = max(max_ordem, int(sf(r.get('POSICAO',0),0)))
                        nova_ordem = max_ordem + 1
                        if max_ordem==0: nova_ordem=1

                        st.info(f"Este LOTE {lote_e.upper()} vai entrar na POSIÇÃO ORDINAL {nova_ordem}")
                        if st.button(f"ENTRADA POS {nova_ordem} LOTE {lote_e.upper()} - {qtd_e*sf(mat.get('QTD_POR_EMBALAGEM',1250)):,.0f}", use_container_width=True):
                            agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                            st.session_state.mov.append({"ID":id_mov,"DESCRICAO":mat['DESCRICAO'],"POSICAO":nova_ordem,"ORDEM":nova_ordem,"LOTE":lote_e.upper(),"MARCA":mat.get('MARCA',''),"PALETES":qtd_e,"TOTAL_QTD":qtd_e*sf(mat.get('QTD_POR_EMBALAGEM',1250)),"DATA_HORA":agora_str,"TIPO":"ENTRADA","QTD_POR_EMBALAGEM":sf(mat.get('QTD_POR_EMBALAGEM',1250))})
                            salvar()
                            st.success(f"LOTE {lote_e.upper()} cadastrado na POSIÇÃO {nova_ordem}")
                            st.rerun()

if "ESTOQUE" in tab_dict:
    with tab_dict["ESTOQUE"]:
        st.subheader("ESTOQUE - ORDINAL")
        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]
        if lista:
            df=pd.DataFrame(lista).sort_values(['ID','ORDEM'])
            st.dataframe(df[['ORDEM','POSICAO','ID','LOTE','DESCRICAO','SALDO']], use_container_width=True, height=500)

if "GRAFICO POS 1" in tab_dict:
    with tab_dict["GRAFICO POS 1"]:
        st.subheader("📊 GRAFICO - QUAL LOTE ESTÁ NA POS 1")
        saldos = get_saldos_ordinal()
        lista=[v for v in saldos.values() if v['SALDO']>0]
        if lista:
            id_graf=st.text_input("DIGITE ID", key="id_graf", placeholder="Ex: 7")
            if id_graf:
                id_graf=id_graf.upper().strip()
                lotes_id = [s for s in lista if s['ID']==id_graf]
                lotes_id = sorted(lotes_id, key=lambda x: x['ORDEM'])
                if not lotes_id:
                    st.error(f"ID {id_graf} sem estoque")
                else:
                    pos1 = lotes_id[0]
                    st.markdown(f"## ⭐ ID {id_graf} - POS 1 AGORA")
                    st.markdown(f"# LOTE {pos1['LOTE']} - {pos1['SALDO']:,.0f}")
                    st.markdown(f"### {pos1['DESCRICAO']}")

                    df_pos1=pd.DataFrame([pos1])
                    df_pos1['TEXTO']=f"LOTE {pos1['LOTE']} | {pos1['SALDO']:,.0f}"
                    fig=px.bar(df_pos1, x='SALDO', y='LOTE', color='LOTE', text='TEXTO', orientation='h', title=f"ID {id_graf} - POS 1 - LOTE {pos1['LOTE']} - USAR AGORA")
                    fig.update_traces(textposition='outside', textfont=dict(size=20))
                    fig.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                    st.divider()
                    st.markdown(f"#### FILA ORDINAL ID {id_graf}")
                    df_fila=pd.DataFrame(lotes_id)
                    df_fila['LABEL']=df_fila.apply(lambda r: f"POS {r['ORDEM']} - LOTE {r['LOTE']}", axis=1)
                    df_fila['TEXTO']=df_fila.apply(lambda r: f"{r['SALDO']:,.0f}", axis=1)
                    df_fila['COR']=df_fila.apply(lambda r: "POS 1" if r['ORDEM']==1 else "FILA", axis=1)
                    fig2=px.bar(df_fila, x='SALDO', y='LABEL', color='COR', text='TEXTO', orientation='h', title=f"FILA ORDINAL ID {id_graf}", color_discrete_map={"POS 1":"green","FILA":"gray"})
                    fig2.update_traces(textposition='outside')
                    st.plotly_chart(fig2, use_container_width=True)

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

st.caption(f"{agora.strftime('%d/%m/%Y %H:%M:%S')} | FIFO ORDINAL - POS 1 AUTO")
