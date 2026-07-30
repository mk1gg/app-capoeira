import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Avaliação - Campeonato de Capoeira", layout="centered")

# --- 2. CONEXÃO COM O GOOGLE SHEETS ---
def conectar_planilha():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        # As credenciais da sua conta de serviço Google (JSON) devem ficar no st.secrets do GitHub/Streamlit
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # IMPORTANTE: Substitua o texto abaixo pelo ID real da sua planilha do Google Sheets
        sheet = client.open_by_key("COLOQUE_AQUI_O_ID_DA_SUA_PLANILHA") 
        return sheet.worksheet("Dados_Brutos")
    except Exception as e:
        return None

worksheet = conectar_planilha()

# --- 3. INTERFACE PRINCIPAL ---
st.title("🏆 Campeonato de Capoeira - Avaliação")

# Identificação do Mestre e do Critério
st.header("1. Identificação do Avaliador")
col_mestre, col_criterio = st.columns(2)

with col_mestre:
    mestre_avaliador = st.text_input("Nome do Mestre/Avaliador:")

with col_criterio:
    criterio = st.selectbox("Qual critério você está avaliando?", 
                            ["Tradição", "Volume de Jogo", "Técnica"])

# Carregamento da Planilha de Atletas
st.header("2. Base de Atletas")
arquivo_upl = st.file_uploader("Carregue a planilha de atletas (Excel ou CSV)", type=["xlsx", "csv"])

if arquivo_upl is not None:
    # Leitura baseada na extensão do arquivo
    if arquivo_upl.name.endswith('.csv'):
        df_atletas = pd.read_csv(arquivo_upl)
    else:
        df_atletas = pd.read_excel(arquivo_upl)
    
    # Verificação das colunas obrigatórias
    colunas_necessarias = ['Nº', 'Nome', 'Categoria']
    if not all(col in df_atletas.columns for col in colunas_necessarias):
        st.error(f"Erro: A planilha deve conter exatamente as colunas: {', '.join(colunas_necessarias)}")
    else:
        st.success(f"Planilha carregada com sucesso! Total de atletas: {len(df_atletas)}")
        
        # --- 4. SELEÇÃO DA BATERIA ---
        st.header("3. Bateria 1x1")
        
        # Lista categorias únicas em ordem alfabética
        categorias_disponiveis = df_atletas['Categoria'].dropna().unique().tolist()
        categorias_disponiveis.sort()
        
        categoria_selecionada = st.selectbox("Selecione a Categoria da Bateria:", categorias_disponiveis)
        
        # Filtra os atletas pela categoria selecionada
        df_categoria = df_atletas[df_atletas['Categoria'] == categoria_selecionada]
        lista_nomes = df_categoria['Nome'].tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            atleta_a = st.selectbox("Atleta A:", ["Selecione..."] + lista_nomes)
        with col2:
            atleta_b = st.selectbox("Atleta B:", ["Selecione..."] + lista_nomes)
            
        if atleta_a != "Selecione..." and atleta_b != "Selecione..." and atleta_a == atleta_b:
            st.error("Erro: Selecione atletas diferentes para compor a bateria.")
            
        # --- 5. AVALIAÇÃO E NOTAS ---
        elif atleta_a != "Selecione..." and atleta_b != "Selecione...":
            st.header("4. Avaliação")
            st.info(f"Avaliando o critério: **{criterio}**")
            
            col_nota_a, col_nota_b = st.columns(2)
            
            with col_nota_a:
                st.markdown(f"### {atleta_a}")
                nota_a = st.slider(f"Nota para {atleta_a}", min_value=5, max_value=10, value=7, step=1)
                
            with col_nota_b:
                st.markdown(f"### {atleta_b}")
                nota_b = st.slider(f"Nota para {atleta_b}", min_value=5, max_value=10, value=7, step=1)
                
            # --- 6. ENVIO PARA O GOOGLE SHEETS ---
            st.markdown("---")
            if st.button("Enviar Notas", use_container_width=True, type="primary"):
                if not mestre_avaliador:
                    st.error("Atenção: O preenchimento do nome do Mestre/Avaliador é obrigatório!")
                else:
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    
                    # Separa a avaliação em duas linhas distintas para o ranking individual
                    linha_a = [agora, atleta_a, categoria_selecionada, mestre_avaliador, criterio, nota_a]
                    linha_b = [agora, atleta_b, categoria_selecionada, mestre_avaliador, criterio, nota_b]
                    
                    if worksheet:
                        try:
                            worksheet.append_rows([linha_a, linha_b])
                            st.success("✅ Notas enviadas com sucesso para a nuvem!")
                        except Exception as e:
                            st.error(f"Erro ao enviar para o Google Sheets: {e}")
                    else:
                        st.warning("⚠️ Modo de Teste: Conexão com o Google Sheets não detectada. Dados gerados:")
                        st.json([linha_a, linha_b])
