import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(layout="wide", page_title="GGE Dashboard", page_icon="📊")
st.title("📊 Dashboard de Anúncios GGE (v3.5)")

def formatar_brl(valor):
    if pd.isna(valor):
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_int_br(numero):
    if pd.isna(numero):
        return "0"
    return f"{int(numero):,}".replace(",", ".")

def encontrar_coluna(df, opcoes):
    for opcao in opcoes:
        if opcao in df.columns:
            return opcao
    return None

try:
    db_url = st.secrets["database_url"]
    engine = create_engine(db_url)
except Exception as e:
    st.error(f"Erro de conexao: {e}")
    st.stop()

st.sidebar.header("Carregar Novos Dados")
uploaded_file = st.sidebar.file_uploader("Selecione arquivo do Mercado Livre", type=['xlsx'])

if uploaded_file is not None:
    try:
        st.sidebar.info("Lendo arquivo...")
        df_upload = pd.read_excel(uploaded_file, sheet_name='Anúncios', skiprows=3)
        df_upload = df_upload.dropna(how='all')
        
        col_item_id = encontrar_coluna(df_upload, ['ITEM_ID', 'Item ID', 'item_id', 'ID'])
        if col_item_id is None:
            st.sidebar.error("Nao foi encontrada coluna ITEM_ID no arquivo")
            st.stop()
        
        df_upload = df_upload[df_upload[col_item_id].notna()]
        
        num_linhas = len(df_upload)
        st.sidebar.info(f"{num_linhas} linhas lidas")
        
        if st.sidebar.button("Enviar para o Banco de Dados"):
            with st.spinner("Enviando dados..."):
                df_processado = pd.DataFrame()
                
                col_product = encontrar_coluna(df_upload, ['PRODUCT_NUMBER', 'Product Number', 'product_number', 'SKU'])
                col_title = encontrar_coluna(df_upload, ['TITLE', 'Title', 'title', 'TITULO'])
                col_price = encontrar_coluna(df_upload, ['PRICE', 'Price', 'price', 'PRECO'])
                col_status = encontrar_coluna(df_upload, ['STATUS', 'Status', 'status'])
                col_listing = encontrar_coluna(df_upload, ['LISTING_TYPE', 'Listing Type', 'listing_type', 'TIPO'])
                col_fee = encontrar_coluna(df_upload, ['FEE_PER_SALE', 'Fee Per Sale', 'fee_per_sale'])
                col_quantity = encontrar_coluna(df_upload, ['QUANTITY', 'Quantity', 'quantity', 'ESTOQUE'])
                
                df_processado['id_anuncio'] = df_upload[col_item_id]
                df_processado['id_conta'] = 312056139
                df_processado['sku'] = df_upload[col_product] if col_product else ""
                df_processado['titulo'] = df_upload[col_title] if col_title else ""
                df_processado['preco_venda'] = df_upload[col_price] if col_price else 0
                df_processado['status'] = df_upload[col_status].str.lower() if col_status else "active"
                df_processado['tipo_anuncio'] = df_upload[col_listing].str.lower() if col_listing else "classic"
                df_processado['custo_envio'] = df_upload[col_fee] if col_fee else 0
                df_processado['quantidade_estoque'] = df_upload[col_quantity] if col_quantity else 0
                df_processado['vendas_totais'] = 0
                df_processado['data_criacao'] = pd.Timestamp.now()
                df_processado['ultima_atualizacao'] = pd.Timestamp.now()
                df_processado['score_descricao'] = 0
                df_processado['score_ficha_tecnica'] = 0
                df_processado['score_fotos'] = 0
                df_processado['status_catalogo'] = 'Nao Aplicavel'
                df_processado['flex_status'] = 'Nao Elegivel'
                
                df_processado.to_sql('Anuncios', engine, if_exists='replace', index=False)
            
            st.sidebar.success("Sucesso! Dados enviados.")
            st.rerun()

    except Exception as e:
        st.sidebar.error(f"Erro: {e}")

try:
    query = 'SELECT * FROM "Anuncios";'
    df_master = pd.read_sql(query, engine)
    df_master['preco_venda'] = pd.to_numeric(df_master['preco_venda'], errors='coerce').fillna(0)
    df_master['quantidade_estoque'] = pd.to_numeric(df_master['quantidade_estoque'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")
    df_master = pd.DataFrame()

if df_master.empty:
    st.warning("Banco vazio. Use o uploader para carregar dados.")
else:
    st.sidebar.header("Filtros")
    sku_filter = st.sidebar.text_input("Buscar por SKU")
    
    status_list = sorted(df_master['status'].dropna().unique().tolist())
    status_options = ["Todos"] + status_list
    status_filter = st.sidebar.selectbox("Filtrar por Status", options=status_options)

    tipo_list = sorted(df_master['tipo_anuncio'].dropna().unique().tolist())
    tipo_options = ["Todos"] + tipo_list
    tipo_filter = st.sidebar.selectbox("Filtrar por Tipo", options=tipo_options)

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
        st.metric(label="Anuncios Exibidos", value=formatar_int_br(num_anuncios))
    
    with col2:
        st.metric(label="Valor Total Estoque", value=formatar_brl(valor_estoque))

    with col3:
        st.metric(label="Quantidade Total", value=formatar_int_br(qtd_itens))

    st.write("---")
    st.header("Analises Visuais")
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Tipo de Anuncio")
        df_tipo = df_filtrado['tipo_anuncio'].value_counts()
        st.bar_chart(df_tipo)

    with col_graf2:
        st.subheader("Top 5 por Estoque")
        df_top_estoque = df_filtrado.nlargest(5, 'quantidade_estoque')
        st.bar_chart(df_top_estoque, x='sku', y='quantidade_estoque')

    st.write("---") 
    st.header("Visao Geral dos Anuncios")
    st.dataframe(df_filtrado)
