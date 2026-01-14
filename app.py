import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(layout="wide", page_title="Gestão Comercial")

# ===============================
# CAMINHOS DAS PLANILHAS
# ===============================
CAMINHO_VENDAS = "data/VENDAS.xlsx"
CAMINHO_PRODUTOS = "data/PRODUTOS.xlsx"
CAMINHO_PRECOS = "data/TABELA_PRECOS.xlsx"
CAMINHO_INADIMPLENCIA = "data/INADIMPLENCIA.xlsx"

# ===============================
# CARREGAMENTO DOS DADOS
# ===============================
@st.cache_data
def carregar_dados():
    vendas = pd.read_excel(CAMINHO_VENDAS)
    produtos = pd.read_excel(CAMINHO_PRODUTOS)
    precos = pd.read_excel(CAMINHO_PRECOS)
    inad = pd.read_excel(CAMINHO_INADIMPLENCIA)
    return vendas, produtos, precos, inad

vendas, produtos, tabela_precos, inadimplencia = carregar_dados()

# ===============================
# TRATAMENTOS
# ===============================
vendas["DataEmissao"] = pd.to_datetime(vendas["DataEmissao"])

vendas = vendas.merge(
    produtos,
    left_on="CodigoProduto",
    right_on="ID_COD",
    how="left"
)

vendas = vendas.merge(
    tabela_precos[["ID_COD", "PRECO"]],
    left_on="CodigoProduto",
    right_on="ID_COD",
    how="left"
)

vendas.rename(columns={"PRECO": "PrecoTabela"}, inplace=True)

# ===============================
# COMISSÃO
# ===============================
def calcular_comissao(row):
    if row["PrecoUnit"] >= row["PrecoTabela"] * 1.06:
        return row["TotalLiquidoNF"] * 0.04
    return row["TotalLiquidoNF"] * 0.03

vendas["Comissao"] = vendas.apply(calcular_comissao, axis=1)

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("Gestão Comercial")

modulo = st.sidebar.radio(
    "Módulo",
    ["Relatório BI", "Pedidos e Comissões", "Inadimplência"]
)

data_ini = st.sidebar.date_input("Data Inicial", vendas["DataEmissao"].min())
data_fim = st.sidebar.date_input("Data Final", vendas["DataEmissao"].max())

vendedor_sel = st.sidebar.selectbox(
    "Vendedor",
    ["Todos"] + sorted(vendas["Vendedor"].unique().tolist())
)

df = vendas[
    (vendas["DataEmissao"] >= pd.to_datetime(data_ini)) &
    (vendas["DataEmissao"] <= pd.to_datetime(data_fim))
]

if vendedor_sel != "Todos":
    df = df[df["Vendedor"] == vendedor_sel]

# ===============================
# RELATÓRIO BI
# ===============================
if modulo == "Relatório BI":

    st.title("Relatório Comercial")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Faturamento", f"R$ {df['TotalLiquidoNF'].sum():,.2f}")
    col2.metric("Clientes", df["CPF_CNPJ"].nunique())
    col3.metric("Ticket Médio", f"R$ {df['TotalLiquidoNF'].mean():,.2f}")

    clientes_60 = df[
        (datetime.now() - df["DataEmissao"]).dt.days <= 60
    ]["CPF_CNPJ"].nunique()

    positivacao = (clientes_60 / df["CPF_CNPJ"].nunique()) * 100 if df["CPF_CNPJ"].nunique() > 0 else 0
    col4.metric("Positivação", f"{positivacao:.1f}%")

    st.subheader("Evolução Mensal")
    df["Mes"] = df["DataEmissao"].dt.to_period("M").astype(str)
    st.line_chart(df.groupby("Mes")["TotalLiquidoNF"].sum())

    st.subheader("Ranking de Clientes")
    ranking_clientes = (
        df.groupby("RazaoSocial")["TotalLiquidoNF"]
        .sum()
        .sort_values(ascending=False)
    )
    st.dataframe(ranking_clientes)

    st.subheader("Ranking de Vendedores")
    ranking_vendedores = (
        df.groupby("Vendedor")
        .agg(Faturamento=("TotalLiquidoNF", "sum"),
             Comissao=("Comissao", "sum"))
        .sort_values("Faturamento", ascending=False)
    )
    st.dataframe(ranking_vendedores)

# ===============================
# PEDIDOS E COMISSÕES
# ===============================
elif modulo == "Pedidos e Comissões":

    st.title("Pedidos e Comissões")

    busca = st.text_input("Buscar produto")

    produtos_view = produtos.merge(
        tabela_precos,
        on="ID_COD",
        how="left"
    )

    if busca:
        produtos_view = produtos_view[
            produtos_view["ID_COD"].str.contains(busca, case=False) |
            produtos_view["Descricao"].str.contains(busca, case=False)
        ]

    st.dataframe(produtos_view)

    st.markdown(
        """
        <div style="background:#eff6ff;padding:16px;border-left:5px solid #3b82f6">
        <b>Regras de Comissão</b><br>
        3%: Preço = Tabela<br>
        4%: Preço >= Tabela + 6%
        </div>
        """,
        unsafe_allow_html=True
    )

# ===============================
# INADIMPLÊNCIA
# ===============================
else:

    st.title("Inadimplência")

    inadimplencia["Dt.Vencimento"] = pd.to_datetime(inadimplencia["Dt.Vencimento"])
    inadimplencia["DiasAtraso"] = (datetime.now() - inadimplencia["Dt.Vencimento"]).dt.days

    st.dataframe(inadimplencia)

    total_aberto = inadimplencia["Vr.Líquido"].sum()
    st.metric("Total em Aberto", f"R$ {total_aberto:,.2f}")
