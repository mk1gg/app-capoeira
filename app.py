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

ID_PLANILHA = "1-OfCbo6PyGnU1J5l1akeidIdqQOR4N3VBakvwiOe344"
planilha = cliente.open_by_key(ID_PLANILHA)

aba_base = planilha.worksheet("Base_Atletas")
aba_brutos = planilha.worksheet("Dados_Brutos")
aba_painel = planilha.worksheet("Painel_de_Chaves")

# ==========================================
# 2. MOTOR DE ATUALIZAÇÃO DO PAINEL (AUTOMÁTICO)
# ==========================================
def atualizar_painel_de_chaves():
    # Puxa os dados brutos atualizados
    dados = aba_brutos.get_all_records()
    if not dados:
        return
    
    df = pd.DataFrame(dados)
    
    # Garante que as colunas de notas são numéricas
    for col in ['Tradição', 'Volume', 'Técnica']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    # Cria uma coluna de Nota Total
    df['Nota Total'] = df['Tradição'] + df['Volume'] + df['Técnica']
    
    # Agrupa por Fase, Categoria e Atleta para somar as notas dos 3 juízes
    ranking = df.groupby(['Fase', 'Categoria', 'Nome do Atleta']).agg(
        Votos=('Avaliador', 'count'),
        Pontuação_Final=('Nota Total', 'sum'),
        Faltas=('Punições/Faltas', lambda x: ' | '.join(filter(lambda v: v != "Nenhuma" and str(v).strip() != "", x)))
    ).reset_index()
    
    # Ordena os atletas para que os com maior pontuação fiquem no topo
    ranking = ranking.sort_values(by=['Fase', 'Categoria', 'Pontuação_Final'], ascending=[True, True, False])
    
    # Limpa a aba Painel_de_Chaves e escreve o novo ranking formatado
    aba_painel.clear()
    aba_painel.update([ranking.columns.values.tolist()] + ranking.values.tolist())

# ==========================================
# 3. INTERFACE DE AVALIAÇÃO DO MESTRE
# ==========================================
st.write("## Avaliação da Roda")

fases_campeonato = ["Eliminatórias", "Oitavas de Final", "Quartas de Final", "Semifinal", "Final"]
fase_atual = st.selectbox("Fase Atual do Campeonato:", fases_campeonato)

nome_avaliador = st.selectbox("Quem é você?", ["Selecione...", "Mestre 1", "Mestre 2", "Mestre 3", "Mestre 4", "Mestre 5", "Mestre 6"])

lista_infrações = [
    "Cabeçadas traumatizantes", "Agarrões (baianada, pilão, bate estaca)", "Cotoveladas",
    "Forquilha (dedo nos olhos)", "Galopante", "Telefone", "Socos",
    "Asfixiante", "Chaves", "Golpes baixos atingindo genitais"
]

if nome_avaliador != "Selecione...":
    df_base = pd.DataFrame(aba_base.get_all_records())
    df_brutos = pd.DataFrame(aba_brutos.get_all_records())
    
    # Lógica de contagem de votos isolada por fase
    if not df_brutos.empty and 'Nome do Atleta' in df_brutos.columns and 'Fase' in df_brutos.columns:
        votos_na_fase = df_brutos[df_brutos['Fase'] == fase_atual]
        contagem_votos = votos_na_fase['Nome do Atleta'].value_counts()
    else:
        contagem_votos = {}
    
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
        
        # Puxa a categoria dos atletas para registrar junto com a nota
        categoria_a1 = df_base.loc[df_base['Nome'] == atleta_1, 'Categoria'].values[0] if 'Categoria' in df_base.columns else ""
        categoria_a2 = df_base.loc[df_base['Nome'] == atleta_2, 'Categoria'].values[0] if 'Categoria' in df_base.columns else ""

        st.write("---")
        col_notas_1, divisor, col_notas_2 = st.columns([1, 0.1, 1])
        
        with col_notas_1:
            st.write(f"**Notas: {atleta_1}**")
            t1 = st.number_input("Tradição", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="t1")
            v1 = st.number_input("Volume", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="v1")
            tc1 = st.number_input("Técnica", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="tc1")
            faltas_1 = st.multiselect("Registrar Golpe Sujo:", lista_infrações, key="f1")
            faltas_str_1 = " | ".join(faltas_1) if faltas_1 else "Nenhuma"
            
        with col_notas_2:
            st.write(f"**Notas: {atleta_2}**")
            t2 = st.number_input("Tradição", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="t2")
            v2 = st.number_input("Volume", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="v2")
            tc2 = st.number_input("Técnica", min_value=5.0, max_value=10.0, value=5.0, step=0.1, key="tc2")
            faltas_2 = st.multiselect("Registrar Golpe Sujo:", lista_infrações, key="f2")
            faltas_str_2 = " | ".join(faltas_2) if faltas_2 else "Nenhuma"

        if st.button("Enviar Notas do Jogo"):
            data_hora = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
            
            linha_1 = [data_hora, nome_avaliador, atleta_1, categoria_a1, t1, v1, tc1, fase_atual, faltas_str_1]
            linha_2 = [data_hora, nome_avaliador, atleta_2, categoria_a2, t2, v2, tc2, fase_atual, faltas_str_2]
            
            aba_brutos.append_row(linha_1)
            aba_brutos.append_row(linha_2)
            
            # Aciona o motor automático para reescrever as chaves na planilha visual
            atualizar_painel_de_chaves()
            
            st.success(f"Notas registradas! Painel de chaves atualizado com sucesso.")
            st.rerun()
