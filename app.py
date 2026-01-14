import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(page_title="Gestão Comercial", layout="wide", page_icon="📊")

# Função para carregar dados
@st.cache_data
def carregar_dados():
    """Carrega todas as planilhas necessárias"""
    try:
        # Mensagens de debug
        st.sidebar.info("Carregando dados...")
        
        # 1. Vendas
        st.sidebar.text("📄 Carregando vendas...")
        vendas = pd.read_excel('CONSULTA_VENDEDORES.xlsx')
        st.sidebar.success(f"✅ Vendas: {len(vendas)} registros")
        
        # Verificar e converter data
        if 'DataEmissao' in vendas.columns:
            vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        else:
            st.error("❌ Coluna 'DataEmissao' não encontrada em CONSULTA_VENDEDORES.xlsx")
            st.write("Colunas disponíveis:", vendas.columns.tolist())
            return None, None, None, None
        
        # 2. Produtos
        st.sidebar.text("📦 Carregando produtos...")
        produtos = pd.read_excel('Produtos_Agrupados_Completos_conciliados.xlsx')
        st.sidebar.success(f"✅ Produtos: {len(produtos)} registros")
        
        # Verificar coluna ID_COD
        if 'ID_COD' not in produtos.columns:
            st.error("❌ Coluna 'ID_COD' não encontrada em Produtos")
            st.write("Colunas disponíveis:", produtos.columns.tolist())
            return None, None, None, None
        
        # 3. Tabela de Preços
        st.sidebar.text("💰 Carregando tabela de preços...")
        tabela_preco = pd.read_excel('TABELAS_NE.xlsx')
        st.sidebar.success(f"✅ Preços: {len(tabela_preco)} registros")
        
        # 4. Inadimplência
        st.sidebar.text("📋 Carregando inadimplência...")
        inadimplencia = pd.read_excel('XLS_Grid_LANCAMENTO A RECEBER.xls')
        st.sidebar.success(f"✅ Inadimplência: {len(inadimplencia)} registros")
        
        if 'Dt.Vencimento' in inadimplencia.columns:
            inadimplencia['Dt.Vencimento'] = pd.to_datetime(inadimplencia['Dt.Vencimento'], errors='coerce')
        
        st.sidebar.success("🎉 Todos os dados carregados!")
        
        return vendas, produtos, tabela_preco, inadimplencia
        
    except FileNotFoundError as e:
        st.error(f"❌ Arquivo não encontrado: {str(e)}")
        st.info("📁 Certifique-se de que os arquivos estão na raiz do repositório GitHub")
        return None, None, None, None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.write("Tipo do erro:", type(e).__name__)
        import traceback
        st.code(traceback.format_exc())
        return None, None, None, None

# Função para conciliar vendas com produtos e preços
@st.cache_data
def conciliar_dados(vendas, produtos, tabela_preco):
    """Realiza a conciliação entre vendas, produtos e tabela de preços"""
    # Merge vendas com produtos
    vendas_completas = vendas.merge(
        produtos[['ID_COD', 'Gramatura', 'Descrição']], 
        left_on='CodigoProduto', 
        right_on='ID_COD', 
        how='left'
    )
    
    # Merge com tabela de preços
    vendas_completas = vendas_completas.merge(
        tabela_preco[['ID_COD', 'PRECO']], 
        left_on='CodigoProduto', 
        right_on='ID_COD', 
        how='left',
        suffixes=('', '_preco')
    )
    
    # Renomear coluna de preço de tabela
    vendas_completas.rename(columns={'PRECO': 'PrecoTabela'}, inplace=True)
    
    # Calcular desconto percentual
    vendas_completas['DescontoPerc'] = (
        (vendas_completas['PrecoTabela'] - vendas_completas['PrecoUnit']) / 
        vendas_completas['PrecoTabela'] * 100
    )
    
    # Calcular comissão
    def calcular_comissao(row):
        if pd.isna(row['PrecoTabela']) or row['PrecoTabela'] == 0:
            return 0
        if row['PrecoUnit'] == row['PrecoTabela']:
            return row['TotalLiquidoNF'] * 0.03
        elif row['PrecoUnit'] >= (row['PrecoTabela'] * 1.06):
            return row['TotalLiquidoNF'] * 0.04
        else:
            return row['TotalLiquidoNF'] * 0.03
    
    vendas_completas['Comissao'] = vendas_completas.apply(calcular_comissao, axis=1)
    
    return vendas_completas

# Carregar dados
vendas, produtos, tabela_preco, inadimplencia = carregar_dados()

if vendas is None:
    st.stop()

# Conciliar dados
vendas_completas = conciliar_dados(vendas, produtos, tabela_preco)

# ========== SIDEBAR ==========
st.sidebar.title("🎯 Filtros Globais")

