import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Gestão Comercial", layout="wide")

# =====================================================
# BLOCO DE PATHS (CORRIGIDO PARA STREAMLIT CLOUD + GITHUB)
# =====================================================

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")

PATH_VENDAS = os.path.join(DATA_DIR, "CONSULTA_VENDEDORES.xlsx")
PATH_PRODUTOS = os.path.join(DATA_DIR, "Produtos_Agrupados_Completos_conciliados.xlsx")
PATH_TABELA = os.path.join(DATA_DIR, "TABELAS_NE.xlsx")
PATH_INAD = os.path.join(DATA_DIR, "XLS_Grid_LANCAMENTO A RECEBER.xls")

# =====================================================
# CARGA DE DADOS
# =====================================================

@st.cache_data
def carregar_dados():
    vendas = pd.read_excel(PATH_VENDAS)
    produtos = pd.read_excel(PATH_PRODUTOS)
    tabela = pd.read_excel(PATH_TABELA)
    inad = pd.read_excel(PATH_INAD)
    return vendas, produtos, tabela, inad

vendas, produtos, tabela, inad = carregar_dados()

# =====================================================
# TRATAMENTO E CONCILIAÇÃO
# =====================================================

vendas["DataEmissao"] = pd.to_datetime(vendas["DataEmissao"])
inad["Dt.Vencimento"] = pd.to_datetime(inad["Dt.Vencimento"])

produtos = produtos.rename(columns={"Descrição": "Descricao"})
tabela = tabela.rename(columns={"PRECO": "PrecoTabela"})

base = vendas.merge(
    produtos[["ID_COD", "Gramatura", "Descricao"]],
    left_on="CodigoProduto",
    right_on="ID_COD",
    how="left"
).merge(
    tabela[["ID_COD", "PrecoTabela"]],
    left_on="CodigoProduto",
    right_on="ID_COD",
    how="left"
)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("Gestão Comercial")

data_inicio = st.sidebar.date_input(
    "Data inicial",
    base["DataEmissao"].min().date()
)

data_fim = st.sidebar.date_input(
    "Data final",
    base["DataEmissao"].max().date()
)

vendedor_sel = st.sidebar.selectbox(
    "Vendedor",
    ["Todos"] + sorted(base["Vendedor"].dropna().unique().tolist())
)

base_filtro = base[
    (base["DataEmissao"].dt.date >= data_inicio) &
    (base["DataEmissao"].dt.date <= data_fim)
]

if vendedor_sel != "Todos":
    base_filtro = base_filtro[base_filtro["Vendedor"] == vendedor_sel]

modulo = st.sidebar.radio(
    "Módulos",
    ["Relatório Comercial (BI)", "Pedidos e Comissões", "Inadimplência"]
)

# =====================================================
# MÓDULO BI
# =====================================================

if modulo == "Relatório Comercial (BI)":

    st.title("Relatório Comercial Completo")

    faturamento = base_filtro["TotalLiquidoNF"].sum()
    clientes = base_filtro["CPF_CNPJ"].nunique()
    ticket = base_filtro["TotalLiquidoNF"].mean()

    clientes_total = base["CPF_CNPJ"].nunique()
    positivacao = (clientes / clientes_total) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento", f"R$ {faturamento:,.2f}")
    col2.metric("Clientes Ativos", clientes)
    col3.metric("Ticket Médio", f"R$ {ticket:,.2f}")
    col4.metric("Positivação", f"{positivacao:.1f}%")

    st.subheader("Evolução Mensal de Faturamento")
    evolucao = base_filtro.groupby(base_filtro["DataEmissao"].dt.to_period("M"))["TotalLiquidoNF"].sum().reset_index()
    evolucao["DataEmissao"] = evolucao["DataEmissao"].astype(str)
    st.line_chart(evolucao, x="DataEmissao", y="TotalLiquidoNF")

    st.subheader("Ranking de Clientes")
    ranking_clientes = base_filtro.groupby("RazaoSocial")["TotalLiquidoNF"].sum().sort_values(ascending=False)
    st.dataframe(ranking_clientes)

    st.subheader("Ranking de Vendedores")
    ranking_vendedores = base_filtro.groupby("Vendedor")["TotalLiquidoNF"].sum().sort_values(ascending=False)
    st.dataframe(ranking_vendedores)

    st.subheader("Clientes sem compras há mais de 60 dias")
    limite = datetime.today() - timedelta(days=60)
    churn = base.groupby("CPF_CNPJ")["DataEmissao"].max()
    churn = churn[churn < limite]
    st.dataframe(churn.reset_index())

    st.subheader("Análise Média de Desconto por Vendedor")
    base_filtro["Desconto_%"] = (base_filtro["PrecoTabela"] - base_filtro["PrecoUnit"]) / base_filtro["PrecoTabela"] * 100
    desconto = base_filtro.groupby("Vendedor")["Desconto_%"].mean()
    st.dataframe(desconto)

# =====================================================
# MÓDULO PEDIDOS E COMISSÕES
# =====================================================

elif modulo == "Pedidos e Comissões":

    st.title("Pedidos e Comissões")

    busca = st.text_input("Buscar por Código ou Descrição")

    produtos_filtro = base[[
        "CodigoProduto", "Descricao", "Gramatura", "PrecoTabela"
    ]].drop_duplicates()

    if busca:
        produtos_filtro = produtos_filtro[
            produtos_filtro["CodigoProduto"].str.contains(busca, case=False, na=False) |
            produtos_filtro["Descricao"].str.contains(busca, case=False, na=False)
        ]

    st.dataframe(produtos_filtro)

    st.info("Regras de Comissão: 3% no preço tabela | 4% se preço ≥ tabela + 6%")

# =====================================================
# MÓDULO INADIMPLÊNCIA
# =====================================================

else:

    st.title("Inadimplência")

    vend_sel = st.selectbox(
        "Vendedor",
        ["Todos"] + sorted(inad["Funcionário"].dropna().unique().tolist())
    )

    cli_sel = st.selectbox(
        "Cliente",
        ["Todos"] + sorted(inad["Razão Social"].dropna().unique().tolist())
    )

    inad_filtro = inad.copy()

    if vend_sel != "Todos":
        inad_filtro = inad_filtro[inad_filtro["Funcionário"] == vend_sel]

    if cli_sel != "Todos":
        inad_filtro = inad_filtro[inad_filtro["Razão Social"] == cli_sel]

    st.dataframe(inad_filtro)

    total_aberto = inad_filtro["Vr.Líquido"].sum()
    st.metric("Total em Aberto", f"R$ {total_aberto:,.2f}")

    st.download_button(
        "Exportar CSV",
        inad_filtro.to_csv(index=False).encode("utf-8"),
        "inadimplencia.csv",
        "text/csv"
    )
