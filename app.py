import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta, date
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="REFORMA FIFO - COM PERMISSÃO", layout="wide")
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
    return df.to_dict('records')

def carregar_emails():
    if not os.path.exists(ARQ_EMAILS):
        df = pd.DataFrame([{
            "EMAIL":"admin@admin.com","SENHA":"admin","NOME":"ADMIN","STATUS":"LIBERADO",
            "CADASTRO":"SIM","ENTRADA":"SIM","SAIDA":"SIM","ESTOQUE":"SIM","GRAFICO":"SIM","HISTORICO":"SIM","ADMIN":"SIM"
        }])
        df.to_csv(ARQ_EMAILS,index=False,encoding='utf-8')
    df=pd.read_csv(ARQ_EMAILS,dtype=str,encoding='utf-8').fillna("")
    df.columns=[c.upper() for c in df.columns]
    # garante colunas de permissão
    for col in ["CADASTRO","ENTRADA","SAIDA","ESTOQUE","GRAFICO","HISTORICO","ADMIN","NOME","STATUS"]:
        if col not in df.columns: df[col]="NAO" if col not in ["NOME","STATUS"] else ""
    return df

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
            pos=int(sf(r.get('POSICAO',1),1))
            carac[k]={'ID':idp,'DESCRICAO':desc,'POSICAO':pos,'MARCA':str(r.get('MARCA','')).upper(),'QTD':sf(r.get('QTD_POR_EMBALAGEM',1250))}
    for m in st.session_state.mov:
        try:
            idp=str(m.get('ID','')).upper().strip(); desc=str(m.get('DESCRICAO','')).upper()
            lote=str(m.get('LOTE','SEM LOTE')).upper().strip()
            if not idp: continue
            c=None
            for v in carac.values():
                if v['ID']==idp and v['DESCRICAO']==desc: c=v; break
            if not c:
                for v in carac.values():
                    if v['ID']==idp: c=v; break
            if not c: continue
            chave=f"{idp}__{desc}__{c['POSICAO']}__{c['MARCA']}__{lote}"
            if chave not in saldos:
                saldos[chave]={'ID':idp,'DESCRICAO':desc,'POSICAO':c['POSICAO'],'MARCA':c['MARCA'],'LOTE':lote,'SALDO':0}
            if m.get('TIPO')=="ENTRADA": saldos[chave]['SALDO']+=sf(m.get('TOTAL_QTD',0))
            else: saldos[chave]['SALDO']-=sf(m.get('TOTAL_QTD',0))
        except: continue
    return saldos, carac

def tem_permissao(func):
    """Verifica se usuário tem permissão"""
    user = st.session_state.get('user',{})
    if not user: return False
    if str(user.get('ADMIN','')).upper()=='SIM': return True
    return str(user.get(func,'')).upper()=='SIM'

if 'ok' not in st.session_state:
    st.session_state.cad=carregar(ARQ_CAD)
    st.session_state.mov=carregar(ARQ_MOV)
    st.session_state.ok=True
if 'log' not in st.session_state: st.session_state.log=False
if 'user' not in st.session_state: st.session_state.user=None

if not st.session_state.log:
    st.title("REFORMA DE FORNOS - LOGIN")
    df_emails = carregar_emails()
    e=st.text_input("Email"); s=st.text_input("Senha",type="password")
    if st.button("Entrar",type="primary"):
        u=df_emails[(df_emails["EMAIL"].str.lower()==e.lower().strip()) & (df_emails["SENHA"].astype(str)==str(s)) & (df_emails["STATUS"].str.upper()=="LIBERADO")]
        if not u.empty:
            st.session_state.log=True
            st.session_state.user=u.iloc[0].to_dict()
            st.rerun()
        else: st.error("Acesso negado ou sem permissão")
    st.stop()

user = st.session_state.user
agora=datetime.now(fuso)

# SIDEBAR COM PERMISSÕES
st.sidebar.write(f"👤 {user.get('NOME')} - {user.get('EMAIL')}")
st.sidebar.write(f"Permissões:")
for f in ["CADASTRO","ENTRADA","SAIDA","ESTOQUE","GRAFICO","HISTORICO","ADMIN"]:
    if str(user.get(f,'')).upper()=='SIM':
        st.sidebar.caption(f"✅ {f}")
    else:
        st.sidebar.caption(f"❌ {f}")

if st.sidebar.button("Sair"):
    salvar()
    st.session_state.log=False
    st.session_state.user=None
    st.rerun()

