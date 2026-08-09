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

# Abas do Banco de Dados
aba_base = planilha.worksheet("Base_Atletas")
aba_brutos = planilha.worksheet("Dados_Brutos")

df_base = pd.DataFrame(aba_base.get_all_records())
df_brutos = pd.DataFrame(aba_brutos.get_all_records())

# ==========================================
# 2. INTERFACE DE AVALIAÇÃO DO MESTRE
# ==========================================
st.write("## Avaliação da Roda")

# Seletor de Fase do Campeonato (Mata-mata)
fases_campeonato = ["Eliminatórias", "Oitavas de Final", "Quartas de Final", "Semifinal", "Final"]
fase_atual = st.selectbox("Fase Atual do Campeonato:", fases_campeonato)

# Identificação do Mestre (permite N avaliadores simultâneos)
nome_avaliador = st.selectbox("Quem é você?", ["Selecione...", "Mestre 1", "Mestre 2", "Mestre 3", "Mestre 4", "Mestre 5", "Mestre 6"])

# Lista de Golpes Sujos conforme regulamento
lista_infrações = [
    "Cabeçadas traumatizantes",
    "Agarrões (baianada, pilão, bate estaca)",
    "Cotoveladas",
    "Forquilha (dedo nos olhos)",
    "Galopante",
    "Telefone",
    "Socos",
    "Asfixiante",
    "Chaves",
    "Golpes baixos atingindo genitais"
]

if nome_avaliador != "Selecione...":
    
    # Lógica de contagem de votos ISOLADA POR FASE
    if not df_brutos.empty and 'Nome do Atleta' in df_brutos.columns and 'Fase' in df_brutos.columns:
        # Filtra os votos apenas da fase selecionada no momento
        votos_na_fase = df_brutos[df_brutos['Fase'] == fase_atual]
        contagem_votos = votos_na_fase['Nome do Atleta'].value_counts()
    else:
        contagem_votos = {}
    
    # Atletas que ainda não têm 3 avaliações nesta fase específica
    atletas_disponiveis = [
        atleta for atleta in df_base['Nome'] 
        if contagem_votos.get(atleta, 0) < 3
    ]

    st.write("---")
    st.write("### Selecione a Dupla (Digite o número da camisa)")
    
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
            # Travas de 5.0 a 10.0 aplicadas
            t1 = st.number_input("Tradição", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="t1")
            v1 = st.number_input("Volume", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="v1")
            tc1 = st.number_input("Técnica", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="tc1")
            
            # Caixa de seleção múltipla para golpes sujos (sem perda de pontos)
            faltas_1 = st.multiselect("Registrar Golpe Sujo (Não subtrai pontos):", lista_infrações, key="f1")
            faltas_str_1 = " | ".join(faltas_1) if faltas_1 else "Nenhuma"
            
        with col_notas_2:
            st.write(f"**Notas: {atleta_2}**")
            t2 = st.number_input("Tradição", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="t2")
            v2 = st.number_input("Volume", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="v2")
            tc2 = st.number_input("Técnica", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="tc2")
            
            faltas_2 = st.multiselect("Registrar Golpe Sujo (Não subtrai pontos):", lista_infrações, key="f2")
            faltas_str_2 = " | ".join(faltas_2) if faltas_2 else "Nenhuma"

        if st.button("Enviar Notas do Jogo"):
            data_hora = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Formato de envio alinhado com as colunas (A a I)
            # [Data, Avaliador, Atleta, Categoria, Tradição, Volume, Técnica, Fase, Faltas]
            linha_1 = [data_hora, nome_avaliador, atleta_1, "", t1, v1, tc1, fase_atual, faltas_str_1]
            linha_2 = [data_hora, nome_avaliador, atleta_2, "", t2, v2, tc2, fase_atual, faltas_str_2]
            
            aba_brutos.append_row(linha_1)
            aba_brutos.append_row(linha_2)
            
            st.success(f"Notas registradas para a fase: {fase_atual}! Atualizando painel...")
            st.rerun()