# Filtro de Data
data_min = vendas_completas['DataEmissao'].min().date()
data_max = vendas_completas['DataEmissao'].max().date()

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.date_input("Data Início", data_min)
with col2:
    data_fim = st.date_input("Data Fim", data_max)

# Filtro de Vendedor
vendedores = ['Todos'] + sorted(vendas_completas['Vendedor'].unique().tolist())
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
    
    total_faturamento = df_filtrado['TotalLiquidoNF'].sum()
    total_clientes = df_filtrado['CPF_CNPJ'].nunique()
    ticket_medio = df_filtrado['TotalLiquidoNF'].mean()
    
    # Positivação de Carteira
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
        df_mensal = df_filtrado.groupby(df_filtrado['DataEmissao'].dt.to_period('M'))['TotalLiquidoNF'].sum().reset_index()
        df_mensal['DataEmissao'] = df_mensal['DataEmissao'].astype(str)
        fig = px.line(df_mensal, x='DataEmissao', y='TotalLiquidoNF', 
                      labels={'TotalLiquidoNF': 'Faturamento', 'DataEmissao': 'Mês'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top 10 Clientes")
        top_clientes = df_filtrado.groupby('RazaoSocial')['TotalLiquidoNF'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(top_clientes, orientation='h', 
                     labels={'value': 'Faturamento', 'RazaoSocial': 'Cliente'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Rankings
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎖️ Ranking de Vendedores")
        ranking_vendedores = df_filtrado.groupby('Vendedor').agg({
            'TotalLiquidoNF': 'sum',
            'Comissao': 'sum'
        }).sort_values('TotalLiquidoNF', ascending=False).reset_index()
        ranking_vendedores.columns = ['Vendedor', 'Faturamento', 'Comissão']
        ranking_vendedores['Faturamento'] = ranking_vendedores['Faturamento'].apply(lambda x: f"R$ {x:,.2f}")
        ranking_vendedores['Comissão'] = ranking_vendedores['Comissão'].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(ranking_vendedores, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("💸 Análise de Desconto por Vendedor")
        analise_desconto = df_filtrado.groupby('Vendedor')['DescontoPerc'].mean().sort_values(ascending=False).reset_index()
        analise_desconto.columns = ['Vendedor', 'Desconto Médio (%)']
        analise_desconto['Desconto Médio (%)'] = analise_desconto['Desconto Médio (%)'].apply(lambda x: f"{x:.2f}%")
        st.dataframe(analise_desconto, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Churn - Clientes sem compras há mais de 60 dias
    st.subheader("⚠️ Clientes sem Compras (últimos 60 dias)")
    
    clientes_recentes_set = set(df_filtrado[df_filtrado['DataEmissao'] >= data_60_dias]['CPF_CNPJ'].unique())
    todos_clientes_set = set(vendas_completas['CPF_CNPJ'].unique())
    clientes_churn = todos_clientes_set - clientes_recentes_set
    
    df_churn = vendas_completas[vendas_completas['CPF_CNPJ'].isin(clientes_churn)][['RazaoSocial', 'CPF_CNPJ']].drop_duplicates()
    
    st.info(f"📊 Total de clientes inativos: {len(df_churn)}")
    st.dataframe(df_churn, use_container_width=True, hide_index=True)
    
    # Histórico detalhado
    st.markdown("---")
    st.subheader("🔍 Histórico Detalhado")
    
    tab1, tab2 = st.tabs(["Por Cliente", "Por Produto"])
    
    with tab1:
        cliente_hist = st.selectbox("Selecione o Cliente", df_filtrado['RazaoSocial'].unique())
        df_cliente = df_filtrado[df_filtrado['RazaoSocial'] == cliente_hist][
            ['DataEmissao', 'CodigoProduto', 'Descrição', 'Gramatura', 'Quantidade', 
             'PrecoUnit', 'TotalLiquidoNF', 'CondPagamento']
        ].sort_values('DataEmissao', ascending=False)
        st.dataframe(df_cliente, use_container_width=True, hide_index=True)
    
    with tab2:
        produto_hist = st.selectbox("Selecione o Produto", df_filtrado['CodigoProduto'].unique())
        df_produto = df_filtrado[df_filtrado['CodigoProduto'] == produto_hist][
            ['DataEmissao', 'RazaoSocial', 'Vendedor', 'Quantidade', 
             'PrecoUnit', 'PrecoTabela', 'TotalLiquidoNF', 'CondPagamento']
        ].sort_values('DataEmissao', ascending=False)
        st.dataframe(df_produto, use_container_width=True, hide_index=True)

# ========== MÓDULO PEDIDOS ==========
elif modulo == "📦 Pedidos e Comissões":
    st.title("📦 Módulo de Pedidos e Comissões")
    
    st.info("💡 **Regras de Comissão:** 3% quando Preço = Tabela | 4% quando Preço ≥ Tabela + 6%")
    
    # Busca inteligente
    busca = st.text_input("🔍 Buscar por Código ou Descrição do Produto", "")
    
    # Filtrar produtos
    if busca:
        mask_busca = (produtos['ID_COD'].str.contains(busca, case=False, na=False)) | \
                     (produtos['Descrição'].str.contains(busca, case=False, na=False))
        produtos_filtrados = produtos[mask_busca]
    else:
        produtos_filtrados = produtos
    
    # Merge com tabela de preços
    produtos_display = produtos_filtrados.merge(
        tabela_preco[['ID_COD', 'PRECO']], 
        on='ID_COD', 
        how='left'
    )
    
    # Adicionar coluna de comissão base
    produtos_display['Comissão Base'] = '3% (4% se +6%)'
    
    # Exibir tabela
    st.dataframe(
        produtos_display[['ID_COD', 'Descrição', 'Gramatura', 'PRECO', 'Comissão Base']].rename(
            columns={'ID_COD': 'Código', 'PRECO': 'Preço Tabela'}
        ),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Simulador de Comissão
    st.subheader("🧮 Simulador de Comissão")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        produto_sim = st.selectbox("Produto", produtos['ID_COD'].unique())
        preco_tab = tabela_preco[tabela_preco['ID_COD'] == produto_sim]['PRECO'].values[0] if len(tabela_preco[tabela_preco['ID_COD'] == produto_sim]) > 0 else 0
        st.write(f"**Preço Tabela:** R$ {preco_tab:.2f}")
    
    with col2:
        qtd_sim = st.number_input("Quantidade", min_value=1, value=100)
    
    with col3:
        preco_venda_sim = st.number_input("Preço de Venda", min_value=0.0, value=float(preco_tab))
    
    total_venda = qtd_sim * preco_venda_sim
    
    if preco_venda_sim == preco_tab:
        comissao_sim = total_venda * 0.03
        taxa = "3%"
    elif preco_venda_sim >= (preco_tab * 1.06):
        comissao_sim = total_venda * 0.04
        taxa = "4%"
    else:
        comissao_sim = total_venda * 0.03
        taxa = "3%"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total da Venda", f"R$ {total_venda:,.2f}")
    col2.metric("Taxa de Comissão", taxa)
    col3.metric("Comissão", f"R$ {comissao_sim:,.2f}", delta=None)

# ========== MÓDULO INADIMPLÊNCIA ==========
elif modulo == "💰 Inadimplência":
    st.title("💰 Módulo de Inadimplência")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        funcionarios = ['Todos'] + sorted(inadimplencia['Funcionário'].dropna().unique().tolist())
        func_selecionado = st.selectbox("Vendedor", funcionarios)
    
    with col2:
        clientes_inad = ['Todos'] + sorted(inadimplencia['Razão Social'].dropna().unique().tolist())
        cliente_selecionado = st.selectbox("Cliente", clientes_inad)
    
    with col3:
        st.write("")
        st.write("")
        exportar = st.button("📥 Exportar para CSV", use_container_width=True)
    
    # Aplicar filtros
    df_inad = inadimplencia.copy()
    
    if func_selecionado != 'Todos':
        df_inad = df_inad[df_inad['Funcionário'] == func_selecionado]
    
    if cliente_selecionado != 'Todos':
        df_inad = df_inad[df_inad['Razão Social'] == cliente_selecionado]
    
    # Calcular dias de atraso
    hoje = datetime.now()
    df_inad['Dias Atraso'] = (hoje - df_inad['Dt.Vencimento']).dt.days
    df_inad['Status'] = df_inad['Dias Atraso'].apply(lambda x: f"{x} dias" if x > 0 else "A vencer")
    
    # Métricas
    total_aberto = df_inad['Vr.Líquido'].sum()
    qtd_titulos = len(df_inad)
    titulos_vencidos = len(df_inad[df_inad['Dias Atraso'] > 0])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total em Aberto", f"R$ {total_aberto:,.2f}")
    col2.metric("📄 Quantidade de Títulos", qtd_titulos)
    col3.metric("⚠️ Títulos Vencidos", titulos_vencidos)
    
    st.markdown("---")
    
    # Tabela de inadimplência
    df_display = df_inad[['No Doc', 'Razão Social', 'Funcionário', 'Dt.Vencimento', 'Vr.Líquido', 'Status']].copy()
    df_display['Dt.Vencimento'] = df_display['Dt.Vencimento'].dt.strftime('%d/%m/%Y')
    df_display['Vr.Líquido'] = df_display['Vr.Líquido'].apply(lambda x: f"R$ {x:,.2f}")
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Exportar
    if exportar:
        csv = df_inad.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"inadimplencia_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        st.success("✅ Arquivo pronto para download! Use para enviar por WhatsApp/Email.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Sistema de Gestão Comercial v1.0")