# DEFINE QUAIS ABAS O USUÁRIO PODE VER
abas_disponiveis = []
mapa_abas = {
    "CADASTRO": "CADASTRO",
    "ENTRADA / SAIDA": "ENTRADA", # precisa de ENTRADA ou SAIDA
    "ESTOQUE": "ESTOQUE",
    "GRAFICO POS 1": "GRAFICO",
    "HISTORICO": "HISTORICO",
    "USUARIOS": "ADMIN"
}

# Lógica: ENTRADA/SAIDA libera se tiver uma das duas
for nome_aba, permissao in mapa_abas.items():
    if nome_aba == "ENTRADA / SAIDA":
        if tem_permissao("ENTRADA") or tem_permissao("SAIDA") or tem_permissao("ADMIN"):
            abas_disponiveis.append(nome_aba)
    else:
        if tem_permissao(permissao):
            abas_disponiveis.append(nome_aba)

if not abas_disponiveis:
    st.error("⛔ Você não tem permissão para nenhuma função. Fale com o ADMIN.")
    st.stop()

tabs = st.tabs(abas_disponiveis)

# DICIONARIO PARA ACESSAR TAB PELO NOME
tab_dict = {nome: tab for nome, tab in zip(abas_disponiveis, tabs)}

# TAB CADASTRO
if "CADASTRO" in tab_dict:
    with tab_dict["CADASTRO"]:
        if not tem_permissao("CADASTRO"):
            st.error("⛔ Sem permissão para CADASTRO")
        else:
            st.subheader("CADASTRO - PERMISSÃO CADASTRO")
            id_in=st.text_input("ID", key="id_cad")
            with st.form("form_cad"):
                c1,c2,c3=st.columns([1,3,1])
                with c1: id_f=st.text_input("ID", value=id_in.upper() if id_in else "")
                with c2: desc=st.text_input("DESCRIÇÃO")
                with c3: pos=st.number_input("POSIÇÃO", min_value=1, value=1, step=1)
                c4,c5=st.columns(2)
                with c4: marca=st.text_input("MARCA")
                with c5: qtd=st.number_input("QTD/EMB", value=1250.0)
                if st.form_submit_button("CADASTRAR", type="primary", use_container_width=True):
                    if id_f and desc:
                        st.session_state.cad.append({"ID":id_f.upper().strip(),"POSICAO":pos,"DESCRICAO":desc.upper(),"MARCA":marca.upper() or "SEM MARCA","QTD_POR_EMBALAGEM":qtd})
                        salvar(); st.rerun()
            if st.session_state.cad:
                df = pd.DataFrame(st.session_state.cad)
                df['POSICAO']=df['POSICAO'].apply(lambda x: int(sf(x,1)))
                df=df.sort_values(['ID','POSICAO'])
                st.dataframe(df, use_container_width=True, height=300)
                for idx_df, row in df.iterrows():
                    c1,c2,c3,c4,c5,c6 = st.columns([0.8,1,3,1.5,1,0.8])
                    c1.write(f"{row.get('POSICAO',1)}"); c2.write(f"{row.get('ID','')}"); c3.write(f"{row.get('DESCRICAO','')}"); c4.write(f"{row.get('MARCA','')}"); c5.write(f"{row.get('QTD_POR_EMBALAGEM','')}")
                    if c6.button("🗑️", key=f"del_{idx_df}"):
                        for j in range(len(st.session_state.cad)-1,-1,-1):
                            rj=st.session_state.cad[j]
                            if str(rj.get('ID'))==str(row.get('ID')) and str(rj.get('DESCRICAO'))==str(row.get('DESCRICAO')):
                                st.session_state.cad.pop(j); break
                        salvar(); st.rerun()

