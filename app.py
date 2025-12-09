import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# Configuração da página
st.set_page_config(layout="wide", page_title="GGE Dashboard", page_icon="📊")

# Título principal
st.title("📊 Dashboard de Anúncios GGE (v3.6)")
st.markdown("---")

# ============================================================================
# FUNÇÕES DE FORMATAÇÃO
# ============================================================================

def formatar_brl(valor):
    """Formata valor para Real Brasileiro"""
    if pd.isna(valor):
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_int_br(numero):
    """Formata número inteiro com separador brasileiro"""
    if pd.isna(numero):
        return "0"
    return f"{int(numero):,}".replace(",", ".")


# ============================================================================
# CONEXÃO COM BANCO DE DADOS
# ============================================================================

def conectar_banco():
    """Estabelece conexão com o banco de dados"""
    try:
        # Tenta usar secrets do Streamlit
        db_url = st.secrets.get("database_url")
        if not db_url:
            # Fallback para variáveis de ambiente
            db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            st.warning("⚠️ Banco de dados não configurado. Use o uploader para carregar dados.")
            return None
        
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        st.warning(f"⚠️ Erro ao conectar ao banco: {e}")
        return None


engine = conectar_banco()

# ============================================================================
# SEÇÃO DE UPLOAD DE DADOS
# ============================================================================

st.sidebar.header("📤 Carregar Novos Dados")
st.sidebar.markdown("Selecione um arquivo para atualizar o banco de dados")

uploaded_file = st.sidebar.file_uploader(
    "Selecione arquivo do Mercado Livre (Excel)",
    type=['xlsx'],
    help="Arquivo Excel com dados de anúncios do Mercado Livre"
)

if uploaded_file is not None:
    try:
        st.sidebar.info("📖 Lendo arquivo...")
        df_upload = pd.read_excel(uploaded_file, sheet_name='Anúncios')
        df_upload = df_upload.dropna(how='all')
        df_upload = df_upload[df_upload['ITEM_ID'].notna()]
        
        num_linhas = len(df_upload)
        st.sidebar.info(f"✅ {num_linhas} linhas lidas com sucesso")
        
        if st.sidebar.button("🔄 Enviar para o Banco de Dados", use_container_width=True):
            if engine is None:
                st.sidebar.error("❌ Banco de dados não disponível")
            else:
                with st.spinner("⏳ Enviando dados..."):
                    try:
                        df_processado = pd.DataFrame()
                        df_processado['id_anuncio'] = df_upload['ITEM_ID']
                        df_processado['id_conta'] = 312056139
                        df_processado['sku'] = df_upload['PRODUCT_NUMBER']
                        df_processado['titulo'] = df_upload['TITLE']
                        df_processado['preco_venda'] = df_upload['PRICE']
                        df_processado['status'] = df_upload['STATUS'].str.lower()
                        df_processado['tipo_anuncio'] = df_upload['LISTING_TYPE'].str.lower()
                        df_processado['custo_envio'] = df_upload['FEE_PER_SALE']
                        df_processado['quantidade_estoque'] = df_upload['QUANTITY']
                        df_processado['vendas_totais'] = 0
                        df_processado['data_criacao'] = pd.Timestamp.now()
                        df_processado['ultima_atualizacao'] = pd.Timestamp.now()
                        df_processado['score_descricao'] = 0
                        df_processado['score_ficha_tecnica'] = 0
                        df_processado['score_fotos'] = 0
                        df_processado['status_catalogo'] = 'Nao Aplicavel'
                        df_processado['flex_status'] = 'Nao Elegivel'
                        
                        df_processado.to_sql('Anuncios', engine, if_exists='replace', index=False)
                        st.sidebar.success("✅ Sucesso! Dados enviados ao banco.")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"❌ Erro ao enviar dados: {e}")

    except Exception as e:
        st.sidebar.error(f"❌ Erro ao processar arquivo: {e}")

# ============================================================================
# CARREGAMENTO DE DADOS DO BANCO
# ============================================================================

df_master = pd.DataFrame()

if engine is not None:
    try:
        query = 'SELECT * FROM "Anuncios";'
        df_master = pd.read_sql(query, engine)
        df_master['preco_venda'] = pd.to_numeric(df_master['preco_venda'], errors='coerce').fillna(0)
        df_master['quantidade_estoque'] = pd.to_numeric(df_master['quantidade_estoque'], errors='coerce').fillna(0)
    except Exception as e:
        st.warning(f"⚠️ Erro ao buscar dados: {e}")

