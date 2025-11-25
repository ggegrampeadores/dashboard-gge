import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# --- Configurações da Página ---
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Anúncios GGE (v2.4 - Gráficos)")

# --- Funções Auxiliares ---

# Função para formatar números no padrão brasileiro (substitui a biblioteca locale)
def formatar_brl(valor):
    """Formata um número como moeda brasileira (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_int_br(numero):
    """Formata um número inteiro com separador de milhar brasileiro (1.234)."""
    return f"{int(numero):,}".replace(",", ".")

# --- Conexão e Busca de Dados (com cache) ---
@st.cache_data
def fetch_data():
    try:
        db_url = st.secrets["database_url"]
        engine = create_engine(db_url)
        query = 'SELECT * FROM "Anuncios";'
        df = pd.read_sql(query, engine)
        df['preco_venda'] = pd.to_numeric(df['preco_venda'], errors='coerce').fillna(0)
        df['quantidade_estoque'] = pd.to_numeric(df['quantidade_estoque'], errors='coerce').fillna(0)
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
        st.metric(label="Nº de Anúncios Exibidos", value=formatar_int_br(num_anuncios))
    
    with col2:
        st.metric(label="Valor Total em Estoque", value=formatar_brl(valor_estoque))

    with col3:
        st.metric(label="Quantidade Total de Itens", value=formatar_int_br(qtd_itens))

    # --- Seção de Gráficos ---
    st.write("---")
    st.header("Análises Visuais")

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Proporção por Tipo de Anúncio")
        # Agrupa os dados e conta a ocorrência de cada tipo de anúncio
        df_tipo = df_filtrado['tipo_anuncio'].value_counts().reset_index()
        df_tipo.columns = ['tipo_anuncio', 'contagem']
        
        # Usa o próprio Streamlit para criar o gráfico de pizza
        st.bar_chart(df_tipo, x='tipo_anuncio', y='contagem')
        # st.altair_chart(c, use_container_width=True) # (Alternativa para gráfico de rosca)

    with col_graf2:
        st.subheader("Top 5 Produtos por Estoque")
        # Ordena o dataframe pela quantidade de estoque e pega os 5 maiores
        df_top_estoque = df_filtrado.sort_values('quantidade_estoque', ascending=False).head(5)
        
        # Usa o Streamlit para criar o gráfico de barras
        st.bar_chart(df_top_estoque, x='sku', y='quantidade_estoque')

    # --- Exibição da Tabela de Dados ---
    st.write("---") 
    st.header("Visão Geral dos Anúncios")
    st.dataframe(df_filtrado)

else:
    st.warning("Nenhum dado de anúncio foi encontrado na base de dados.")

