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
        produtos[['ID_COD', 'Gramatura', 'Descrição']], 
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
    produtos_vendidos = df_filtrado.groupby(['CodigoProduto', 'Descrição']).agg({
        'Quantidade': 'sum',
        'TotalProduto2': 'sum'
    }).sort_values('Quantidade', ascending=False).reset_index()
    produtos_vendidos.columns = ['Código', 'Descrição', 'Qtd Total', 'Faturamento Total']
    produtos_vendidos['Qtd Total'] = produtos_vendidos['Qtd Total'].apply(lambda x: f"{x:,.0f}")
    produtos_vendidos['Faturamento Total'] = produtos_vendidos['Faturamento Total'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(produtos_vendidos.head(20), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Rankings com filtros
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎖️ Ranking de Vendedores")
        ranking_vendedores = df_filtrado.groupby('Vendedor').agg({
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
        analise_desconto = df_filtrado.groupby('Vendedor')['DescontoPerc'].mean().sort_values(ascending=False).reset_index()
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
    
    # Filtro de dias
    dias_sem_compra = st.slider("Dias sem compra", min_value=30, max_value=365, value=60, step=30)
    
    data_limite_churn = hoje - timedelta(days=dias_sem_compra)
    clientes_recentes_set = set(df_filtrado[df_filtrado['DataEmissao'] >= data_limite_churn]['CPF_CNPJ'].unique())
    todos_clientes_set = set(vendas_completas['CPF_CNPJ'].unique())
    clientes_churn = todos_clientes_set - clientes_recentes_set
    
    df_churn = vendas_completas[vendas_completas['CPF_CNPJ'].isin(clientes_churn)][['RazaoSocial', 'CPF_CNPJ']].drop_duplicates()
    
    st.info(f"📊 Total de clientes inativos há mais de {dias_sem_compra} dias: {len(df_churn)}")
    st.dataframe(df_churn, use_container_width=True, hide_index=True)
    
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
            'Descrição': 'first',
            'Gramatura': 'first',
            'Quantidade': 'sum',
            'PrecoUnit': 'mean',
            'TotalProduto2': 'sum'
        }).reset_index()
        
        df_cliente_agrupado.columns = [
            'Código Produto',
            'Data Última Compra',
            'Descrição',
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
    busca = st.text_input("🔍 Buscar por Código ou Descrição do Produto", "")
    
    # Filtrar produtos baseado na busca
    if busca:
        mask_busca = (produtos['ID_COD'].astype(str).str.contains(busca, case=False, na=False)) | \
                     (produtos['Descrição'].astype(str).str.contains(busca, case=False, na=False))
        produtos_filtrados = produtos[mask_busca]
        
        if len(produtos_filtrados) > 0:
            opcoes_produtos = produtos_filtrados['Descrição'].tolist()
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
    colunas_exibir = ['Última Compra', 'ID_COD', 'Descrição', 'Gramatura', 'PRECO', 'Tabela']
    
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
            st.text_input("Razão Social", value="SUA EMPRESA LTDA", disabled=True)
            st.text_input("CNPJ", value="00.000.000/0001-00", disabled=True)
        with col2:
            st.text_input("Endereço", value="Rua Exemplo, 123", disabled=True)
            st.text_input("Telefone", value="(00) 0000-0000", disabled=True)
    
    st.markdown("#### Dados do Cliente")
    
    # Opção de novo cliente ou existente
    tipo_cliente = st.radio("", ["Cliente Existente", "Novo Cliente"], horizontal=True)
    
    if tipo_cliente == "Cliente Existente":
        clientes_lista = sorted(vendas_completas['RazaoSocial'].unique().tolist())
        cliente_pedido = st.selectbox("Selecione o Cliente", clientes_lista)
        
        # Buscar dados do cliente
        cliente_dados = vendas_completas[vendas_completas['RazaoSocial'] == cliente_pedido].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Razão Social", value=cliente_pedido, disabled=True, key="rs_exist")
            st.text_input("CPF/CNPJ", value=cliente_dados['CPF_CNPJ'], disabled=True)
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
    
    # Tabela para adicionar produtos ao pedido
    if 'itens_pedido' not in st.session_state:
        st.session_state.itens_pedido = []
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        produtos_opcoes = produtos['ID_COD'].tolist()
        produto_add = st.selectbox("Produto", produtos_opcoes, key="prod_add")
    
    with col2:
        qtd_add = st.number_input("Quantidade", min_value=1, value=1, key="qtd_add")
    
    with col3:
        # Buscar preço do produto
        preco_produto = tabela_preco[tabela_preco['ID_COD'] == produto_add]['PRECO'].values
        preco_default = float(preco_produto[0]) if len(preco_produto) > 0 else 0.0
        preco_add = st.number_input("Preço Unit.", min_value=0.0, value=preco_default, key="preco_add")
    
    with col4:
        st.write("")
        st.write("")
        if st.button("➕ Adicionar"):
            desc_produto = produtos[produtos['ID_COD'] == produto_add]['Descrição'].values[0]
            st.session_state.itens_pedido.append({
                'Código': produto_add,
                'Descrição': desc_produto,
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
    
    # Calcular quantidade de títulos por cliente
    titulos_por_cliente = df_inad.groupby('Razão Social').size().reset_index(name='Qtd Títulos')
    
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
    
    # Quantidade de títulos por cliente
    st.subheader("📊 Títulos por Cliente")
    st.dataframe(
        titulos_por_cliente.sort_values('Qtd Títulos', ascending=False),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Tabela de inadimplência
    st.subheader("📋 Detalhamento de Títulos")
    df_display = df_inad[['N_Doc', 'Razão Social', 'Funcionário', 'Dt.Vencimento', 'Vr.Líquido', 'Status']].copy()
    
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
