import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import openpyxl

# ==============================================================================
# CONFIGURAÇÕES DA PÁGINA
# ==============================================================================
st.set_page_config(
    layout="wide",
    page_title="GGE Dashboard",
    page_icon="📊"
)

st.title("📊 Dashboard de Anúncios GGE (v3.2 - Novo Formato ML)")

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def formatar_brl(valor):
    if pd.isna(valor): return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_int_br(numero):
    if pd.isna(numero): return "0"
    return f"{int(numero):,}".replace(",", ".")

@st.cache_data(ttl=3600)
def fetch_data(engine):
    try:
        query = 'SELECT * FROM "Anuncios";'
        df = pd.read_sql(query, engine)
        df['preco_venda'] = pd.to_numeric(df['preco_venda'], errors='coerce').fillna(0)
        df['quantidade_estoque'] = pd.to_numeric(df['quantidade_estoque'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar os dados do banco: {e}")
        return pd.DataFrame()

# ==============================================================================
# CORPO PRINCIPAL DO APP
# ==============================================================================

try:
    db_url = st.secrets["database_url"]
    engine = create_engine(db_url)
except Exception as e:
    st.error(f"Não foi possível conectar ao
