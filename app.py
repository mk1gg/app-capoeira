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
    return (planilha.worksheet("Base_Atletas"), 
            planilha.worksheet("Dados_Brutos"), 
            planilha.worksheet("Painel_de_Chaves"),
            planilha.worksheet("Finalistas"))

aba_base, aba_brutos, aba_painel, aba_finalistas = conectar_sheets()

@st.cache_data(ttl=30) 
def carregar_dados():
    return pd.DataFrame(aba_base.get_all_records()), pd.DataFrame(aba_brutos.get_all_records())

# ==========================================
# 2. MOTOR CENTRAL (ATUALIZA CHAVES E FINALISTAS)
# ==========================================
def atualizar_paineis_e_chaves():
    base_records = aba_base.get_all_records()
    brutos_records = aba_brutos.get_all_records()
    
    if not base_records:
        return
        
    df_base = pd.DataFrame(base_records)
    for col in ['Gênero', 'Categoria', 'Subcategoria', 'Nome', 'Número']:
        if col in df_base.columns:
            df_base[col] = df_base[col].astype(str).str.strip()
            
    df_base['Identificador_Completo'] = df_base['Número'] + " - " + df_base['Nome']
    
    if brutos_records:
        df_brutos = pd.DataFrame(brutos_records)
        for col in ['Tradição', 'Volume', 'Técnica']:
            df_brutos[col] = pd.to_numeric(df_brutos[col], errors='coerce').fillna(0)
        df_brutos['Nota Total'] = df_brutos['Tradição'] + df_brutos['Volume'] + df_brutos['Técnica']
        
        # Rastreador para saber se os atletas já estão disputando a Final oficial
        df_brutos['É_Final'] = df_brutos['Fase'] == 'Final'
        
        ranking = df_brutos.groupby('Nome do Atleta').agg(
            Votos_Gerais=('Avaliador', 'count'),
            Pontuação_Acumulada=('Nota Total', 'sum'),
            Faltas=('Punições/Faltas', lambda x: ' | '.join(filter(lambda v: v != "Nenhuma" and str(v).strip() != "", x))),
            Jogou_Final=('É_Final', 'sum')
        ).reset_index()
    else:
        ranking = pd.DataFrame(columns=['Nome do Atleta', 'Votos_Gerais', 'Pontuação_Acumulada', 'Faltas', 'Jogou_Final'])

    df_final = pd.merge(df_base, ranking, left_on='Identificador_Completo', right_on='Nome do Atleta', how='left')
    
    df_final['Votos_Gerais'] = df_final['Votos_Gerais'].fillna(0)
    df_final['Pontuação_Acumulada'] = df_final['Pontuação_Acumulada'].fillna(0)
    df_final['Faltas'] = df_final['Faltas'].fillna("Nenhuma")
    df_final['Faltas'] = df_final['Faltas'].replace("", "Nenhuma")
    df_final['Jogou_Final'] = df_final['Jogou_Final'].fillna(0)
    
    df_final = df_final.sort_values(by=['Pontuação_Acumulada'], ascending=False)
    
    dados_chaves = []
    dados_finalistas = []
    
    grupos = df_final.groupby(['Gênero', 'Categoria', 'Subcategoria'], sort=False)
    
    for nome_grupo, grupo_df in grupos:
        gen, cat, sub = nome_grupo
        if not str(gen).strip(): continue
            
        titulo_bloco = f"🏆 {str(gen).upper()} | {str(cat).upper()} | {str(sub).upper()}"
        
        # 1. ESCREVE O PAINEL DE CHAVES (SOMA CUMULATIVA)
        dados_chaves.append([titulo_bloco, "", "", "", ""])
        dados_chaves.append(["Número", "Nome do Atleta", "Pontuação Acumulada", "Total de Votos", "Faltas"])
        
        for _, row in grupo_df.iterrows():
            dados_chaves.append([
                row['Número'], 
                row['Nome'], 
                row['Pontuação_Acumulada'], 
                int(row['Votos_Gerais']), 
                row['Faltas']
            ])
        dados_chaves.append(["", "", "", "", ""])
        dados_chaves.append(["", "", "", "", ""])
        
        # 2. ESCREVE O PAINEL DO LOCUTOR (COM TRAVA DE EXIBIÇÃO)
        total_atletas_categoria = len(grupo_df)
        top2 = grupo_df.head(2)
        
        # Só exibe se a categoria for muito pequena (<=2) ou se eles já receberam votos na "Final"
        ja_chegaram_na_final = top2['Jogou_Final'].sum() > 0
        
        if not top2.empty and (total_atletas_categoria <= 2 or ja_chegaram_na_final):
            dados_finalistas.append([f"🎤 {str(gen).upper()} | {str(cat).upper()} | {str(sub).upper()}", "", ""])
            dados_finalistas.append(["Nº", "Nome do Capoeirista", "Status"])
            
            for i, (_, row) in enumerate(top2.iterrows()):
                # Se o atleta já recebeu 3 notas na fase "Final", ele é coroado. Se não, é finalista.
                if row['Jogou_Final'] >= 3:
                    status = "🏆 CAMPEÃO" if i == 0 else "🥈 VICE-CAMPEÃO"
                else:
                    status = "FINALISTA"
                    
                dados_finalistas.append([row['Número'], row['Nome'], status])
                
            dados_finalistas.append(["", "", ""])
            dados_finalistas.append(["", "", ""])

    aba_painel.clear()
    if dados_chaves: aba_painel.update("A1", dados_chaves)
        
    aba_finalistas.clear()
    if dados_finalistas: aba_finalistas.update("A1", dados_finalistas)

