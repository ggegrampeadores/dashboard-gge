import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --- Configurações da Página ---
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Anúncios GGE (v2.2 - KPIs)")

# --- Conexão e Busca de Dados (com cache) ---
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
    # --- Seção de Filtros na Barra Lateral ---
    st.sidebar.header("Filtros")
    sku_filter = st.sidebar.text_input("Buscar por SKU")
    
    status_options = ["Todos"] + df_anuncios_master['status'].unique().tolist()
    status_filter = st.sidebar.selectbox("Filtrar por Status", options=status_options)

    tipo_options = ["Todos"] + df_anuncios_master['tipo_anuncio'].unique().tolist()
    tipo_filter = st.sidebar.selectbox("Filtrar por Tipo de Anúncio", options=tipo_options)

    # --- Aplicação dos Filtros ---
    df_filtrado = df_anuncios_master.copy()

    if sku_filter:
        df_filtrado = df_filtrado[df_filtrado['sku'].str.contains(sku_filter, case=False, na=False)]
    if status_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == status_filter]
    if tipo_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_anuncio'] == tipo_filter]

    # --- Seção de KPIs ---
    st.header("Indicadores Chave")
    
    # Cria 3 colunas para os KPIs
    col1, col2, col3 = st.columns(3)

    # Calcula os valores dos KPIs a partir do dataframe JÁ FILTRADO
    num_anuncios = len(df_filtrado)
    valor_estoque = (df_filtrado['preco_venda'] * df_filtrado['quantidade_estoque']).sum()
    qtd_itens = df_filtrado['quantidade_estoque'].sum()

    # Exibe os KPIs nos cartões
    with col1:
        st.metric(label="Nº de Anúncios Exibidos", value=num_anuncios)
    
    with col2:
        # Formata o valor como moeda brasileira
        st.metric(label="Valor Total em Estoque", value=f"R$ {valor_estoque:,.2f}")

    with col3:
        st.metric(label="Quantidade Total de Itens", value=f"{qtd_itens:,}")


    # --- Exibição da Tabela de Dados ---
    st.write("---") # Adiciona uma linha divisória
    st.header("Visão Geral dos Anúncios")
    st.dataframe(df_filtrado)

else:
    st.warning("Nenhum dado de anúncio foi encontrado na base de dados.")


