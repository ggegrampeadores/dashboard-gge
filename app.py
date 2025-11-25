import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --- Configurações da Página ---
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Anúncios GGE (v2.1 - Filtros)")

# --- Conexão e Busca de Dados (com cache) ---
# @st.cache_data é um "decorador" que armazena o resultado da função em cache.
# Isso significa que o app não vai recarregar os dados do banco a cada interação.
@st.cache_data
def fetch_data():
    try:
        db_url = st.secrets["database_url"]
        engine = create_engine(db_url)
        query = 'SELECT * FROM "Anuncios";'
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar os dados: {e}")
        return pd.DataFrame()

# --- Execução Principal ---
df_anuncios_master = fetch_data()

if not df_anuncios_master.empty:
    st.success(f"{len(df_anuncios_master)} anúncio(s) carregado(s) com sucesso do Supabase!")

    # --- Seção de Filtros ---
    st.sidebar.header("Filtros")

    # Filtro por SKU (busca de texto)
    sku_filter = st.sidebar.text_input("Buscar por SKU")

    # Filtro por Status (menu de seleção múltipla)
    # Pegamos as opções únicas da coluna 'status' e adicionamos "Todos"
    status_options = ["Todos"] + df_anuncios_master['status'].unique().tolist()
    status_filter = st.sidebar.selectbox("Filtrar por Status", options=status_options)

    # Filtro por Tipo de Anúncio (menu de seleção)
    tipo_options = ["Todos"] + df_anuncios_master['tipo_anuncio'].unique().tolist()
    tipo_filter = st.sidebar.selectbox("Filtrar por Tipo de Anúncio", options=tipo_options)

    # --- Aplicação dos Filtros ---
    df_filtrado = df_anuncios_master.copy() # Começamos com uma cópia do dataframe original

    # Aplicar filtro de SKU
    if sku_filter:
        # Filtra linhas onde a coluna 'sku' contém o texto digitado (ignorando maiúsculas/minúsculas)
        df_filtrado = df_filtrado[df_filtrado['sku'].str.contains(sku_filter, case=False, na=False)]

    # Aplicar filtro de Status
    if status_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == status_filter]

    # Aplicar filtro de Tipo de Anúncio
    if tipo_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_anuncio'] == tipo_filter]


    # --- Exibição dos Dados ---
    st.write("### Visão Geral dos Anúncios")
    st.dataframe(df_filtrado)

else:
    st.warning("Nenhum dado de anúncio foi encontrado na base de dados.")

