import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(layout="wide")
st.title("📊 Dashboard de Anúncios GGE (v2.0 - Supabase)")

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

df_anuncios = fetch_data()

if not df_anuncios.empty:
    st.success(f"{len(df_anuncios)} anúncio(s) carregado(s) com sucesso do Supabase!")
    st.write("### Visão Geral dos Anúncios")
    st.dataframe(df_anuncios)
else:
    st.warning("Nenhum dado de anúncio foi encontrado na base de dados.")

