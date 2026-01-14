import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configurações de Página
st.set_page_config(page_title="Gestão Comercial Integrada", layout="wide")

# --- FUNÇÕES DE CARGA E TRATAMENTO ---
@st.cache_data
def load_data():
    # Nota: Em produção, garanta que os caminhos dos arquivos estejam corretos
    df_vendas = pd.read_excel("CONSULTA_VENDEDORES.xlsx")
    df_produtos = pd.read_excel("Produtos_Agrupados_Completos_conciliados.xlsx")
    df_tabela = pd.read_excel("TABELAS_NE.xlsx")
    df_inad = pd.read_excel("XLS_Grid_LANCAMENTO A RECEBER.xls") # Requer xlrd

    # Padronização de Chaves para Join
    df_vendas['CodigoProduto'] = df_vendas['CodigoProduto'].astype(str)
    df_produtos['ID_COD'] = df_produtos['ID_COD'].astype(str)
    df_tabela['ID_COD'] = df_tabela['ID_COD'].astype(str)

    # Merge Vendas + Produtos + Tabela
    df_master = pd.merge(df_vendas, df_produtos, left_on='CodigoProduto', right_on='ID_COD', how='left')
    df_master = pd.merge(df_master, df_tabela[['ID_COD', 'PRECO']], on='ID_COD', how='left')
    
    return df_master, df_inad, df_produtos, df_tabela

df_master, df_inad, df_produtos, df_tabela = load_data()

# --- SIDEBAR: FILTROS GLOBAIS ---
st.sidebar.header("Filtros Globais")
vendedores = st.sidebar.multiselect("Vendedor", options=df_master['Vendedor'].unique())
data_range = st.sidebar.date_input("Período", [df_master['DataEmissao'].min(), df_master['DataEmissao'].max()])

# Aplicação dos Filtros
df_filtrado = df_master.copy()
if vendedores:
    df_filtrado = df_filtrado[df_filtrado['Vendedor'].isin(vendedores)]
# Filtro de data (conversão para datetime necessária)
df_filtrado = df_filtrado[(df_filtrado['DataEmissao'].dt.date >= data_range[0]) & 
                           (df_filtrado['DataEmissao'].dt.date <= data_range[1])]

# --- NAVEGAÇÃO ---
aba = st.sidebar.radio("Navegação", ["Dashboard BI", "Pedidos & Comissões", "Financeiro"])

# --- MÓDULO A: DASHBOARD COMERCIAL (BI) ---
if aba == "Dashboard BI":
    st.title("📊 Relatório Comercial Completo")
    
    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    faturamento = df_filtrado['TotalLiquidoNF'].sum()
    c1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
    
    # Cálculo Positivação
    clientes_ativos = df_filtrado['RazaoSocial'].nunique()
    total_clientes = df_master['RazaoSocial'].nunique() # Simplificado: total da base histórica
    positivacao = (clientes_ativos / total_clientes) * 100
    c2.metric("Positivação", f"{positivacao:.1f}%")

    # Cálculo Desconto Médio
    df_filtrado['Desc_Perc'] = (df_filtrado['PrecoUnit'] - df_filtrado['PRECO']) / df_filtrado['PRECO']
    desc_medio = df_filtrado['Desc_Perc'].mean() * 100
    c3.metric("Margem/Desconto Médio", f"{desc_medio:.1f}%")

    # Churn (Sem compras > 60 dias)
    hoje = pd.to_datetime(datetime.now())
    u_compra = df_master.groupby('RazaoSocial')['DataEmissao'].max().reset_index()
    churn_list = u_compra[u_compra['DataEmissao'] < (hoje - timedelta(days=60))]
    c4.metric("Clientes em Churn", len(churn_list))

    # Gráficos
    col_esq, col_dir = st.columns(2)
    
    with col_esq:
        st.subheader("Ranking de Vendedores")
        rank_vend = df_filtrado.groupby('Vendedor')['TotalLiquidoNF'].sum().sort_values(ascending=False).reset_index()
        fig_vend = px.bar(rank_vend, x='TotalLiquidoNF', y='Vendedor', orientation='h', color='TotalLiquidoNF')
        st.plotly_chart(fig_vend, use_container_width=True)

    with col_dir:
        st.subheader("Mix de Produtos (Curva ABC)")
        mix = df_filtrado.groupby('Descrição')['TotalLiquidoNF'].sum().reset_index()
        fig_pie = px.pie(mix, values='TotalLiquidoNF', names='Descrição', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

# --- MÓDULO B: PEDIDOS E COMISSÕES ---
elif aba == "Pedidos & Comissões":
    st.title("📝 Módulo de Pedidos e Comissões")
    
    with st.expander("Calculadora de Comissão (Regra de Negócio)", expanded=True):
        # Lógica de Comissão via LaTeX para clareza:
        # $Comissão = 3\% \text{ se } P = P_{tab}; 4\% \text{ se } P \geq P_{tab} + 6\%$
        
        def calc_comissao(row):
            if row['PrecoUnit'] >= (row['PRECO'] * 1.06): return row['TotalLiquidoNF'] * 0.04
            elif row['PrecoUnit'] == row['PRECO']: return row['TotalLiquidoNF'] * 0.03
            else: return 0 # Ou regra padrão para outros casos
        
        df_filtrado['Comissao_R$'] = df_filtrado.apply(calc_comissao, axis=1)
        st.dataframe(df_filtrado[['Vendedor', 'RazaoSocial', 'CodigoProduto', 'PrecoUnit', 'PRECO', 'Comissao_R$']])

    st.subheader("Busca Inteligente de Produtos")
    busca = st.text_input("Digite o Código ou Descrição do Produto")
    if busca:
        sugestoes = df_produtos[
            (df_produtos['ID_COD'].astype(str).str.contains(busca)) | 
            (df_produtos['Descrição'].str.contains(busca, case=False))
        ]
        st.write("Resultados encontrados:")
        # Ao selecionar, carregaria automaticamente (exemplo simplificado de exibição)
        st.table(pd.merge(sugestoes, df_tabela[['ID_COD', 'PRECO']], on='ID_COD'))

# --- MÓDULO C: FINANCEIRO (INADIMPLÊNCIA) ---
elif aba == "Financeiro":
    st.title("💸 Gestão de Inadimplência")
    
    # Filtros específicos do financeiro
    f_cliente = st.selectbox("Filtrar por Cliente", ["Todos"] + list(df_inad['Razão Social'].unique()))
    
    df_inad_f = df_inad.copy()
    if f_cliente != "Todos":
        df_inad_f = df_inad_f[df_inad_f['Razão Social'] == f_cliente]
    
    # Tabela de pendências
    st.dataframe(df_inad_f[['Razão Social', 'Funcionário', 'Nº Doc', 'Dt.Vencimento', 'Vr.Líquido']])
    
    # Exportação
    csv = df_inad_f.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Relatório para WhatsApp/E-mail",
        data=csv,
        file_name='pendencias_financeiras.csv',
        mime='text/csv',
    )
