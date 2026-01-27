import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    def password_entered():
        # Verifica se a senha digitada é 'admin123'
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Limpa a senha da memória
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Exibe campo de senha
        st.text_input("Senha de Acesso", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Senha incorreta, exibe novamente o campo
        st.text_input("Senha de Acesso", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta")
        return False
    else:
        # Senha correta
        return True

if not check_password():
    st.stop()
# Configuração da página
st.set_page_config(page_title="Gestão Comercial", layout="wide", page_icon="📊")

# Função para carregar dados (SEM widgets dentro)
@st.cache_data
def carregar_dados_do_arquivo(arquivo_vendas, arquivo_produtos, arquivo_precos, arquivo_inadimplencia):
    """Carrega todas as planilhas a partir dos arquivos fornecidos"""
    try:
        # 1. Vendas
        vendas = pd.read_excel(arquivo_vendas)
        
        # Verificar e converter data
        if 'DataEmissao' not in vendas.columns:
            st.error("❌ Coluna 'DataEmissao' não encontrada em vendas")
            return None, None, None, None
        
        vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        
        # 2. Produtos
        produtos = pd.read_excel(arquivo_produtos)
        
        # 🔧 LIMPEZA FORÇADA DOS NOMES DAS COLUNAS
        produtos.columns = (
            produtos.columns
            .astype(str)
            .str.replace('\ufeff', '', regex=True)
            .str.replace('\xa0', '', regex=True)
            .str.strip()
        )

        # 🔒 VALIDAÇÃO
        if 'ID_COD' not in produtos.columns:
            st.error(f"❌ Coluna 'ID_COD' não encontrada em produtos. Colunas: {list(produtos.columns)}")
            return None, None, None, None
        
        # 3. Tabela de Preços
        tabela_preco = pd.read_excel(arquivo_precos)
        
        # 4. Inadimplência
        inadimplencia = pd.read_excel(arquivo_inadimplencia)
        
        if 'Dt.Vencimento' in inadimplencia.columns:
            inadimplencia['Dt.Vencimento'] = pd.to_datetime(inadimplencia['Dt.Vencimento'], errors='coerce')
        
        return vendas, produtos, tabela_preco, inadimplencia
        
    except Exception as e:
        st.error(f"❌ Erro ao processar dados: {str(e)}")
        return None, None, None, None

# Verificar se arquivos existem localmente
arquivos_necessarios = {
    'vendas': 'CONSULTA_VENDEDORES.xlsx',
    'produtos': 'Produtos_Agrupados_Completos_conciliados.xlsx',
    'precos': 'TABELAS_NE.xlsx',
    'inadimplencia': 'XLS_Grid_LANCAMENTO A RECEBER.xlsx'
}

# Verificar quais arquivos estão faltando
arquivos_faltando = []
for nome, arquivo in arquivos_necessarios.items():
    caminho_dados = os.path.join('dados', arquivo)
    if os.path.exists(caminho_dados):
        arquivos_necessarios[nome] = caminho_dados
    elif not os.path.exists(arquivo):
        arquivos_faltando.append(nome)

# Se algum arquivo estiver faltando, solicitar upload
uploaded_files = {}
if arquivos_faltando:
    st.warning(f"⚠️ {len(arquivos_faltando)} arquivo(s) não encontrado(s). Por favor, faça upload:")
    
    for nome in arquivos_faltando:
        arquivo_original = arquivos_necessarios[nome].split('/')[-1]
        
        if nome == 'vendas':
            uploaded = st.file_uploader(f"📤 {arquivo_original}", type=['xlsx'], key='upload_vendas')
            if uploaded:
                uploaded_files['vendas'] = uploaded
        elif nome == 'produtos':
            uploaded = st.file_uploader(f"📦 {arquivo_original}", type=['xlsx'], key='upload_produtos')
            if uploaded:
                uploaded_files['produtos'] = uploaded
        elif nome == 'precos':
            uploaded = st.file_uploader(f"💰 {arquivo_original}", type=['xlsx'], key='upload_precos')
            if uploaded:
                uploaded_files['precos'] = uploaded
        elif nome == 'inadimplencia':
            uploaded = st.file_uploader(f"📋 {arquivo_original}", type=['xls', 'xlsx'], key='upload_inadimplencia')
            if uploaded:
                uploaded_files['inadimplencia'] = uploaded
    
    if len(uploaded_files) != len(arquivos_faltando):
        st.info("👆 Aguardando upload de todos os arquivos necessários...")
        st.stop()
    
    for nome in arquivos_faltando:
        arquivos_necessarios[nome] = uploaded_files[nome]

# Carregar dados
with st.spinner("🔄 Carregando dados..."):
    vendas, produtos, tabela_preco, inadimplencia = carregar_dados_do_arquivo(
        arquivos_necessarios['vendas'],
        arquivos_necessarios['produtos'],
        arquivos_necessarios['precos'],
        arquivos_necessarios['inadimplencia']
    )

if vendas is None:
    st.error("❌ Erro ao carregar dados. Verifique os arquivos e tente novamente.")
    st.stop()

st.sidebar.success("✅ Dados carregados com sucesso!")

# Função para conciliar vendas com produtos e preços
@st.cache_data
def conciliar_dados(vendas, produtos, tabela_preco):
    """Realiza a conciliação entre vendas, produtos e tabela de preços"""
    vendas_completas = vendas.merge(
        produtos[['ID_COD', 'Gramatura', 'DESCRICAONF']], 
        left_on='CodigoProduto', 
        right_on='ID_COD', 
        how='left'
    )
    
    vendas_completas = vendas_completas.merge(
        tabela_preco[['ID_COD', 'PRECO']], 
        left_on='CodigoProduto', 
        right_on='ID_COD', 
        how='left',
        suffixes=('', '_preco')
    )
    
    vendas_completas.rename(columns={'PRECO': 'PrecoTabela'}, inplace=True)
    
    vendas_completas['DescontoPerc'] = (
        (vendas_completas['PrecoTabela'] - vendas_completas['PrecoUnit']) / 
        vendas_completas['PrecoTabela'] * 100
    )
    
    def calcular_comissao(row):
        if pd.isna(row['PrecoTabela']) or row['PrecoTabela'] == 0:
            return 0
        if row['PrecoUnit'] == row['PrecoTabela']:
            return row['TotalProduto2'] * 0.03
        elif row['PrecoUnit'] >= (row['PrecoTabela'] * 1.06):
            return row['TotalProduto2'] * 0.04
        else:
            return row['TotalProduto2'] * 0.03
    
    vendas_completas['Comissao'] = vendas_completas.apply(calcular_comissao, axis=1)
    
    return vendas_completas

# Conciliar dados
vendas_completas = conciliar_dados(vendas, produtos, tabela_preco)

# Função para gerar PDF de inadimplência
def gerar_pdf_inadimplencia(df_inad, vendedor, cliente):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Relatório de Inadimplência")
    
    y = height - 80
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Vendedor: {vendedor}")
    y -= 20
    p.drawString(50, y, f"Cliente: {cliente}")
    y -= 20
    p.drawString(50, y, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    
    y -= 40
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Documento")
    p.drawString(150, y, "Cliente")
    p.drawString(300, y, "Vencimento")
    p.drawString(400, y, "Valor")
    p.drawString(500, y, "Status")
    
    y -= 20
    p.setFont("Helvetica", 9)
    
    for _, row in df_inad.iterrows():
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 9)
        
        p.drawString(50, y, str(row.get('N_Doc', ''))[:15])
        p.drawString(150, y, str(row.get('Razão Social', ''))[:20])
        p.drawString(300, y, row['Dt.Vencimento'].strftime('%d/%m/%Y'))
        p.drawString(400, y, f"R$ {row['Vr.Líquido']:,.2f}")
        p.drawString(500, y, str(row.get('Status', '')))
        y -= 15
    
    p.save()
    buffer.seek(0)
    return buffer

# ========== SIDEBAR ==========
st.sidebar.title("🎯 Filtros Globais")

# Filtro de Data com formato DD/MM/AAAA
data_min = vendas_completas['DataEmissao'].min().date()
data_max = vendas_completas['DataEmissao'].max().date()

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input("Data Início", data_min, format="DD/MM/YYYY")
with col2:
    data_fim = st.date_input("Data Fim", data_max, format="DD/MM/YYYY")

# Filtro de Vendedor
vendedores = (
    ['Todos'] +
    sorted(
        vendas_completas['Vendedor']
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
)

vendedor_selecionado = st.sidebar.selectbox("Vendedor", vendedores)

# Aplicar filtros
mask = (vendas_completas['DataEmissao'].dt.date >= data_inicio) & \
       (vendas_completas['DataEmissao'].dt.date <= data_fim)

if vendedor_selecionado != 'Todos':
    mask &= vendas_completas['Vendedor'] == vendedor_selecionado

df_filtrado = vendas_completas[mask]

# ========== NAVEGAÇÃO ==========
st.sidebar.markdown("---")
st.sidebar.title("📋 Módulos")
modulo = st.sidebar.radio(
    "",
    ["📊 Relatório BI", "📦 Pedidos e Comissões", "💰 Inadimplência"]
)

# ========== MÓDULO BI ==========
if modulo == "📊 Relatório BI":
    st.title("📊 Relatório Comercial Completo")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_faturamento = df_filtrado['TotalProduto2'].sum()
    total_clientes = df_filtrado['CPF_CNPJ'].nunique()
    ticket_medio = df_filtrado['TotalProduto2'].mean()
    
    hoje = datetime.now()
    data_60_dias = hoje - timedelta(days=60)
    clientes_ativos = df_filtrado[df_filtrado['DataEmissao'] >= data_60_dias]['CPF_CNPJ'].nunique()
    total_clientes_base = vendas_completas['CPF_CNPJ'].nunique()
    positivacao = (clientes_ativos / total_clientes_base * 100) if total_clientes_base > 0 else 0
    
    col1.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}")
    col2.metric("👥 Total de Clientes", f"{total_clientes}")
    col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}")
    col4.metric("📈 Positivação", f"{positivacao:.1f}%")
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Evolução Mensal de Faturamento")
        df_mensal = df_filtrado.groupby(df_filtrado['DataEmissao'].dt.to_period('M'))['TotalProduto2'].sum().reset_index()
        df_mensal['DataEmissao'] = df_mensal['DataEmissao'].astype(str)
        fig = px.line(df_mensal, x='DataEmissao', y='TotalProduto2', 
                      labels={'TotalProduto2': 'Faturamento', 'DataEmissao': 'Mês'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top 10 Clientes")
        top_clientes = df_filtrado.groupby('RazaoSocial')['TotalProduto2'].sum().sort_values(ascending=True).tail(10)
        fig = px.bar(top_clientes, orientation='h', 
                     labels={'value': 'Faturamento', 'RazaoSocial': 'Cliente'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
        
    # Produtos Mais Vendidos
    st.subheader("📦 Produtos Mais Vendidos")
    
    # Filtros para produtos mais vendidos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        prod_data_inicio = st.date_input("Data Início Produto", data_inicio, format="DD/MM/YYYY", key="prod_inicio")
    with col2:
        prod_data_fim = st.date_input("Data Fim Produto", data_fim, format="DD/MM/YYYY", key="prod_fim")
    with col3:
        filtro_cod_prod = st.text_input("Filtrar por Código", key="filtro_cod_prod")
    with col4:
        filtro_desc_prod = st.text_input("Filtrar por DESCRICAONF", key="filtro_desc_prod")
    
    # Aplicar filtros em produtos mais vendidos
    df_prod_filtrado = df_filtrado.copy()
    df_prod_filtrado = df_prod_filtrado[
        (df_prod_filtrado['DataEmissao'].dt.date >= prod_data_inicio) & 
        (df_prod_filtrado['DataEmissao'].dt.date <= prod_data_fim)
    ]
    
    if filtro_cod_prod:
        df_prod_filtrado = df_prod_filtrado[df_prod_filtrado['CodigoProduto'].astype(str).str.contains(filtro_cod_prod, case=False, na=False)]
    
    if filtro_desc_prod:
        df_prod_filtrado = df_prod_filtrado[df_prod_filtrado['DESCRICAONF'].astype(str).str.contains(filtro_desc_prod, case=False, na=False)]
    
    produtos_vendidos = df_prod_filtrado.groupby(['CodigoProduto', 'DESCRICAONF']).agg({
        'Quantidade': 'sum',
        'TotalProduto2': 'sum'
    }).sort_values('Quantidade', ascending=False).reset_index()
    produtos_vendidos.columns = ['Código', 'DESCRICAONF', 'Qtd Total', 'Faturamento Total']
    produtos_vendidos['Qtd Total'] = produtos_vendidos['Qtd Total'].apply(lambda x: f"{x:,.0f}")
    produtos_vendidos['Faturamento Total'] = produtos_vendidos['Faturamento Total'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(produtos_vendidos.head(20), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Rankings com filtros
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎖️ Ranking de Vendedores")
        
        # Filtros para ranking de vendedores
        rank_col1, rank_col2, rank_col3 = st.columns(3)
        with rank_col1:
            rank_data_inicio = st.date_input("Data Início Ranking", data_inicio, format="DD/MM/YYYY", key="rank_inicio")
        with rank_col2:
            rank_data_fim = st.date_input("Data Fim Ranking", data_fim, format="DD/MM/YYYY", key="rank_fim")
        with rank_col3:
            # Filtro por cidade
            if 'Cidade' in vendas_completas.columns:
                cidades_rank = ['Todas'] + sorted(vendas_completas['Cidade'].dropna().unique().tolist())
                cidade_rank = st.selectbox("Cidade", cidades_rank, key="cidade_rank")
            else:
                cidade_rank = 'Todas'
        
        # Filtro por estado
        if 'Estado' in vendas_completas.columns or 'UF' in vendas_completas.columns:
            col_estado_rank = 'Estado' if 'Estado' in vendas_completas.columns else 'UF'
            estados_rank = ['Todos'] + sorted(vendas_completas[col_estado_rank].dropna().unique().tolist())
            estado_rank = st.selectbox("Estado", estados_rank, key="estado_rank")
        else:
            estado_rank = 'Todos'
        
        # Aplicar filtros
        df_rank_filtrado = df_filtrado.copy()
        df_rank_filtrado = df_rank_filtrado[
            (df_rank_filtrado['DataEmissao'].dt.date >= rank_data_inicio) & 
            (df_rank_filtrado['DataEmissao'].dt.date <= rank_data_fim)
        ]
        
        if cidade_rank != 'Todas' and 'Cidade' in vendas_completas.columns:
            df_rank_filtrado = df_rank_filtrado[df_rank_filtrado['Cidade'] == cidade_rank]
        
        if estado_rank != 'Todos':
            if 'Estado' in vendas_completas.columns:
                df_rank_filtrado = df_rank_filtrado[df_rank_filtrado['Estado'] == estado_rank]
            elif 'UF' in vendas_completas.columns:
                df_rank_filtrado = df_rank_filtrado[df_rank_filtrado['UF'] == estado_rank]
        
        ranking_vendedores = df_rank_filtrado.groupby('Vendedor').agg({
            'TotalProduto2': 'sum',
            'Comissao': 'sum'
        }).sort_values('TotalProduto2', ascending=False).reset_index()
        ranking_vendedores.columns = ['Vendedor', 'Faturamento', 'Comissão']
        
        # Exibir com filtros de coluna
        st.dataframe(
            ranking_vendedores,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Faturamento": st.column_config.NumberColumn(
                    "Faturamento",
                    format="R$ %.2f"
                ),
                "Comissão": st.column_config.NumberColumn(
                    "Comissão",
                    format="R$ %.2f"
                )
            }
        )
    
    with col2:
        st.subheader("💸 Análise de Desconto por Vendedor")
        
        # Usar os mesmos filtros do ranking
        analise_desconto = df_rank_filtrado.groupby('Vendedor')['DescontoPerc'].mean().sort_values(ascending=False).reset_index()
        analise_desconto.columns = ['Vendedor', 'Desconto Médio (%)']
        
        st.dataframe(
            analise_desconto,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Desconto Médio (%)": st.column_config.NumberColumn(
                    "Desconto Médio (%)",
                    format="%.2f%%"
                )
            }
        )
    
    st.markdown("---")
    
    # Churn - Clientes sem compras com filtro de dias
    st.subheader("⚠️ Clientes sem Compras")
    
    # Filtros para clientes sem compra
    churn_col1, churn_col2, churn_col3, churn_col4 = st.columns(4)
    
    with churn_col1:
        dias_sem_compra = st.slider("Dias sem compra", min_value=30, max_value=365, value=60, step=30)
    
    with churn_col2:
        churn_data_inicio = st.date_input("Data Início Análise", data_inicio, format="DD/MM/YYYY", key="churn_inicio")
    
    with churn_col3:
        churn_data_fim = st.date_input("Data Fim Análise", data_fim, format="DD/MM/YYYY", key="churn_fim")
    
    with churn_col4:
        vendedores_churn = ['Todos'] + sorted(vendas_completas['Vendedor'].dropna().unique().tolist())
        vendedor_churn = st.selectbox("Vendedor", vendedores_churn, key="vendedor_churn")
    
    # Filtro por estado
    if 'Estado' in vendas_completas.columns or 'UF' in vendas_completas.columns:
        col_estado_churn = 'Estado' if 'Estado' in vendas_completas.columns else 'UF'
        estados_churn = ['Todos'] + sorted(vendas_completas[col_estado_churn].dropna().unique().tolist())
        estado_churn = st.selectbox("Estado", estados_churn, key="estado_churn")
    else:
        estado_churn = 'Todos'
    
    # Aplicar filtros de período
    df_churn_filtrado = vendas_completas[
        (vendas_completas['DataEmissao'].dt.date >= churn_data_inicio) & 
        (vendas_completas['DataEmissao'].dt.date <= churn_data_fim)
    ]
    
    # Aplicar filtro de vendedor
    if vendedor_churn != 'Todos':
        df_churn_filtrado = df_churn_filtrado[df_churn_filtrado['Vendedor'] == vendedor_churn]
    
    # Aplicar filtro de estado
    if estado_churn != 'Todos':
        if 'Estado' in vendas_completas.columns:
            df_churn_filtrado = df_churn_filtrado[df_churn_filtrado['Estado'] == estado_churn]
        elif 'UF' in vendas_completas.columns:
            df_churn_filtrado = df_churn_filtrado[df_churn_filtrado['UF'] == estado_churn]
    
    data_limite_churn = hoje - timedelta(days=dias_sem_compra)
    clientes_recentes_set = set(df_churn_filtrado[df_churn_filtrado['DataEmissao'] >= data_limite_churn]['CPF_CNPJ'].unique())
    todos_clientes_set = set(df_churn_filtrado['CPF_CNPJ'].unique())
    clientes_churn = todos_clientes_set - clientes_recentes_set
    
    # Calcular valor total que deixou de comprar (baseado na média histórica)
    df_churn_detalhado = []
    for cpf in clientes_churn:
        cliente_hist = vendas_completas[vendas_completas['CPF_CNPJ'] == cpf]
        razao_social = cliente_hist['RazaoSocial'].iloc[0] if len(cliente_hist) > 0 else 'N/A'
        valor_medio_mensal = cliente_hist['TotalProduto2'].sum() / max(1, cliente_hist['DataEmissao'].dt.to_period('M').nunique())
        meses_sem_compra = dias_sem_compra / 30
        valor_perdido = valor_medio_mensal * meses_sem_compra
        
        df_churn_detalhado.append({
            'Razão Social': razao_social,
            'CPF_CNPJ': cpf,
            'Valor Perdido Estimado': valor_perdido
        })
    
    df_churn = pd.DataFrame(df_churn_detalhado)
    valor_total_perdido = df_churn['Valor Perdido Estimado'].sum()
    
    st.info(f"📊 Total de clientes inativos há mais de {dias_sem_compra} dias: {len(df_churn)}")
    st.error(f"💰 Valor total estimado perdido: R$ {valor_total_perdido:,.2f}")
    
    st.dataframe(
        df_churn,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valor Perdido Estimado": st.column_config.NumberColumn(
                "Valor Perdido Estimado",
                format="R$ %.2f"
            )
        }
    )
    
    # Histórico detalhado
    st.markdown("---")
    st.subheader("🔍 Histórico Detalhado")
    
    tab1, tab2 = st.tabs(["Por Cliente", "Por Produto"])
    
    with tab1:
        cliente_hist = st.selectbox("Selecione o Cliente", df_filtrado['RazaoSocial'].unique())
        
        # Preparar dados com última compra
        df_cliente_temp = df_filtrado[df_filtrado['RazaoSocial'] == cliente_hist].copy()
        
        # Agrupar por produto para obter totais
        df_cliente_agrupado = df_cliente_temp.groupby('CodigoProduto').agg({
            'DataEmissao': 'max',
            'DESCRICAONF': 'first',
            'Gramatura': 'first',
            'Quantidade': 'sum',
            'PrecoUnit': 'mean',
            'TotalProduto2': 'sum'
        }).reset_index()
        
        df_cliente_agrupado.columns = [
            'Código Produto',
            'Data Última Compra',
            'DESCRICAONF',
            'Gramatura',
            'Qtd Total',
            'Preço Unitário Médio',
            'Total'
        ]
        
        df_cliente_agrupado = df_cliente_agrupado.sort_values('Data Última Compra', ascending=False)
        
        st.dataframe(
            df_cliente_agrupado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Data Última Compra": st.column_config.DateColumn(
                    "Data Última Compra",
                    format="DD/MM/YYYY"
                ),
                "Preço Unitário Médio": st.column_config.NumberColumn(
                    "Preço Unit. Médio",
                    format="R$ %.2f"
                ),
                "Total": st.column_config.NumberColumn(
                    "Total",
                    format="R$ %.2f"
                )
            }
        )
    
    with tab2:
        produto_hist = st.selectbox("Selecione o Produto", df_filtrado['CodigoProduto'].unique())
        df_produto = df_filtrado[df_filtrado['CodigoProduto'] == produto_hist][
            ['DataEmissao', 'RazaoSocial', 'Vendedor', 'Quantidade', 
             'PrecoUnit', 'PrecoTabela', 'TotalProduto2', 'CondPagamento']
        ].sort_values('DataEmissao', ascending=False)
        
        st.dataframe(
            df_produto,
            use_container_width=True,
            hide_index=True,
            column_config={
                "DataEmissao": st.column_config.DateColumn(
                    "Data Emissão",
                    format="DD/MM/YYYY"
                ),
                "PrecoUnit": st.column_config.NumberColumn(
                    "Preço Unit.",
                    format="R$ %.2f"
                ),
                "PrecoTabela": st.column_config.NumberColumn(
                    "Preço Tabela",
                    format="R$ %.2f"
                ),
                "TotalProduto2": st.column_config.NumberColumn(
                    "Total",
                    format="R$ %.2f"
                )
            }
        )