# ==========================================
# 3. INTERFACE DE AVALIAÇÃO DO MESTRE
# ==========================================
st.write("## Avaliação da Roda")

fases_campeonato = [
    "Mata-mata - 1ª Rodada", "Mata-mata - 2ª Rodada", "Mata-mata - 3ª Rodada",
    "Mata-mata - 4ª Rodada", "Mata-mata - 5ª Rodada", "Mata-mata - 6ª Rodada", "Final"
]
fase_atual = st.selectbox("Fase Atual do Campeonato:", fases_campeonato)

nome_avaliador = st.text_input("Digite o seu nome de Avaliador:")
criterio_avaliador = st.selectbox("Qual critério você está avaliando?", ["Selecione...", "Tradição", "Volume", "Técnica"])

lista_infrações = [
    "Cabeçadas traumatizantes", "Agarrões (baianada, pilão, bate estaca)", "Cotoveladas",
    "Forquilha (dedo nos olhos)", "Galopante", "Telefone", "Socos",
    "Asfixiante", "Chaves", "Golpes baixos atingindo genitais"
]

if nome_avaliador.strip() != "" and criterio_avaliador != "Selecione...":
    df_base, df_brutos = carregar_dados()
    
    if 'Subcategoria' not in df_base.columns or 'Gênero' not in df_base.columns:
        st.error("⚠️ Atenção: Certifique-se de que as colunas 'Gênero' e 'Subcategoria' existam na aba 'Base_Atletas'.")
        st.stop()
        
    df_base['Num_Str'] = df_base['Número'].astype(str).str.strip()
    df_base['Nome'] = df_base['Nome'].astype(str).str.strip()
    df_base['Identificador_Completo'] = df_base['Num_Str'] + " - " + df_base['Nome']
    df_base['Gênero'] = df_base['Gênero'].astype(str).str.strip()
    df_base['Categoria'] = df_base['Categoria'].astype(str).str.strip()
    df_base['Subcategoria'] = df_base['Subcategoria'].astype(str).str.strip()
    
    st.write("---")
    
    generos_existentes = [g for g in df_base['Gênero'].unique().tolist() if g != ""]
    genero_escolhido = st.selectbox("Selecione o Gênero:", ["Selecione..."] + sorted(generos_existentes))
    
    if genero_escolhido != "Selecione...":
        df_base_gen = df_base[df_base['Gênero'] == genero_escolhido]
        
        categorias_existentes = [c for c in df_base_gen['Categoria'].unique().tolist() if c != ""]
        categoria_escolhida = st.selectbox("Selecione a Categoria:", ["Selecione..."] + sorted(categorias_existentes))
        
        if categoria_escolhida != "Selecione...":
            df_base_cat = df_base_gen[df_base_gen['Categoria'] == categoria_escolhida]
            
            subcategorias_existentes = [s for s in df_base_cat['Subcategoria'].unique().tolist() if s != ""]
            subcategoria_escolhida = st.selectbox("Selecione a Subcategoria:", ["Selecione..."] + sorted(subcategorias_existentes))
            
            if subcategoria_escolhida != "Selecione...":
                df_base_filtrada = df_base_cat[df_base_cat['Subcategoria'] == subcategoria_escolhida]
                
                # Bloqueio de votos duplos na MESMA fase
                if not df_brutos.empty and 'Nome do Atleta' in df_brutos.columns and 'Fase' in df_brutos.columns and 'Avaliador' in df_brutos.columns:
                    votos_na_fase = df_brutos[df_brutos['Fase'] == fase_atual]
                    contagem_votos = votos_na_fase['Nome do Atleta'].astype(str).str.strip().value_counts()
                    nome_formatado = nome_avaliador.strip()
                    votos_deste_avaliador = votos_na_fase[votos_na_fase['Avaliador'].astype(str).str.strip() == nome_formatado]
                    ja_avaliados_por_mim = votos_deste_avaliador['Nome do Atleta'].astype(str).str.strip().unique().tolist()
                else:
                    contagem_votos = {}
                    ja_avaliados_por_mim = []
                
                numeros_disponiveis = [
                    num for num, ident in zip(df_base_filtrada['Num_Str'], df_base_filtrada['Identificador_Completo'])
                    if contagem_votos.get(ident, 0) < 3 and ident not in ja_avaliados_por_mim
                ]

                st.write("### Selecione a Dupla (Pelo número da camisa)")
                
                colA, colB = st.columns(2)
                with colA:
                    atleta_1_num = st.selectbox("Atleta 1 (Número):", ["Selecione..."] + numeros_disponiveis, key="a1")
                
                with colB:
                    se_escolhido = [n for n in numeros_disponiveis if n != atleta_1_num] if atleta_1_num != "Selecione..." else numeros_disponiveis
                    atleta_2_num = st.selectbox("Atleta 2 (Número):", ["Selecione..."] + se_escolhido, key="a2")
                    
                if atleta_1_num != "Selecione..." and atleta_2_num != "Selecione...":
                    
                    ident_1 = df_base_filtrada.loc[df_base_filtrada['Num_Str'] == atleta_1_num, 'Identificador_Completo'].values[0]
                    ident_2 = df_base_filtrada.loc[df_base_filtrada['Num_Str'] == atleta_2_num, 'Identificador_Completo'].values[0]

                    st.write("---")
                    col_notas_1, divisor, col_notas_2 = st.columns([1, 0.1, 1])
                    
                    t1, v1, tc1 = 0, 0, 0
                    t2, v2, tc2 = 0, 0, 0
                    
                    with col_notas_1:
                        st.write(f"**Notas do Nº {atleta_1_num}**")
                        if criterio_avaliador == "Tradição": t1 = st.number_input("Tradição", min_value=5, max_value=10, value=5, step=1, key="t1")
                        elif criterio_avaliador == "Volume": v1 = st.number_input("Volume", min_value=5, max_value=10, value=5, step=1, key="v1")
                        elif criterio_avaliador == "Técnica": tc1 = st.number_input("Técnica", min_value=5, max_value=10, value=5, step=1, key="tc1")
                        
                        faltas_1 = st.multiselect("Registrar Golpe Sujo:", lista_infrações, key="f1")
                        faltas_str_1 = " | ".join(faltas_1) if faltas_1 else "Nenhuma"
                        
                    with col_notas_2:
                        st.write(f"**Notas do Nº {atleta_2_num}**")
                        if criterio_avaliador == "Tradição": t2 = st.number_input("Tradição", min_value=5, max_value=10, value=5, step=1, key="t2")
                        elif criterio_avaliador == "Volume": v2 = st.number_input("Volume", min_value=5, max_value=10, value=5, step=1, key="v2")
                        elif criterio_avaliador == "Técnica": tc2 = st.number_input("Técnica", min_value=5, max_value=10, value=5, step=1, key="tc2")
                            
                        faltas_2 = st.multiselect("Registrar Golpe Sujo:", lista_infrações, key="f2")
                        faltas_str_2 = " | ".join(faltas_2) if faltas_2 else "Nenhuma"

                    if st.button("Enviar Notas do Jogo"):
                        data_hora = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")
                        
                        categoria_final = f"{genero_escolhido} - {categoria_escolhida} - {subcategoria_escolhida}"
                        
                        linha_1 = [data_hora, nome_avaliador, ident_1, categoria_final, t1, v1, tc1, fase_atual, faltas_str_1]
                        linha_2 = [data_hora, nome_avaliador, ident_2, categoria_final, t2, v2, tc2, fase_atual, faltas_str_2]
                        
                        aba_brutos.append_row(linha_1)
                        aba_brutos.append_row(linha_2)
                        
                        carregar_dados.clear()
                        atualizar_paineis_e_chaves()
                        
                        votos_agora = contagem_votos.get(ident_1, 0) + 1
                        
                        if votos_agora == 3:
                            st.success(f"✅ Notas ENVIADAS! Todos os 3 mestres já votaram na dupla {atleta_1_num} e {atleta_2_num} na {fase_atual}.")
                        else:
                            st.success(f"✅ Nota enviada! (Votos registrados na dupla nesta fase: {votos_agora}/3)")
                            
                        st.rerun()
