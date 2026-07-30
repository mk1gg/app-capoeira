import streamlit as st
import pandas as pd

st.set_page_config(page_title="Capoeira CS:GO", layout="centered")

st.title("🏆 Avaliação & Ranking")

# A lista de graduações
graduacoes = [
    "Aluno (Branca-Amarela)", 
    "Graduado (Azul)", 
    "Instrutor (Verde)", 
    "Professor (Roxo)", 
    "Contramestre (Marrom)", 
    "Mestrando (Preta)", 
    "Mestre (Vermelha)"
]

# Nova lógica: As faixas etárias mudam dependendo da graduação escolhida!
def obter_faixas_etarias(graduacao):
    if graduacao == "Aluno (Branca-Amarela)":
        return ["Infantil", "Juvenil", "Adulto", "Sênior (Idosos)"]
    else:
        return ["Jovens Adultos", "Maiores de 40 anos"]

tab1, tab2 = st.tabs(["📝 Avaliar Bateria", "📊 Ranking (Estilo CS)"])

# ABA 1: TELA DO AVALIADOR
with tab1:
    st.subheader("Bateria Atual")
    
    # Primeiro escolhe a graduação
    graduacao_selecionada = st.selectbox("Graduação", graduacoes)
    
    # Depois o sistema carrega as idades certas para aquela graduação
    faixa_etaria_selecionada = st.selectbox("Faixa Etária", obter_faixas_etarias(graduacao_selecionada))
    
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
    st.subheader("Estatísticas ('Kills')")
    quedas = st.number_input("Quedas aplicadas (Takedowns)", min_value=0, step=1)
    floreios = st.number_input("Floreios / Acrobacias", min_value=0, step=1)

    if st.button("ENVIAR AVALIAÇÃO", use_container_width=True):
        st.success(f"✅ Notas enviadas! Categoria: {graduacao_selecionada} - {faixa_etaria_selecionada}")

# ABA 2: TELA DO MESTRE DE CERIMÔNIAS
with tab2:
    st.subheader("Tabela de Classificação")
    
    # O locutor agora filtra por duas coisas para achar a categoria exata
    filtro_grad = st.selectbox("Ver ranking da Graduação:", graduacoes)
    filtro_idade = st.selectbox("Ver ranking da Faixa Etária:", obter_faixas_etarias(filtro_grad))
    
    # Dados simulados atualizados para testar os filtros
    dados = {
        "Nº": [135, 42, 7, 88, 12, 199, 50],
        "Apelido": ["Macaco", "Vento", "Faísca", "Muralha", "Sombra", "Trovão", "Bala"],
        "Graduação": [
            "Contramestre (Marrom)", 
            "Instrutor (Verde)", 
            "Aluno (Branca-Amarela)", 
            "Mestrando (Preta)", 
            "Aluno (Branca-Amarela)", 
            "Graduado (Azul)", 
            "Mestre (Vermelha)"
        ],
        "Faixa Etária": [
            "Jovens Adultos", 
            "Maiores de 40 anos", 
            "Infantil", 
            "Jovens Adultos", 
            "Sênior (Idosos)", 
            "Jovens Adultos", 
            "Maiores de 40 anos"
        ],
        "Pts Totais": [45.5, 42.0, 39.5, 45.5, 30.0, 38.0, 48.0],
        "Quedas (Kills)": [5, 2, 4, 1, 0, 3, 6],
        "Floreios (HS)": [3, 8, 2, 0, 1, 4, 5]
    }
    
    df = pd.DataFrame(dados)
    
    # A MÁGICA DOS FILTROS: Mostra apenas quem tem a graduação E a idade escolhidas
    df_filtrado = df[(df["Graduação"] == filtro_grad) & (df["Faixa Etária"] == filtro_idade)]
        
    df_filtrado = df_filtrado.sort_values(by=["Pts Totais", "Quedas (Kills)", "Floreios (HS)"], ascending=[False, False, False])
    
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
        return cores.get(valor, "")

    tabela_colorida = df_filtrado.style.map(colorir_graduacao, subset=["Graduação"])
    
    # Se a tabela ficar vazia (não tem simulado pra todas), mostra um aviso
    if df_filtrado.empty:
        st.warning("Nenhum atleta nesta categoria (nos dados simulados atuais).")
    else:
        st.dataframe(tabela_colorida, hide_index=True, use_container_width=True)
