import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. AUTENTICAÇÃO E CONEXÃO COM O GOOGLE SHEETS
# ==========================================
escopos = ['https://www.googleapis.com/auth/spreadsheets']
credenciais_dict = dict(st.secrets["gcp_service_account"])
credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
cliente = gspread.authorize(credenciais)

# Substitua pelo ID real da sua planilha
ID_PLANILHA = "1-OfCbo6PyGnU1J5l1akeidIdqQOR4N3VBakvwiOe344"
planilha = cliente.open_by_key(ID_PLANILHA)

# Puxando as abas
aba_base = planilha.worksheet("Base_Atletas")
aba_brutos = planilha.worksheet("Dados_Brutos")

# Transformando em tabelas
df_base = pd.DataFrame(aba_base.get_all_records())
df_brutos = pd.DataFrame(aba_brutos.get_all_records())


# ==========================================
# 2. INTERFACE E LÓGICA DE AVALIAÇÃO
# ==========================================
st.write("## Avaliação da Roda")

nome_avaliador = st.selectbox("Quem é você?", ["Selecione...", "Mestre 1", "Mestre 2", "Mestre 3"])

if nome_avaliador != "Selecione...":
    
    # Lógica de contagem de votos para sumir com o nome
    if not df_brutos.empty and 'Nome do Atleta' in df_brutos.columns:
        contagem_votos = df_brutos['Nome do Atleta'].value_counts()
    else:
        contagem_votos = {}
    
    # Filtra quem tem menos de 3 votos
    atletas_disponiveis = [
        atleta for atleta in df_base['Nome'] 
        if contagem_votos.get(atleta, 0) < 3
    ]

    st.write("---")
    st.write("### Selecione o Jogo (Digite o número da camisa)")
    
    colA, colB = st.columns(2)
    with colA:
        atleta_1 = st.selectbox("Atleta 1:", ["Selecione..."] + atletas_disponiveis, key="a1")
    with colB:
        atleta_2 = st.selectbox("Atleta 2:", ["Selecione..."] + atletas_disponiveis, key="a2")
        
    if atleta_1 != "Selecione..." and atleta_2 != "Selecione..." and atleta_1 != atleta_2:
        
        st.write("---")
        col_notas_1, divisor, col_notas_2 = st.columns([1, 0.1, 1])
        
        with col_notas_1:
            st.write(f"**Notas: {atleta_1}**")
            t1 = st.number_input("Tradição", 0.0, 10.0, step=0.1, key="t1")
            v1 = st.number_input("Volume", 0.0, 10.0, step=0.1, key="v1")
            tc1 = st.number_input("Técnica", 0.0, 10.0, step=0.1, key="tc1")
            
        with col_notas_2:
            st.write(f"**Notas: {atleta_2}**")
            t2 = st.number_input("Tradição", 0.0, 10.0, step=0.1, key="t2")
            v2 = st.number_input("Volume", 0.0, 10.0, step=0.1, key="v2")
            tc2 = st.number_input("Técnica", 0.0, 10.0, step=0.1, key="tc2")

        if st.button("Enviar Notas do Jogo"):
            
            # Pega a data e hora atual
            data_hora = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Prepara as duas linhas para enviar ao Sheets
            linha_atleta_1 = [data_hora, nome_avaliador, atleta_1, t1, v1, tc1]
            linha_atleta_2 = [data_hora, nome_avaliador, atleta_2, t2, v2, tc2]
            
            # Injeta na aba Dados_Brutos
            aba_brutos.append_row(linha_atleta_1)
            aba_brutos.append_row(linha_atleta_2)
            
            st.success("Notas registradas com sucesso! Atualizando painel...")
            st.rerun()
