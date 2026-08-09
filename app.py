import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. AUTENTICAÇÃO E CONEXÃO COM CACHE
# ==========================================
@st.cache_resource
def conectar_sheets():
    escopos = ['https://www.googleapis.com/auth/spreadsheets']
    credenciais_dict = dict(st.secrets["gcp_service_account"])
    credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente = gspread.authorize(credenciais)
    planilha = cliente.open_by_key("1-OfCbo6PyGnU1J5l1akeidIdqQOR4N3VBakvwiOe344")
    return planilha.worksheet("Base_Atletas"), planilha.worksheet("Dados_Brutos"), planilha.worksheet("Painel_de_Chaves")

aba_base, aba_brutos, aba_painel = conectar_sheets()

@st.cache_data(ttl=30) 
def carregar_dados():
    return pd.DataFrame(aba_base.get_all_records()), pd.DataFrame(aba_brutos.get_all_records())

# ==========================================
# 2. MOTOR DE ATUALIZAÇÃO DO PAINEL
# ==========================================
def atualizar_painel_de_chaves():
    dados = aba_brutos.get_all_records()
    if not dados:
        return
    
    df = pd.DataFrame(dados)
    
    for col in ['Tradição', 'Volume', 'Técnica']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    df['Nota Total'] = df['Tradição'] + df['Volume'] + df['Técnica']
    
    ranking = df.groupby(['Fase', 'Categoria', 'Nome do Atleta']).agg(
        Votos=('Avaliador', 'count'),
        Pontuação_Final=('Nota Total', 'sum'),
        Faltas=('Punições/Faltas', lambda x: ' | '.join(filter(lambda v: v != "Nenhuma" and str(v).strip() != "", x)))
    ).reset_index()
    
    ranking = ranking.sort_values(by=['Fase', 'Categoria', 'Pontuação_Final'], ascending=[True, True, False])
    
    aba_painel.clear()
    aba_painel.update([ranking.columns.values.tolist()] + ranking.values.tolist())

# ==========================================
# 3. INTERFACE DE AVALIAÇÃO DO MESTRE
# ==========================================
st.write("## Avaliação da Roda")

fases_campeonato = ["Eliminatórias", "Oitavas de Final", "Quartas de Final", "Semifinal", "Final"]
fase_atual = st.selectbox("Fase Atual do Campeonato:", fases_campeonato)

nome_avaliador = st.text_input("Digite o seu nome de Avaliador:")

# Novo seletor de especialidade do avaliador
criterio_avaliador = st.selectbox("Qual critério você está avaliando?", ["Selecione...", "Tradição", "Volume", "Técnica"])

lista_infrações = [
    "Cabeçadas traumatizantes", "Agarrões (baianada, pilão, bate estaca)", "Cotoveladas",
    "Forquilha (dedo nos olhos)", "Galopante", "Telefone", "Socos",
    "Asfixiante", "Chaves", "Golpes baixos atingindo genitais"
]