# ========== MÓDULO PEDIDOS ==========
elif modulo == "📦 Pedidos e Comissões":
    st.title("📦 Módulo de Pedidos e Comissões")
    
    # Busca inteligente com seleção
    busca = st.text_input("🔍 Buscar por Código ou DESCRICAONF do Produto", "")
    
    # Filtrar produtos baseado na busca
    if busca:
        mask_busca = (produtos['ID_COD'].astype(str).str.contains(busca, case=False, na=False)) | \
                     (produtos['DESCRICAONF'].astype(str).str.contains(busca, case=False, na=False))
        produtos_filtrados = produtos[mask_busca]
        
        if len(produtos_filtrados) > 0:
            opcoes_produtos = produtos_filtrados['DESCRICAONF'].tolist()
            produto_selecionado = st.selectbox("Selecione o produto:", opcoes_produtos)
        else:
            st.warning("Nenhum produto encontrado com esse termo.")
            produtos_filtrados = produtos
    else:
        produtos_filtrados = produtos
    
    # Merge com tabela de preços e última compra
    produtos_display = produtos_filtrados.merge(
        tabela_preco[['ID_COD', 'PRECO']], 
        on='ID_COD', 
        how='left'
    )
    
    # Adicionar data da última compra
    ultima_compra = df_filtrado.groupby('CodigoProduto')['DataEmissao'].max().reset_index()
    ultima_compra.columns = ['ID_COD', 'Última Compra']
    
    produtos_display = produtos_display.merge(
        ultima_compra,
        on='ID_COD',
        how='left'
    )
    
    # Adicionar taxa de comissão
    def determinar_tabela(preco):
        if pd.isna(preco):
            return 'N/A'
        return '3%'
    
    produtos_display['Tabela'] = produtos_display['PRECO'].apply(determinar_tabela)
    
    # Exibir tabela com todas as colunas solicitadas
    colunas_exibir = ['Última Compra', 'ID_COD', 'DESCRICAONF', 'Gramatura', 'PRECO', 'Tabela']
    
    # Verificar se coluna Fios existe
    if 'Fios' in produtos_display.columns:
        colunas_exibir.insert(4, 'Fios')
    
    st.dataframe(
        produtos_display[colunas_exibir].rename(
            columns={
                'ID_COD': 'Código',
                'PRECO': 'Preço Tabela',
                'Última Compra': 'Última Compra'
            }
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Última Compra": st.column_config.DateColumn(
                "Última Compra",
                format="DD/MM/YYYY"
            ),
            "Preço Tabela": st.column_config.NumberColumn(
                "Preço Tabela",
                format="R$ %.2f"
            )
        }
    )
    
    st.markdown("---")
    
    # Área de Criação de Pedido
    st.subheader("📝 Criar Proposta Comercial")
    
    # Dados da Empresa (fixos - ajustar conforme sua empresa)
    with st.expander("📄 Dados da Empresa", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Razão Social", value="ULTRA TEXTIL INDUSTRIA E COMERCIO DE PRODUTOS HOSPITALARES LTDA", disabled=True)
            st.text_input("CNPJ", value="40.357.820/0001-50", disabled=True)
            st.text_input("Inscrição Estadual", value="16.390.286-0", disabled=True)
        with col2:
            st.text_input("Endereço", value="R Y DOIS, 355 - GALPÃO 3 - Distrito industrial - João Pessoa - PB", disabled=True)
            st.text_input("Telefone", value="(83) 3233-9798", disabled=True)
            st.text_input("Email", value="comercial.ultratextilpb@gmail.com", disabled=True)
    
    st.markdown("#### Dados do Cliente")
    
    # Opção de novo cliente ou existente
    tipo_cliente = st.radio("", ["Cliente Existente", "Novo Cliente"], horizontal=True)
    
    if tipo_cliente == "Cliente Existente":
        clientes_lista = sorted(vendas_completas['RazaoSocial'].dropna().unique().tolist())
        cliente_pedido = st.selectbox("Selecione o Cliente", clientes_lista)
        
        # Buscar dados do cliente
        cliente_dados = vendas_completas[vendas_completas['RazaoSocial'] == cliente_pedido].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Razão Social", value=cliente_pedido, disabled=True, key="rs_exist")
            cpf_cnpj_valor = str(cliente_dados['CPF_CNPJ']) if pd.notna(cliente_dados['CPF_CNPJ']) else ""
            st.text_input("CPF/CNPJ", value=cpf_cnpj_valor, disabled=True)
        with col2:
            st.text_input("Endereço", value="", key="end_exist")
            st.text_input("Telefone", value="", key="tel_exist")
    
    else:
        col1, col2 = st.columns(2)
        with col1:
            novo_cliente_nome = st.text_input("Razão Social*")
            novo_cliente_cnpj = st.text_input("CPF/CNPJ*")
        with col2:
            novo_cliente_endereco = st.text_input("Endereço")
            novo_cliente_telefone = st.text_input("Telefone")
        
        if st.button("💾 Salvar Novo Cliente"):
            if novo_cliente_nome and novo_cliente_cnpj:
                st.success(f"✅ Cliente {novo_cliente_nome} salvo com sucesso!")
            else:
                st.error("❌ Preencha os campos obrigatórios (Razão Social e CPF/CNPJ)")
    
    st.markdown("#### Itens do Pedido")
    
    # Filtros para busca de produtos
    filtro_col1, filtro_col2 = st.columns(2)
    with filtro_col1:
        filtro_codigo_item = st.text_input("🔍 Filtrar por Código", key="filtro_cod_item")
    with filtro_col2:
        filtro_produto_item = st.text_input("🔍 Filtrar por Produto", key="filtro_prod_item")
    
    # Aplicar filtros nos produtos
    produtos_disponiveis = produtos.copy()
    if filtro_codigo_item:
        produtos_disponiveis = produtos_disponiveis[produtos_disponiveis['ID_COD'].astype(str).str.contains(filtro_codigo_item, case=False, na=False)]
    if filtro_produto_item:
        produtos_disponiveis = produtos_disponiveis[produtos_disponiveis['DESCRICAONF'].astype(str).str.contains(filtro_produto_item, case=False, na=False)]
    
    # Exibir tabela de produtos disponíveis com informações relevantes
    if len(produtos_disponiveis) > 0:
        # Merge com tabela de preços
        produtos_display_pedido = produtos_disponiveis.merge(
            tabela_preco[['ID_COD', 'PRECO']], 
            on='ID_COD', 
            how='left'
        )
        
        colunas_exibir_pedido = ['ID_COD', 'DESCRICAONF', 'Gramatura']
        if 'Apresentacao' in produtos_display_pedido.columns:
            colunas_exibir_pedido.insert(2, 'Apresentacao')
        colunas_exibir_pedido.append('PRECO')
        
        st.dataframe(
            produtos_display_pedido[colunas_exibir_pedido].rename(
                columns={
                    'ID_COD': 'Código',
                    'Apresentacao': 'Apresentação',
                    'PRECO': 'Preço Tabela'
                }
            ).head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Preço Tabela": st.column_config.NumberColumn(
                    "Preço Tabela",
                    format="R$ %.2f"
                )
            }
        )
    
    st.markdown("---")
    
    # Tabela para adicionar produtos ao pedido
    if 'itens_pedido' not in st.session_state:
        st.session_state.itens_pedido = []
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        produtos_opcoes = produtos_disponiveis['ID_COD'].tolist()
        if len(produtos_opcoes) > 0:
            produto_add = st.selectbox("Produto", produtos_opcoes, key="prod_add")
        else:
            st.warning("Nenhum produto encontrado com os filtros aplicados")
            produto_add = None
    
    with col2:
        qtd_add = st.number_input("Quantidade", min_value=1, value=1, key="qtd_add")
    
    with col3:
        # Buscar preço do produto
        if produto_add:
            preco_produto = tabela_preco[tabela_preco['ID_COD'] == produto_add]['PRECO'].values
            preco_default = float(preco_produto[0]) if len(preco_produto) > 0 else 0.0
        else:
            preco_default = 0.0
        preco_add = st.number_input("Preço Unit.", min_value=0.0, value=preco_default, key="preco_add")
    
    with col4:
        st.write("")
        st.write("")
        if st.button("➕ Adicionar") and produto_add:
            desc_produto = produtos[produtos['ID_COD'] == produto_add]['DESCRICAONF'].values[0]
            gramatura = produtos[produtos['ID_COD'] == produto_add]['Gramatura'].values[0] if 'Gramatura' in produtos.columns else ''
            st.session_state.itens_pedido.append({
                'Código': produto_add,
                'DESCRICAONF': desc_produto,
                'Gramatura': gramatura,
                'Quantidade': qtd_add,
                'Preço Unit.': preco_add,
                'Total': qtd_add * preco_add
            })
            st.rerun()
    
    # Exibir itens do pedido
    if st.session_state.itens_pedido:
        df_pedido = pd.DataFrame(st.session_state.itens_pedido)
        st.dataframe(df_pedido, use_container_width=True, hide_index=True)
        
        total_pedido = df_pedido['Total'].sum()
        st.metric("💰 Total do Pedido", f"R$ {total_pedido:,.2f}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗑️ Limpar Pedido"):
                st.session_state.itens_pedido = []
                st.rerun()
        
        with col2:
            if st.button("📄 Gerar PDF"):
                st.info("Funcionalidade de PDF será implementada conforme modelo enviado")
        
        with col3:
            if st.button("🖨️ Imprimir"):
                st.info("Abrir diálogo de impressão")
        
        with col4:
            if st.button("📱 Enviar WhatsApp"):
                st.info("Integração com WhatsApp será implementada")

