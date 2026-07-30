import streamlit as st
import pandas as pd

st.set_page_config(page_title="Capoeira CS:GO", layout="centered")

st.title("🏆 Capoeira - Avaliação & Ranking")

# A lista de graduações exatamente como você pediu
graduacoes = [
    "Aluno (Branca-Amarela)", 
    "Graduado (Azul)", 
    "Instrutor (Verde)", 
    "Professor (Roxo)", 
    "Contramestre (Marrom)", 
    "Mestrando (Preta)", 
    "Mestre (Vermelha)"
]

tab1, tab2 = st.tabs(["📝 Avaliar Bateria", "📊 Ranking (Estilo CS)"])

# ABA 1: TELA DO AVALIADOR
with tab1:
    st.subheader("Bateria Atual")
    graduacao_selecionada = st.selectbox("Graduação", graduacoes)
    
    col1, col2 = st.columns(2)
    with col1:
        comp1 = st.number_input("Nº Competidor 1", min_value=1, step=1, key="c1")
    with col2:
        comp2 = st.number_input("Nº Competidor 2", min_value=1, step=1, key="c2")
        
    st.write("---")
    st.subheader("Notas (0 a 10)")
    tecnica = st.slider("1. Técnica e Fundamentos", 0.0, 10.0, 5.0, 0.5)
    volume = st.slider("2. Volume de Jogo", 0.0, 10.0, 5.0, 0.5)
    
    st.write("---")
    st.subheader("Estatísticas Especiais ('Kills' do CS)")
    quedas = st.number_input("Quedas aplicadas (Takedowns)", min_value=0, step=1)
    floreios = st.number_input("Floreios / Acrobacias", min_value=0, step=1)

    if st.button("ENVIAR AVALIAÇÃO", use_container_width=True):
        st.success(f"✅ Notas de {comp1} x {comp2} enviadas!")

# ABA 2: TELA DO MESTRE DE CERIMÔNIAS
with tab2:
    st.subheader("Tabela de Classificação Global")
    
    filtro_grad = st.selectbox("Filtrar por Graduação", ["Todas"] + graduacoes)
    
    # Dados simulados com as novas graduações
    dados = {
        "Nº": [135, 42, 7, 88, 12, 199, 50],
        "Apelido": ["Macaco", "Vento", "Faísca", "Muralha", "Sombra", "Trovão", "Bala"],
        "Graduação": [
            "Contramestre (Marrom)", 
            "Instrutor (Verde)", 
            "Aluno (Branca-Amarela)", 
            "Mestrando (Preta)", 
            "Professor (Roxo)", 
            "Graduado (Azul)", 
            "Mestre (Vermelha)"
        ],
        "Pts Totais": [45.5, 42.0, 39.5, 45.5, 30.0, 38.0, 48.0],
        "Quedas (Kills)": [5, 2, 4, 1, 0, 3, 6],
        "Floreios (HS)": [3, 8, 2, 0, 1, 4, 5],
        "Média (ADR)": [9.1, 8.4, 7.9, 9.1, 6.0, 7.6, 9.6]
    }
    
    df = pd.DataFrame(dados)
    
    if filtro_grad != "Todas":
        df = df[df["Graduação"] == filtro_grad]
        
    df = df.sort_values(by=["Pts Totais", "Quedas (Kills)", "Floreios (HS)"], ascending=[False, False, False])
    
    # Função que pinta as células dependendo da graduação
    def colorir_graduacao(valor):
        cores = {
            "Aluno (Branca-Amarela)": "background-color: #FFFACD; color: black; font-weight: bold;",
            "Graduado (Azul)": "background-color: #0000FF; color: white; font-weight: bold;",
            "Instrutor (Verde)": "background-color: #228B22; color: white; font-weight: bold;",
            "Professor (Roxo)": "background-color: #800080; color: white; font-weight: bold;",
            "Contramestre (Marrom)": "background-color: #8B4513; color: white; font-weight: bold;",
            "Mestrando (Preta)": "background-color: #000000; color: white; font-weight: bold;",
            "Mestre (Vermelha)": "background-color: #FF0000; color: white; font-weight: bold;"
        }
        # Retorna a cor se a palavra for uma graduação, senão deixa vazio
        return cores.get(valor, "")

    # Aplica a pintura apenas na coluna "Graduação"
    tabela_colorida = df.style.map(colorir_graduacao, subset=["Graduação"])
    
    st.dataframe(tabela_colorida, hide_index=True, use_container_width=True)
