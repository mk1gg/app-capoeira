import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import math

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
    fases_ordem = [
        "Mata-mata - 1ª Rodada",
        "Mata-mata - 2ª Rodada",
        "Mata-mata - 3ª Rodada",
        "Mata-mata - 4ª Rodada",
        "Mata-mata - 5ª Rodada",
        "Mata-mata - 6ª Rodada",
        "Final"
    ]
    
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
    else:
        df_brutos = pd.DataFrame(columns=['Fase', 'Nome do Atleta', 'Tradição', 'Volume', 'Técnica', 'Nota Total', 'Punições/Faltas'])

    dados_painel = []
    grupos = df_base.groupby(['Gênero', 'Categoria', 'Subcategoria'], sort=False)
    
    for nome_grupo, grupo_df in grupos:
        gen, cat, sub = nome_grupo
        if not str(gen).strip(): 
            continue
            
        titulo_base = f"🏆 {str(gen).upper()} | {str(cat).upper()} | {str(sub).upper()}"
        tabelas_fases = []
        fase_anterior_concluida = True 
        
        for idx_fase, fase in enumerate(fases_ordem):
            df_fase = df_brutos[df_brutos['Fase'] == fase] if not df_brutos.empty and 'Fase' in df_brutos.columns else pd.DataFrame()
            tem_votos_nesta_fase = not df_fase.empty
            
            mostrar_fase = (idx_fase == 0) or tem_votos_nesta_fase or fase_anterior_concluida
            
            if not mostrar_fase:
                break
                
            if not df_fase.empty:
                ranking = df_fase.groupby('Nome do Atleta').agg(
                    Votos=('Avaliador', 'count'),
                    Pontuação_Final=('Nota Total', 'sum'),
                    Faltas=('Punições/Faltas', lambda x: ' | '.join(filter(lambda v: v != "Nenhuma" and str(v).strip() != "", x)))
                ).reset_index()
            else:
                ranking = pd.DataFrame(columns=['Nome do Atleta', 'Votos', 'Pontuação_Final', 'Faltas'])
                
            df_final = pd.merge(grupo_df, ranking, left_on='Identificador_Completo', right_on='Nome do Atleta', how='left')
            
            if idx_fase == 0:
                df_final['Votos'] = df_final['Votos'].fillna(0)
                df_final['Pontuação_Final'] = df_final['Pontuação_Final'].fillna(0)
                df_final['Faltas'] = df_final['Faltas'].fillna("Nenhuma")
            else:
                df_final = df_final[df_final['Votos'] > 0].copy()
                
            df_final['Faltas'] = df_final['Faltas'].replace("", "Nenhuma")
            df_final = df_final.sort_values(by=['Pontuação_Final'], ascending=False)
            
            tabela_atual = []
            tabela_atual.append([f"{titulo_base} - {fase.upper()}", "", "", "", ""])
            tabela_atual.append(["Número", "Nome do Atleta", "Pontuação Final", "Juízes", "Faltas"])
            
            for _, row in df_final.iterrows():
                tabela_atual.append([
                    row['Número'], 
                    row['Nome'], 
                    row['Pontuação_Final'], 
                    f"{int(row['Votos'])}/3", 
                    row['Faltas']
                ])
                
            tabelas_fases.append(tabela_atual)
            fase_anterior_concluida = all(v == 3 for v in df_final['Votos']) and len(df_final) > 0
            
        if tabelas_fases:
            max_rows = max(len(t) for t in tabelas_fases)
            
            for i in range(max_rows):
                linha_combinada = []
                for idx_t, tabela in enumerate(tabelas_fases):
                    if i < len(tabela):
                        linha_combinada.extend(tabela[i])
                    else:
                        linha_combinada.extend(["", "", "", "", ""])
                        
                    if idx_t < len(tabelas_fases) - 1:
                        linha_combinada.append("") 
                        
                dados_painel.append(linha_combinada)
                
        dados_painel.append([])
        dados_painel.append([])
        
    max_cols = max((len(row) for row in dados_painel if row), default=0)
    for row in dados_painel:
        row.extend([""] * (max_cols - len(row)))
        
    aba_painel.clear()
    if dados_painel:
        aba_painel.update("A1", dados_painel)

# ==========================================
# 3. INTERFACE DE AVALIAÇÃO DO MESTRE
# ==========================================
st.write("## Avaliação da Roda")

fases_campeonato = [
    "Mata-mata - 1ª Rodada",
    "Mata-mata - 2ª Rodada",
    "Mata-mata - 3ª Rodada",
    "Mata-mata - 4ª Rodada",
    "Mata-mata - 5ª Rodada",
    "Mata-mata - 6ª Rodada",
    "Final"
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
                
                # ==========================================
                # INTELIGÊNCIA PREDITIVA DA CHAVE
                # ==========================================
                n_atletas = len(df_base_filtrada)
                if n_atletas > 0:
                    # Calcula as rodadas matemáticas até sobrarem 2 atletas
                    rodadas_ate_final = math.ceil(math.log2(n_atletas)) if n_atletas > 1 else 1
                    nome_fase_final = fases_campeonato[rodadas_ate_final - 1] if rodadas_ate_final <= len(fases_campeonato) else "Final"
                    
                    # Verifica se o número total forma pares perfeitos até o fim
                    e_potencia_de_dois = (n_atletas & (n_atletas - 1) == 0) and n_atletas != 0
                    
                    if e_potencia_de_dois:
                        st.info(f"💡 **Dinâmica da Chave:** {n_atletas} atletas inscritos. Chaveamento perfeito. A final natural desta categoria (quando restarão 2 atletas) ocorrerá na fase **{nome_fase_final}**.")
                    else:
                        st.warning(f"⚠️ **Alerta de Repescagem:** Esta chave possui {n_atletas} atletas. Como o número é ímpar ou não divide perfeitamente até o final, em alguma virada de fase os mestres deverão avançar a nota imediatamente abaixo da linha de corte (repescagem) para que o chaveamento feche corretamente em 2 combatentes. A final desta categoria deverá ocorrer na fase **{nome_fase_final}**.")
                # ==========================================
                
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
                        
                        categoria_final = f"{genero_escolhido} - {categoria_escolhida} - {subcategoria_escolhida}"
                        
                        linha_1 = [data_hora, nome_avaliador, ident_1, categoria_final, t1, v1, tc1, fase_atual, faltas_str_1]
                        linha_2 = [data_hora, nome_avaliador, ident_2, categoria_final, t2, v2, tc2, fase_atual, faltas_str_2]
                        
                        aba_brutos.append_row(linha_1)
                        aba_brutos.append_row(linha_2)
                        
                        carregar_dados.clear()
                        atualizar_painel_de_chaves()
                        
                        votos_agora = contagem_votos.get(ident_1, 0) + 1
                        
                        if votos_agora == 3:
                            st.success(f"✅ Notas ENVIADAS! Todos os 3 mestres já votaram na dupla {atleta_1_num} e {atleta_2_num}.")
                        else:
                            st.success(f"✅ Nota enviada! (Votos registrados na dupla até agora: {votos_agora}/3)")
                            
                        st.rerun()
