import streamlit as st
import mysql.connector
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard GGE",
    page_icon="📊",
    layout="wide"
)

# --- Conexão com o Banco de Dados (com cache) ---
# O cache garante que não vamos nos reconectar ao banco a cada interação.
@st.cache_resource
def get_db_connection():
    conn = mysql.connector.connect(
        host="195.35.61.58",  # IP do servidor do banco de dados que você encontrou
        user="u196862258_ggemarket",
        password=st.secrets["db_password"], # Usando o sistema de segredos do Streamlit
        database="u196862258_controlemarket"
    )
    return conn

# --- Função para Carregar os Dados ---
@st.cache_data(ttl=600) # Cache dos dados por 10 minutos
def carregar_dados_anuncios():
    try:
        conn = get_db_connection()
        # Usamos o Pandas para ler os dados do SQL diretamente para um DataFrame
        query = "SELECT id_anuncio, titulo, preco_venda, quantidade_estoque, status, vendas_totais FROM Anuncios ORDER BY vendas_totais DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco de dados: {e}")
        return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro

# --- Interface do Dashboard ---
st.title("📊 Dashboard de Anúncios GGE")

df_anuncios = carregar_dados_anuncios()

if not df_anuncios.empty:
    st.write(f"Exibindo dados de **{len(df_anuncios)}** anúncios encontrados no banco de dados.")

    # --- Filtros ---
    st.sidebar.header("Filtros")
    status_selecionado = st.sidebar.multiselect(
        "Filtrar por Status:",
        options=df_anuncios["status"].unique(),
        default=df_anuncios["status"].unique()
    )

    df_filtrado = df_anuncios[df_anuncios["status"].isin(status_selecionado)]

    # --- Exibição dos Dados ---
    st.dataframe(df_filtrado)

else:
    st.warning("Nenhum dado de anúncio foi encontrado ou houve um erro ao carregar.")

