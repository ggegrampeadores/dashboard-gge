import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import locale # Importa a biblioteca de localização

# --- Configurações da Página e Localização ---
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Anúncios GGE (v2.3 - Formatação BR)")

# Define a localidade para Português do Brasil para formatação de moeda e números
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Em alguns ambientes (como o Streamlit Cloud), pode ser necessário um fallback
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


# --- Conexão e Busca de Dados (com cache) ---
@st.cache_data
def fetch_data():
    try:
        db_url = st.secrets["database_url"]
        engine = create_engine(db_url)
        query = 'SELECT * FROM "Anuncios";'
        df = pd.read_sql(query, engine)
        # Garante que as colunas numéricas são do tipo correto
        df['preco_venda'] = pd.to_numeric(df['preco_venda'], errors='coerce')
        df['quantidade_estoque'] = pd.to_numeric(df['quantidade_estoque'], errors='coerce')
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
    
    col1, col2, col3 = st.columns(3)

    num_anuncios = len(df_filtrado)
    valor_estoque = (df_filtrado['preco_venda'] * df_filtrado['quantidade_estoque']).sum()
    qtd_itens = df_filtrado['quantidade_estoque'].sum()

    with col1:
        st.metric(label="Nº de Anúncios Exibidos", value=num_anuncios)
    
    with col2:
        # Usa locale.currency() para fo
