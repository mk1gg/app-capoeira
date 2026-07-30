import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sistema de Notas - Capoeira", layout="centered")

st.title("🏆 Avaliação & Ranking")

# Lista oficial extraída do regulamento (Categorias A até Q)
categorias_oficiais = [
    "A) INFANTIL A - até 11 anos de idade - MASCULINO",
    "B) INFANTIL A - até 11 anos de idade - FEMININO",
    "C) INFANTIL B - 12 até 14 anos de idade - MASCULINO",
    "D) INFANTIL B - 12 até 14 anos de idade - FEMININO",
    "E) JOVENS E ADULTOS - 15 A 17 ANOS - iniciante até 3ª grad. - MASCULINO",
    "F) JOVENS E ADULTOS - 15 A 17 ANOS - iniciante até 3ª grad. - FEMININO",
    "G) JOVENS E ADULTOS - ACIMA DE 18 - iniciante até 3ª grad. - MASCULINO",
    "H) JOVENS E ADULTOS - ACIMA DE 18 - iniciante até 3ª grad. - FEMININO",
    "I) JOVENS E ADULTOS - 4ª graduação até Graduado - MASCULINO",
    "J) JOVENS E ADULTOS - 4ª graduação até Graduado - FEMININO",
    "K) JOVENS E ADULTOS - Instrutor até Professor - MASCULINO",
    "L) JOVENS E ADULTOS - Instrutor até Professor - FEMININO",
    "M) JOVENS E ADULTOS - Contramestre até Mestrando - MASCULINO",
    "N) JOVENS E ADULTOS - Contramestre até Mestrando - FEMININO",
    "O) Categoria ESPECIAL A - 45 anos acima - Iniciante",
    "P) Categoria ESPECIAL B - 45 anos acima - Graduação avançada até Instrutor",
    "Q) Categoria ESPECIAL C - 45 anos acima - Professor até Mestrando"
]

st.info("Para começar, faça o upload da planilha de inscritos. Ela deve conter as colunas exatas: **Nº**, **Nome** e **Categoria**.")

arquivo = st.file_uploader("📥 Carregar Planilha (Excel ou CSV)", type=["xlsx", "csv"])

if arquivo:
    try:
        if arquivo.name.endswith('.csv'):
            df_atletas = pd.read_csv(arquivo)
        else:
            df_atletas = pd.read_excel(arquivo)
            
        tab1, tab2 = st.tabs(["📝 Avaliar Bateria", "📊 Ranking Geral"])
        
        # ABA 1: TELA DO AVALIADOR
        with tab1:
            st.subheader("Bateria Atual")
            
            # O menu agora exibe as categorias unificadas A-Q
            cat_selecionada = st.selectbox("1. Escolha a Categoria da Bateria", categorias_oficiais)
            
            # Filtra os atletas que pertencem a essa categoria
            if "Categoria" in df_atletas.columns:
                atletas_filtrados = df_atletas[df_atletas["Categoria"] == cat_selecionada]
                lista_competidores = (atletas_filtrados["Nº"].astype(str) + " - " + atletas_filtrados["Nome"]).tolist()
            else:
                st.error("A sua planilha não possui a coluna 'Categoria'. Corrija a planilha e tente novamente.")
                lista_competidores = []
            
            st.write("---")
            col1, col2 = st.columns(2)
            
            with col1:
                comp1 = st.selectbox("Competidor 1", lista_competidores, key="c1")
            with col2:
                comp2 = st.selectbox("Competidor 2", lista_competidores, key="c2")
                
            st.write("---")
            # Barras de avaliação atualizadas para números inteiros (step=1)
            st.subheader("Critérios de Avaliação (Notas Inteiras de 5 a 10)")
            tradicao = st.slider("A) Tradição (Fundamentos e rituais)", 5, 10, 7, 1)
            volume = st.slider("B) Volume de Jogo (Golpes e criatividade)", 5, 10, 7, 1)
            tecnica = st.slider("C) Técnica (Movimentos corretos e físicos)", 5, 10, 7, 1)
            
            if st.button("ENVIAR AVALIAÇÃO", use_container_width=True):
                st.success("✅ Notas enviadas para a dupla selecionada!")

        # ABA 2: TELA DO RANKING
        with tab2:
            st.subheader("Ranking da Categoria")
            filtro_cat = st.selectbox("Ver ranking da Categoria:", categorias_oficiais, key="rcat")
            
            st.info("Interface finalizada. A exibição do ranking aguarda a futura integração com o banco de dados do Google Sheets.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler a planilha. Verifique as colunas. Erro: {e}")
else:
    st.warning("⚠️ O sistema está bloqueado. Faça o upload da planilha acima para liberar as abas de avaliação e ranking.")