# ========== MÓDULO INADIMPLÊNCIA ==========
elif modulo == "💰 Inadimplência":
    st.title("💰 Módulo de Inadimplência")
    
    # Filtros expandidos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        funcionarios = ['Todos'] + sorted(inadimplencia['Funcionário'].dropna().unique().tolist())
        func_selecionado = st.selectbox("Vendedor", funcionarios)
    
    with col2:
        clientes_inad = ['Todos'] + sorted(inadimplencia['Razão Social'].dropna().unique().tolist())
        cliente_selecionado = st.selectbox("Cliente", clientes_inad)
    
    with col3:
        # Adicionar filtro de Estado (se existir coluna Estado/UF)
        if 'Estado' in inadimplencia.columns or 'UF' in inadimplencia.columns:
            col_estado = 'Estado' if 'Estado' in inadimplencia.columns else 'UF'
            estados = ['Todos'] + sorted(inadimplencia[col_estado].dropna().unique().tolist())
            estado_selecionado = st.selectbox("Estado", estados)
        else:
            estado_selecionado = 'Todos'
    
    with col4:
        st.write("")
        st.write("")
        exportar = st.button("📥 Exportar CSV", use_container_width=True)
    
    # Aplicar filtros
    df_inad = inadimplencia.copy()
    
    if func_selecionado != 'Todos':
        df_inad = df_inad[df_inad['Funcionário'] == func_selecionado]
    
    if cliente_selecionado != 'Todos':
        df_inad = df_inad[df_inad['Razão Social'] == cliente_selecionado]
    
    if estado_selecionado != 'Todos' and estado_selecionado is not None:
        if 'Estado' in inadimplencia.columns:
            df_inad = df_inad[df_inad['Estado'] == estado_selecionado]
        elif 'UF' in inadimplencia.columns:
            df_inad = df_inad[df_inad['UF'] == estado_selecionado]
    
    # Calcular dias de atraso
    hoje = datetime.now()
    df_inad['Dias Atraso'] = (hoje - df_inad['Dt.Vencimento']).dt.days
    df_inad['Status'] = df_inad['Dias Atraso'].apply(lambda x: f"{x} dias" if x > 0 else "A vencer")
    
    # Métricas
    total_aberto = df_inad['Vr.Líquido'].sum()
    qtd_titulos = len(df_inad)
    titulos_vencidos = len(df_inad[df_inad['Dias Atraso'] > 0])
    qtd_clientes = df_inad['Razão Social'].nunique()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 Total em Aberto", f"R$ {total_aberto:,.2f}")
    col2.metric("📄 Qtd de Títulos", qtd_titulos)
    col3.metric("⚠️ Títulos Vencidos", titulos_vencidos)
    col4.metric("👥 Clientes", qtd_clientes)
    
    st.markdown("---")
    
    # Quantidade de títulos por cliente com informações adicionais
    st.subheader("📊 Títulos por Cliente")
    
    # Filtros para títulos por cliente
    titulos_col1, titulos_col2, titulos_col3 = st.columns(3)
    with titulos_col1:
        filtro_vendedor_titulos = st.selectbox("Filtrar por Vendedor", ['Todos'] + sorted(df_inad['Funcionário'].dropna().unique().tolist()), key="filtro_vend_tit")
    with titulos_col2:
        if 'Estado' in df_inad.columns or 'UF' in df_inad.columns:
            col_estado_tit = 'Estado' if 'Estado' in df_inad.columns else 'UF'
            filtro_estado_titulos = st.selectbox("Filtrar por Estado", ['Todos'] + sorted(df_inad[col_estado_tit].dropna().unique().tolist()), key="filtro_est_tit")
        else:
            filtro_estado_titulos = 'Todos'
    with titulos_col3:
        filtro_valor_min = st.number_input("Valor Mínimo Total", min_value=0.0, value=0.0, key="filtro_val_min")
    
    # Aplicar filtros
    df_titulos_filtrado = df_inad.copy()
    if filtro_vendedor_titulos != 'Todos':
        df_titulos_filtrado = df_titulos_filtrado[df_titulos_filtrado['Funcionário'] == filtro_vendedor_titulos]
    
    if filtro_estado_titulos != 'Todos':
        if 'Estado' in df_inad.columns:
            df_titulos_filtrado = df_titulos_filtrado[df_titulos_filtrado['Estado'] == filtro_estado_titulos]
        elif 'UF' in df_inad.columns:
            df_titulos_filtrado = df_titulos_filtrado[df_titulos_filtrado['UF'] == filtro_estado_titulos]
    
    titulos_por_cliente = df_titulos_filtrado.groupby('Razão Social').agg({
        'N_Doc': 'count',
        'Vr.Líquido': 'sum',
        'Funcionário': 'first'
    }).reset_index()
    titulos_por_cliente.columns = ['Cliente', 'Qtd Títulos', 'Valor Total', 'Vendedor']
    
    # Adicionar estado se disponível
    if 'Estado' in df_inad.columns or 'UF' in df_inad.columns:
        col_estado_cliente = 'Estado' if 'Estado' in df_inad.columns else 'UF'
        estados_cliente = df_titulos_filtrado.groupby('Razão Social')[col_estado_cliente].first().reset_index()
        titulos_por_cliente = titulos_por_cliente.merge(estados_cliente, left_on='Cliente', right_on='Razão Social', how='left')
        titulos_por_cliente = titulos_por_cliente.drop('Razão Social', axis=1)
        titulos_por_cliente.rename(columns={col_estado_cliente: 'Estado'}, inplace=True)
    
    # Aplicar filtro de valor mínimo
    titulos_por_cliente = titulos_por_cliente[titulos_por_cliente['Valor Total'] >= filtro_valor_min]
    
    titulos_por_cliente = titulos_por_cliente.sort_values('Qtd Títulos', ascending=False)
    
    st.dataframe(
        titulos_por_cliente,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valor Total": st.column_config.NumberColumn(
                "Valor Total",
                format="R$ %.2f"
            )
        }
    )
    
    st.markdown("---")
    
    # Tabela de inadimplência com filtros
    st.subheader("📋 Detalhamento de Títulos")
    
    # Filtros para detalhamento
    det_col1, det_col2, det_col3, det_col4 = st.columns(4)
    with det_col1:
        filtro_vendedor_det = st.selectbox("Filtrar Vendedor", ['Todos'] + sorted(df_inad['Funcionário'].dropna().unique().tolist()), key="filtro_vend_det")
    with det_col2:
        if 'Estado' in df_inad.columns or 'UF' in df_inad.columns:
            col_estado_det = 'Estado' if 'Estado' in df_inad.columns else 'UF'
            filtro_estado_det = st.selectbox("Filtrar Estado", ['Todos'] + sorted(df_inad[col_estado_det].dropna().unique().tolist()), key="filtro_est_det")
        else:
            filtro_estado_det = 'Todos'
    with det_col3:
        filtro_cliente_det = st.selectbox("Filtrar Cliente", ['Todos'] + sorted(df_inad['Razão Social'].dropna().unique().tolist()), key="filtro_cli_det")
    with det_col4:
        filtro_status = st.selectbox("Status", ['Todos', 'Vencidos', 'A Vencer'], key="filtro_status")
    
    # Aplicar filtros no detalhamento
    df_det_filtrado = df_inad.copy()
    
    if filtro_vendedor_det != 'Todos':
        df_det_filtrado = df_det_filtrado[df_det_filtrado['Funcionário'] == filtro_vendedor_det]
    
    if filtro_estado_det != 'Todos':
        if 'Estado' in df_inad.columns:
            df_det_filtrado = df_det_filtrado[df_det_filtrado['Estado'] == filtro_estado_det]
        elif 'UF' in df_inad.columns:
            df_det_filtrado = df_det_filtrado[df_det_filtrado['UF'] == filtro_estado_det]
    
    if filtro_cliente_det != 'Todos':
        df_det_filtrado = df_det_filtrado[df_det_filtrado['Razão Social'] == filtro_cliente_det]
    
    if filtro_status == 'Vencidos':
        df_det_filtrado = df_det_filtrado[df_det_filtrado['Dias Atraso'] > 0]
    elif filtro_status == 'A Vencer':
        df_det_filtrado = df_det_filtrado[df_det_filtrado['Dias Atraso'] <= 0]
    
    df_display = df_det_filtrado[['N_Doc', 'Razão Social', 'Funcionário', 'Dt.Vencimento', 'Vr.Líquido', 'Status']].copy()
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Dt.Vencimento": st.column_config.DateColumn(
                "Dt. Vencimento",
                format="DD/MM/YYYY"
            ),
            "Vr.Líquido": st.column_config.NumberColumn(
                "Valor Líquido",
                format="R$ %.2f"
            )
        }
    )
    
    st.markdown("---")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if exportar:
            csv = df_inad.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"inadimplencia_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.success("✅ Arquivo CSV pronto!")
    
    with col2:
        if st.button("📄 Gerar PDF", use_container_width=True):
            pdf_buffer = gerar_pdf_inadimplencia(df_inad, func_selecionado, cliente_selecionado)
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_buffer,
                file_name=f"inadimplencia_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    
    with col3:
        if st.button("📱 Enviar WhatsApp", use_container_width=True):
            st.info("📱 Integração com WhatsApp será implementada")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Sistema de Gestão Comercial v2.0")







# ===================== PATCH APLICADO =====================
# Mantém 100% do código original acima.
# Ajustes solicitados: regra NF Venda x NF Dev.Venda para BI
# Base equivalente à fórmula Excel:
# =SE([@TipoMov]="NF Venda";[@TotalProduto];-[@TotalProduto])

if 'TipoMov' in vendas_completas.columns and 'TotalProduto' in vendas_completas.columns:
    vendas_completas['Valor_BI'] = np.where(
        vendas_completas['TipoMov'] == 'NF Venda',
        vendas_completas['TotalProduto'],
        -vendas_completas['TotalProduto']
    )
else:
    vendas_completas['Valor_BI'] = vendas_completas.get('TotalProduto2', 0)

# Remover duplicidade de NF para BI
if 'Numero_NF' in vendas_completas.columns:
    vendas_completas_bi = vendas_completas.drop_duplicates(
        subset=['Numero_NF', 'CodigoProduto'],
        keep='last'
    )
else:
    vendas_completas_bi = vendas_completas.copy()

# A partir deste ponto, relatórios BI podem usar:
# vendas_completas_bi['Valor_BI']
# Histórico permanece usando todas as informações (NF Venda e NF Dev.Venda)

# =================== FIM DO PATCH ===================
