import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sistema de Notas - Capoeira", layout="centered")

st.title("🏆 Avaliação & Ranking")

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

# Dados fictícios embutidos diretamente no código para facilitar os testes
dados_teste = {
    "Nº": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "Nome": [
        "Joãozinho (8 anos)", "Maria (10 anos)", "Pedro (13 anos)", "Ana (14 anos)",
        "Lucas (16 anos)", "Fernanda (22 anos)", "Carlos (30 anos)", "Roberto (46 anos)",
        "Mestre Silva (50 anos)", "Instrutora Amanda (28 anos)"
    ],
    "Categoria": [
        "A) INFANTIL A - até 11 anos de idade - MASCULINO",
        "B) INFANTIL A - até 11 anos de idade - FEMININO",
        "C) INFANTIL B - 12 até 14 anos de idade - MASCULINO",
        "D) INFANTIL B - 12 até 14 anos de idade - FEMININO",
        "E) JOVENS E ADULTOS - 15 A 17 ANOS - iniciante até 3ª grad. - MASCULINO",
        "H) JOVENS E ADULTOS - ACIMA DE 18 - iniciante até 3ª grad. - FEMININO",
        "I) JOVENS E ADULTOS - 4ª graduação até Graduado - MASCULINO",
        "O) Categoria ESPECIAL A - 45 anos acima - Iniciante",
        "Q) Categoria ESPECIAL C - 45 anos acima - Professor até Mestrando",
        "L) JOVENS E ADULTOS - Instrutor até Professor - FEMININO"
    ]
}

st.info("Para começar, faça o upload da planilha de inscritos OU use os dados de teste abaixo.")

# Opção de usar os dados embutidos
usar_teste = st.checkbox("🧪 Usar dados de teste (10 atletas fictícios)")

# Upload da planilha real
arquivo = st.file_uploader("📥 Carregar Planilha (Excel ou CSV)", type=["xlsx", "csv"])

# Lógica para definir qual base de dados usar
df_atletas = None

if usar_teste:
    df_atletas = pd.DataFrame(dados_teste)
elif arquivo:
    try:
        if arquivo.name.endswith('.csv'):
            df_atletas = pd.read_csv(arquivo)
        else:
            df_atletas = pd.read_excel(arquivo)
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler a planilha. Verifique as colunas. Erro: {e}")

# Se os dados foram carregados (seja por teste ou upload), o sistema abre
if df_atletas is not None:
    tab1, tab2 = st.tabs(["📝 Avaliar Bateria", "📊 Ranking Geral"])
    
    # ABA 1: TELA DO AVALIADOR
    with tab1:
        st.subheader("Bateria Atual")
        
        # O menu exibe as categorias unificadas A-Q
        cat_selecionada = st.selectbox("1. Escolha a Categoria da Bateria", categorias_oficiais)
        
        # Filtra os atletas que pertencem a essa categoria
        if "Categoria" in df_atletas.columns:
            atletas_filtrados = df_atletas[df_atletas["Categoria"] == cat_selecionada]
            lista_competidores = (atletas_filtrados["Nº"].astype(str) + " - " + atletas_filtrados["Nome"]).tolist()
        else:
            st.error("A sua base de dados não possui a coluna 'Categoria'.")
            lista_competidores = []
        
        st.write("---")
        
        if len(lista_competidores) == 0:
            st.warning("Nenhum atleta inscrito nesta categoria.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                comp1 = st.selectbox("Competidor 1", lista_competidores, key="c1")
            with col2:
                # Se tiver apenas 1 atleta na categoria, evita erro no segundo selectbox
                opcoes_comp2 = lista_competidores.copy()
                if len(opcoes_comp2) > 1:
                    opcoes_comp2.remove(comp1) # Tenta remover o competidor 1 da lista do 2
                comp2 = st.selectbox("Competidor 2", opcoes_comp2, key="c2")
                
            st.write("---")
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
        
else:
    st.warning("⚠️ O sistema está bloqueado. Marque a caixa de testes acima ou faça o upload da planilha para liberar as abas de avaliação e ranking.")
