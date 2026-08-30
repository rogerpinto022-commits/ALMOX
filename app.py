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
    lotes_vivos = [l for l in lotes_ordenados if l[0] not in lotes_zerados or