if nome_avaliador.strip() != "" and criterio_avaliador != "Selecione...":
    df_base, df_brutos = carregar_dados()
    
    df_base['Num_Str'] = df_base['Número'].astype(str).str.strip()
    df_base['Nome'] = df_base['Nome'].astype(str).str.strip()
    df_base['Identificador_Completo'] = df_base['Num_Str'] + " - " + df_base['Nome']
    
    if not df_brutos.empty and 'Nome do Atleta' in df_brutos.columns and 'Fase' in df_brutos.columns:
        votos_na_fase = df_brutos[df_brutos['Fase'] == fase_atual]
        contagem_votos = votos_na_fase['Nome do Atleta'].astype(str).str.strip().value_counts()
    else:
        contagem_votos = {}
    
    # Atletas continuam sumindo quando recebem 3 votos no total
    numeros_disponiveis = [
        num for num, ident in zip(df_base['Num_Str'], df_base['Identificador_Completo'])
        if contagem_votos.get(ident, 0) < 3
    ]

    st.write("---")
    st.write("### Selecione a Dupla (Pelo número da camisa)")
    
    colA, colB = st.columns(2)
    with colA:
        atleta_1_num = st.selectbox("Atleta 1 (Número):", ["Selecione..."] + numeros_disponiveis, key="a1")
    
    with colB:
        se_escolhido = [n for n in numeros_disponiveis if n != atleta_1_num] if atleta_1_num != "Selecione..." else numeros_disponiveis
        atleta_2_num = st.selectbox("Atleta 2 (Número):", ["Selecione..."] + se_escolhido, key="a2")
        
    if atleta_1_num != "Selecione..." and atleta_2_num != "Selecione...":
        
        ident_1 = df_base.loc[df_base['Num_Str'] == atleta_1_num, 'Identificador_Completo'].values[0]
        ident_2 = df_base.loc[df_base['Num_Str'] == atleta_2_num, 'Identificador_Completo'].values[0]
        
        categoria_a1 = df_base.loc[df_base['Num_Str'] == atleta_1_num, 'Categoria'].values[0] if 'Categoria' in df_base.columns else ""
        categoria_a2 = df_base.loc[df_base['Num_Str'] == atleta_2_num, 'Categoria'].values[0] if 'Categoria' in df_base.columns else ""

        st.write("---")
        col_notas_1, divisor, col_notas_2 = st.columns([1, 0.1, 1])
        
        # Variáveis zeradas por padrão
        t1, v1, tc1 = 0, 0, 0
        t2, v2, tc2 = 0, 0, 0
        
        with col_notas_1:
            st.write(f"**Notas do Nº {atleta_1_num}**")
            # Mostra apenas o critério que o mestre escolheu avaliar
            if criterio_avaliador == "Tradição":
                t1 = st.number_input("Tradição", min_value=5, max_value=10, value=5, step=1, key="t1")
            elif criterio_avaliador == "Volume":
                v1 = st.number_input("Volume", min_value=5, max_value=10, value=5, step=1, key="v1")
            elif criterio_avaliador == "Técnica":
                tc1 = st.number_input("Técnica", min_value=5, max_value=10, value=5, step=1, key="tc1")
            
            faltas_1 = st.multiselect("Registrar Golpe Sujo:", lista_infrações, key="f1")
            faltas_str_1 = " | ".join(faltas_1) if faltas_1 else "Nenhuma"
            
        with col_notas_2:
            st.write(f"**Notas do Nº {atleta_2_num}**")
            if criterio_avaliador == "Tradição":
                t2 = st.number_input("Tradição", min_value=5, max_value=10, value=5, step=1, key="t2")
            elif criterio_avaliador == "Volume":
                v2 = st.number_input("Volume", min_value=5, max_value=10, value=5, step=1, key="v2")
            elif criterio_avaliador == "Técnica":
                tc2 = st.number_input("Técnica", min_value=5, max_value=10, value=5, step=1, key="tc2")
                
            faltas_2 = st.multiselect("Registrar Golpe Sujo:", lista_infrações, key="f2")
            faltas_str_2 = " | ".join(faltas_2) if faltas_2 else "Nenhuma"

        if st.button("Enviar Notas do Jogo"):
            data_hora = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
            
            linha_1 = [data_hora, nome_avaliador, ident_1, categoria_a1, t1, v1, tc1, fase_atual, faltas_str_1]
            linha_2 = [data_hora, nome_avaliador, ident_2, categoria_a2, t2, v2, tc2, fase_atual, faltas_str_2]
            
            aba_brutos.append_row(linha_1)
            aba_brutos.append_row(linha_2)
            
            carregar_dados.clear()
            atualizar_painel_de_chaves()
            
            st.success(f"Notas de {criterio_avaliador} registradas! Painel atualizado.")
            st.rerun()