# ============================================================================
# CONTEÚDO PRINCIPAL
# ============================================================================

if df_master.empty:
    st.info(
        "📌 **Banco de dados vazio**\n\n"
        "Use o painel lateral para carregar dados de um arquivo Excel do Mercado Livre."
    )
else:
    # Filtros na barra lateral
    st.sidebar.header("🔍 Filtros")
    
    sku_filter = st.sidebar.text_input(
        "Buscar por SKU",
        placeholder="Digite o SKU do produto",
        help="Busca parcial (case-insensitive)"
    )
    
    status_list = sorted(df_master['status'].dropna().unique().tolist())
    status_options = ["Todos"] + status_list
    status_filter = st.sidebar.selectbox(
        "Filtrar por Status",
        options=status_options,
        help="Selecione um status para filtrar"
    )

    tipo_list = sorted(df_master['tipo_anuncio'].dropna().unique().tolist())
    tipo_options = ["Todos"] + tipo_list
    tipo_filter = st.sidebar.selectbox(
        "Filtrar por Tipo",
        options=tipo_options,
        help="Selecione um tipo de anúncio"
    )

    # Aplicar filtros
    df_filtrado = df_master.copy()

    if sku_filter:
        df_filtrado = df_filtrado[df_filtrado['sku'].str.contains(sku_filter, case=False, na=False)]
    
    if status_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == status_filter]
    
    if tipo_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_anuncio'] == tipo_filter]

    # ========================================================================
    # INDICADORES CHAVE
    # ========================================================================
    
    st.header("📊 Indicadores Chave")
    
    num_anuncios = len(df_filtrado)
    valor_estoque = (df_filtrado['preco_venda'] * df_filtrado['quantidade_estoque']).sum()
    qtd_itens = df_filtrado['quantidade_estoque'].sum()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Anúncios Exibidos",
            value=formatar_int_br(num_anuncios),
            help="Total de anúncios após filtros"
        )
    
    with col2:
        st.metric(
            label="Valor Total Estoque",
            value=formatar_brl(valor_estoque),
            help="Preço × Quantidade em estoque"
        )

    with col3:
        st.metric(
            label="Quantidade Total",
            value=formatar_int_br(qtd_itens),
            help="Total de itens em estoque"
        )

    st.markdown("---")

    # ========================================================================
    # ANÁLISES VISUAIS
    # ========================================================================
    
    st.header("📈 Análises Visuais")
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Distribuição por Tipo de Anúncio")
        df_tipo = df_filtrado['tipo_anuncio'].value_counts()
        if not df_tipo.empty:
            st.bar_chart(df_tipo)
        else:
            st.info("Sem dados para este gráfico")

    with col_graf2:
        st.subheader("Top 5 Produtos por Estoque")
        df_top_estoque = df_filtrado.nlargest(5, 'quantidade_estoque')
        if not df_top_estoque.empty:
            st.bar_chart(df_top_estoque.set_index('sku')['quantidade_estoque'])
        else:
            st.info("Sem dados para este gráfico")

    st.markdown("---")

    # ========================================================================
    # TABELA DE ANÚNCIOS
    # ========================================================================
    
    st.header("📋 Visão Geral dos Anúncios")
    
    # Selecionar colunas para exibição
    colunas_exibicao = ['id_anuncio', 'sku', 'titulo', 'preco_venda', 
                        'status', 'tipo_anuncio', 'quantidade_estoque']
    
    df_exibicao = df_filtrado[colunas_exibicao].copy()
    df_exibicao.columns = ['MLB', 'SKU', 'Título', 'Preço (R$)', 
                           'Status', 'Tipo', 'Estoque']
    
    # Formatação de valores
    df_exibicao['Preço (R$)'] = df_exibicao['Preço (R$)'].apply(formatar_brl)
    df_exibicao['Estoque'] = df_exibicao['Estoque'].apply(formatar_int_br)
    
    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Informações de rodapé
    st.markdown("---")
    st.caption(
        f"📊 Total de anúncios exibidos: {formatar_int_br(num_anuncios)} | "
        f"Valor total: {formatar_brl(valor_estoque)}"
    )
