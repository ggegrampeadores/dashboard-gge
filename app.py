import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import openpyxl # Importamos a nova biblioteca

# ==============================================================================
# CONFIGURAÇÕES DA PÁGINA
# ==============================================================================
st.set_page_config(
    layout="wide",
    page_title="GGE Dashboard",
    page_icon="📊"
)

st.title("📊 Dashboard de Anúncios GGE (v3.1 - Uploader)")

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
    st.error(f"Não foi possível conectar ao banco de dados. Verifique os segredos. Erro: {e}")
    st.stop()

# --- SEÇÃO DE UPLOAD NA BARRA LATERAL ---
st.sidebar.header("Carregar Novos Dados")
uploaded_file = st.sidebar.file_uploader(
    "Selecione o arquivo 'Anuncios.xlsx'",
    type=['xlsx']
)

if uploaded_file is not None:
    try:
        st.sidebar.info("Lendo o arquivo... Por favor, aguarde.")
        df_upload = pd.read_excel(uploaded_file)
        
        # Renomeia as colunas para corresponder ao banco de dados
        df_upload.columns = [
            'id_anuncio', 'id_conta', 'sku', 'titulo', 'preco_venda', 'status', 
            'tipo_anuncio', 'custo_envio', 'quantidade_estoque', 'vendas_totais', 
            'data_criacao', 'ultima_atualizacao', 'score_descricao', 
            'score_ficha_tecnica', 'score_fotos', 'status_catalogo', 'flex_status'
        ]

        st.sidebar.info(f"{len(df_upload)} linhas lidas do arquivo.")
        
        if st.sidebar.button("Enviar para o Banco de Dados"):
            with st.spinner("Enviando dados para o Supabase... Isso pode levar um momento."):
                # 'replace' apaga a tabela antiga e insere os novos dados
                df_upload.to_sql('Anuncios', engine, if_exists='replace', index=False)
                st.cache_data.clear() # Limpa o cache para forçar a releitura dos novos dados
            st.sidebar.success("Dados enviados com sucesso! O dashboard será atualizado.")
            st.experimental_rerun() # Força a recarga da página

    except Exception as e:
        st.sidebar.error(f"Ocorreu um erro ao processar o arquivo: {e}")


# --- Carrega os dados do banco ---
df_master = fetch_data(engine)

if df_master.empty:
    st.warning("O banco de dados está vazio. Use o uploader na barra lateral para carregar os dados.")
else:
    # O resto do código do dashboard continua aqui...
    st.sidebar.header("Filtros")
    sku_filter = st.sidebar.text_input("Buscar por SKU")
    
    status_options = ["Todos"] + sorted(df_master['status'].unique().tolist())
    status_filter = st.sidebar.selectbox("Filtrar por Status", options=status_options)

    tipo_options = ["Todos"] + sorted(df_master['tipo_anuncio'].unique().tolist())
    tipo_filter = st.sidebar.selectbox("Filtrar por Tipo de Anúncio", options=tipo_options)

    df_filtrado = df_master.copy()

    if sku_filter:
        df_filtrado = df_filtrado[df_filtrado['sku'].str.contains(sku_filter, case=False, na=False)]
    if status_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == status_filter]
    if tipo_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_anuncio'] == tipo_filter]

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

    st.write("---")
    st.header("Análises Visuais")
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Proporção por Tipo de Anúncio")
        df_tipo = df_filtrado['tipo_anuncio'].value_counts()
        st.bar_chart(df_tipo)

    with col_graf2:
        st.subheader("Top 5 Produtos por Estoque")
        df_top_estoque = df_filtrado.nlargest(5, 'quantidade_estoque')
        st.bar_chart(df_top_estoque, x='sku', y='quantidade_estoque')

    st.write("---") 
    st.header("Visão Geral dos Anúncios")
    st.dataframe(df_filtrado)

