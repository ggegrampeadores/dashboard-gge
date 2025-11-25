import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error

# Função para inicializar a conexão com o banco de dados
def init_connection():
    try:
        st.write("DEBUG: Tentando conectar ao banco de dados...")
        conn = mysql.connector.connect(
            host=st.secrets["db_host"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            database=st.secrets["db_name"]
        )
        st.write("DEBUG: Conexão com o banco de dados bem-sucedida!")
        return conn
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        st.write(f"DEBUG: Falha na conexão. Erro: {e}") # Adiciona log de erro na tela
        return None

# Função para buscar os dados dos anúncios
def fetch_data(conn):
    if conn is None:
        st.write("DEBUG: Conexão é nula, não foi possível buscar dados.")
        return pd.DataFrame() # Retorna DataFrame vazio se a conexão falhou
    try:
        st.write("DEBUG: Tentando executar a consulta SQL...")
        query = "SELECT * FROM Anuncios;"
        df = pd.read_sql(query, conn)
        st.write(f"DEBUG: Consulta executada. {len(df)} linhas encontradas.")
        return df
    except Error as e:
        st.error(f"Erro ao buscar dados: {e}")
        st.write(f"DEBUG: Falha na consulta SQL. Erro: {e}") # Adiciona log de erro na tela
        return pd.DataFrame()
    finally:
        if conn.is_connected():
            conn.close()
            st.write("DEBUG: Conexão com o banco de dados fechada.")

# --- Layout do App ---
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Anúncios GGE")

# Conecta e busca os dados
conn = init_connection()
df_anuncios = fetch_data(conn)

# Exibe os dados ou a mensagem de erro
if not df_anuncios.empty:
    st.write("### Visão Geral dos Anúncios")
    st.dataframe(df_anuncios)
else:
    st.warning("Nenhum dado de anúncio foi encontrado ou houve um erro ao carregar.")
    st.info("Verificando os logs de depuração acima para mais detalhes...")