# TAB ENTRADA / SAIDA
if "ENTRADA / SAIDA" in tab_dict:
    with tab_dict["ENTRADA / SAIDA"]:
        pode_entrada = tem_permissao("ENTRADA")
        pode_saida = tem_permissao("SAIDA")
        st.subheader(f"ENTRADA / SAIDA - Entrada: {'✅' if pode_entrada else '❌'} Saida: {'✅' if pode_saida else '❌'}")
        id_mov=st.text_input("ID FIFO", key="id_mov")
        if id_mov:
            saldos,carac = get_saldos()
            lista = sorted([v for v in carac.values() if v['ID']==id_mov.upper()], key=lambda x: x['POSICAO'])
            saldos_id = sorted([s for s in saldos.values() if s['ID']==id_mov.upper() and s['SALDO']>0], key=lambda x: x['POSICAO'])
            if not lista: st.error("ID não cadastrado")
            else:
                for s in saldos_id:
                    emoji="⭐ POS 1 - USAR AGORA" if s['POSICAO']==1 else f"POS {s['POSICAO']}"
                    st.write(f"{emoji} | LOTE {s['LOTE']} | {s['SALDO']:,.0f}")

                if pode_saida:
                    pos1_list = [s for s in saldos_id if s['POSICAO']==1]
                    if pos1_list:
                        mat = pos1_list[0]
                        st.success(f"SAIDA POS 1 LOTE {mat['LOTE']} - {mat['SALDO']:,.0f}")
                        qtd_s=st.number_input("QTD PALETES SAIDA", min_value=0.0, value=0.0, step=1.0, key="qs")
                        if qtd_s>0:
                            cad_pos1 = [c for c in lista if c['POSICAO']==1][0]
                            tot = qtd_s * cad_pos1['QTD']
                            if st.button(f"CONFIRMAR SAIDA {tot:,.0f}", type="primary", use_container_width=True):
                                agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                                st.session_state.mov.append({"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"POSICAO":1,"LOTE":mat['LOTE'],"MARCA":mat['MARCA'],"PALETES":qtd_s,"TOTAL_QTD":tot,"DATA_HORA":agora_str,"TIPO":"SAIDA","QTD_POR_EMBALAGEM":cad_pos1['QTD']})
                                salvar(); st.rerun()
                else:
                    st.warning("⛔ Você não tem permissão para SAIDA")

                if pode_entrada:
                    st.divider()
                    st.markdown("#### ENTRADA COM LOTE")
                    mats_sorted = sorted(lista, key=lambda x: x['POSICAO'])
                    ops=[f"POS {m['POSICAO']} | {m['DESCRICAO']}" for m in mats_sorted]
                    sel=st.selectbox("Material", ops, key="selmat")
                    mat=mats_sorted[ops.index(sel)]
                    c1,c2=st.columns(2)
                    with c1: lote_e=st.text_input("LOTE", key="lote_e")
                    with c2: qtd_e=st.number_input("PALETES", min_value=0.0, value=0.0, step=1.0, key="qe")
                    if qtd_e>0 and lote_e and st.button(f"ENTRADA {qtd_e*mat['QTD']:,.0f}", use_container_width=True):
                        agora_str=datetime.now(fuso).strftime("%d/%m/%Y %H:%M:%S")
                        st.session_state.mov.append({"ID":id_mov.upper(),"DESCRICAO":mat['DESCRICAO'],"POSICAO":mat['POSICAO'],"LOTE":lote_e.upper(),"MARCA":mat['MARCA'],"PALETES":qtd_e,"TOTAL_QTD":qtd_e*mat['QTD'],"DATA_HORA":agora_str,"TIPO":"ENTRADA","QTD_POR_EMBALAGEM":mat['QTD']})
                        salvar(); st.rerun()
                else:
                    st.warning("⛔ Sem permissão para ENTRADA")

# TAB ESTOQUE
if "ESTOQUE" in tab_dict:
    with tab_dict["ESTOQUE"]:
        if not tem_permissao("ESTOQUE"):
            st.error("⛔ Sem permissão ESTOQUE")
        else:
            st.subheader("ESTOQUE FIFO")
            saldos,_=get_saldos()
            lista=[v for v in saldos.values() if v['SALDO']>0]
            if lista:
                df=pd.DataFrame(lista).sort_values(['ID','POSICAO','LOTE'])
                st.dataframe(df, use_container_width=True, height=500)

# TAB GRAFICO
if "GRAFICO POS 1" in tab_dict:
    with tab_dict["GRAFICO POS 1"]:
        if not tem_permissao("GRAFICO"):
            st.error("⛔ Sem permissão GRAFICO")
        else:
            st.subheader("📊 GRAFICO - LOTE NA POS 1 - MATERIAL A USAR")
            saldos,carac = get_saldos()
            lista=[v for v in saldos.values() if v['SALDO']>0]
            if not lista: st.info("Sem estoque")
            else:
                id_graf = st.text_input("DIGITE ID", key="id_graf_input")
                if id_graf:
                    id_graf=id_graf.upper().strip()
                    saldos_id = [s for s in lista if s['ID']==id_graf]
                    pos1 = [s for s in saldos_id if s['POSICAO']==1]
                    if not pos1:
                        st.warning(f"ID {id_graf} POS 1 zerada")
                    else:
                        df_pos1 = pd.DataFrame(pos1)
                        df_pos1['TEXTO']=df_pos1.apply(lambda r: f"LOTE {r['LOTE']} | {r['SALDO']:,.0f}", axis=1)
                        df_pos1['LABEL']=df_pos1.apply(lambda r: f"LOTE {r['LOTE']}", axis=1)
                        st.markdown(f"### ⭐ ID {id_graf} - USAR AGORA POS 1 LOTE {pos1[0]['LOTE']} - {pos1[0]['SALDO']:,.0f}")
                        fig = px.bar(df_pos1, x='SALDO', y='LABEL', color='LOTE', text='TEXTO', orientation='h', title=f"ID {id_graf} - POS 1")
                        fig.update_traces(textposition='outside', textfont=dict(size=16))
                        st.plotly_chart(fig, use_container_width=True)

# TAB HISTORICO
if "HISTORICO" in tab_dict:
    with tab_dict["HISTORICO"]:
        if not tem_permissao("HISTORICO"):
            st.error("⛔ Sem permissão HISTORICO")
        else:
            st.subheader("HISTORICO")
            if st.session_state.mov:
                st.dataframe(pd.DataFrame(st.session_state.mov), use_container_width=True)

# TAB ADMIN - GERENCIAR USUARIOS E PERMISSÕES
if "USUARIOS" in tab_dict:
    with tab_dict["USUARIOS"]:
        if not tem_permissao("ADMIN"):
            st.error("⛔ Só ADMIN acessa usuários")
        else:
            st.subheader("👑 ADMIN - CONTROLE DE ACESSO POR FUNÇÃO")
            df_emails = carregar_emails()
            st.dataframe(df_emails, use_container_width=True, height=250)

            st.divider()
            st.markdown("### ➕ CADASTRAR / EDITAR USUÁRIO E PERMISSÕES")

            with st.form("form_user"):
                c1,c2,c3=st.columns(3)
                with c1: email_novo=st.text_input("Email")
                with c2: senha_novo=st.text_input("Senha")
                with c3: nome_novo=st.text_input("Nome")

                st.markdown("**Marque o que o usuário pode acessar:**")
                p1,p2,p3,p4,p5,p6,p7=st.columns(7)
                with p1: perm_cad=st.checkbox("CADASTRO", value=True)
                with p2: perm_ent=st.checkbox("ENTRADA", value=True)
                with p3: perm_sai=st.checkbox("SAIDA", value=True)
                with p4: perm_est=st.checkbox("ESTOQUE", value=True)
                with p5: perm_graf=st.checkbox("GRAFICO", value=True)
                with p6: perm_hist=st.checkbox("HISTORICO", value=True)
                with p7: perm_admin=st.checkbox("ADMIN", value=False)

                status_novo=st.selectbox("STATUS", ["LIBERADO","BLOQUEADO"])

                if st.form_submit_button("💾 SALVAR USUÁRIO COM PERMISSÕES", type="primary", use_container_width=True):
                    if email_novo and senha_novo:
                        # remove se já existe
                        df_emails = df_emails[df_emails["EMAIL"].str.lower()!=email_novo.lower().strip()]
                        novo = pd.DataFrame([{
                            "EMAIL":email_novo.lower().strip(),
                            "SENHA":senha_novo,
                            "NOME":nome_novo.upper(),
                            "STATUS":status_novo,
                            "CADASTRO":"SIM" if perm_cad else "NAO",
                            "ENTRADA":"SIM" if perm_ent else "NAO",
                            "SAIDA":"SIM" if perm_sai else "NAO",
                            "ESTOQUE":"SIM" if perm_est else "NAO",
                            "GRAFICO":"SIM" if perm_graf else "NAO",
                            "HISTORICO":"SIM" if perm_hist else "NAO",
                            "ADMIN":"SIM" if perm_admin else "NAO"
                        }])
                        df_emails=pd.concat([df_emails,novo],ignore_index=True)
                        df_emails.to_csv(ARQ_EMAILS,index=False,encoding='utf-8')
                        st.success(f"Usuário {email_novo} salvo! Permissões: CAD:{perm_cad} ENT:{perm_ent} SAI:{perm_sai}")
                        st.rerun()

            st.divider()
            st.markdown("### 🗑️ EXCLUIR USUÁRIO")
            if not df_emails.empty:
                email_del = st.selectbox("Selecione email para excluir", df_emails["EMAIL"].tolist(), key="del_user")
                if st.button(f"🗑️ EXCLUIR {email_del}", type="primary"):
                    df_emails = df_emails[df_emails["EMAIL"]!=email_del]
                    df_emails.to_csv(ARQ_EMAILS,index=False,encoding='utf-8')
                    st.success(f"{email_del} excluído"); st.rerun()

st.caption(f"{agora.strftime('%d/%m/%Y %H:%M:%S')} | CONTROLE DE ACESSO ATIVO")
