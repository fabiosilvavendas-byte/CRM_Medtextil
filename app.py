import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="CRM Comercial")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

PATH_VENDAS = os.path.join(DATA_DIR, "CONSULTA_VENDEDORES.xlsx")
PATH_PRODUTOS = os.path.join(DATA_DIR, "Produtos_Agrupados_Completos_conciliados.xlsx")
PATH_TABELA = os.path.join(DATA_DIR, "TABELAS_NE.xlsx")
PATH_INAD = os.path.join(DATA_DIR, "XLS_Grid_LANCAMENTO A RECEBER.xls")


# ---------------- LOAD ----------------
@st.cache_data
def carregar_dados():
    vendas = pd.read_excel(PATH_VENDAS)
    produtos = pd.read_excel(PATH_PRODUTOS)
    tabela = pd.read_excel(PATH_TABELA)
    inad = pd.read_excel(PATH_INAD)
    return vendas, produtos, tabela, inad


vendas, produtos, tabela, inad = carregar_dados()

# ---------------- TRANSFORM ----------------
df = vendas.merge(
    produtos[['ID_COD', 'Gramatura', 'Descrição']],
    left_on='CodigoProduto',
    right_on='ID_COD',
    how='left'
)

df = df.merge(
    tabela[['ID_COD', 'PRECO']],
    on='ID_COD',
    how='left'
)

df.rename(columns={
    'Descrição': 'Fios',
    'PRECO': 'Preco_Tabela'
}, inplace=True)

df['DataEmissao'] = pd.to_datetime(df['DataEmissao'])


def regra_comissao(row):
    if row['PrecoUnit'] == row['Preco_Tabela']:
        return 0.03
    elif row['PrecoUnit'] >= row['Preco_Tabela'] * 1.06:
        return 0.04
    return 0.0


df['Comissao_%'] = df.apply(regra_comissao, axis=1)
df['Valor_Comissao'] = df['TotalLiquidoNF'] * df['Comissao_%']


# ---------------- SIDEBAR ----------------
st.sidebar.title("Filtros Globais")

data_ini, data_fim = st.sidebar.date_input(
    "Período",
    [df['DataEmissao'].min(), df['DataEmissao'].max()]
)

vendedor_sel = st.sidebar.multiselect(
    "Vendedor",
    sorted(df['Vendedor'].dropna().unique())
)

df_filtro = df.copy()

df_filtro = df_filtro[
    (df_filtro['DataEmissao'] >= pd.to_datetime(data_ini)) &
    (df_filtro['DataEmissao'] <= pd.to_datetime(data_fim))
]

if vendedor_sel:
    df_filtro = df_filtro[df_filtro['Vendedor'].isin(vendedor_sel)]


# ---------------- MENU ----------------
menu = st.sidebar.radio(
    "Módulos",
    ["BI Comercial", "Pedidos & Comissão", "Inadimplência"]
)

# ======================================================
# BI COMERCIAL
# ======================================================
if menu == "BI Comercial":
    st.title("Relatório Comercial (BI)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento", f"R$ {df_filtro['TotalLiquidoNF'].sum():,.2f}")
    col2.metric("Clientes Ativos", df_filtro['RazaoSocial'].nunique())
    col3.metric("Ticket Médio", f"R$ {df_filtro['TotalLiquidoNF'].mean():,.2f}")

    st.subheader("Ranking de Clientes")
    ranking_clientes = (
        df_filtro.groupby('RazaoSocial')['TotalLiquidoNF']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.dataframe(ranking_clientes)

    st.subheader("Ranking de Vendedores")
    ranking_vend = (
        df_filtro.groupby('Vendedor')['TotalLiquidoNF']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.dataframe(ranking_vend)

    st.subheader("Clientes Inativos (+60 dias)")
    ultima = df.groupby('RazaoSocial')['DataEmissao'].max().reset_index()
    limite = df['DataEmissao'].max() - pd.Timedelta(days=60)
    st.dataframe(ultima[ultima['DataEmissao'] < limite])

    st.subheader("Evolução Mensal de Faturamento")
    mensal = (
        df_filtro
        .set_index('DataEmissao')
        .resample('M')['TotalLiquidoNF']
        .sum()
    )

    fig, ax = plt.subplots()
    mensal.plot(ax=ax)
    st.pyplot(fig)

# ======================================================
# PEDIDOS E COMISSÃO
# ======================================================
if menu == "Pedidos & Comissão":
    st.title("Pedidos e Comissão")

    termo = st.text_input("Buscar produto (Código ou Descrição)")

    if termo:
        filtro_prod = produtos[
            produtos['ID_COD'].astype(str).str.contains(termo, case=False) |
            produtos['Descrição'].str.contains(termo, case=False)
        ]
        st.dataframe(filtro_prod)

    st.subheader("Pedidos com Comissão")
    cols = [
        'Vendedor', 'RazaoSocial', 'CodigoProduto',
        'Gramatura', 'Fios',
        'PrecoUnit', 'Preco_Tabela',
        'Comissao_%', 'Valor_Comissao'
    ]
    st.dataframe(df_filtro[cols])

# ======================================================
# INADIMPLÊNCIA
# ======================================================
if menu == "Inadimplência":
    st.title("Financeiro - Inadimplência")

    inad['Dt.Vencimento'] = pd.to_datetime(inad['Dt.Vencimento'])

    vend_fin = st.multiselect(
        "Vendedor",
        sorted(inad['Funcionário'].dropna().unique())
    )

    cli_fin = st.multiselect(
        "Cliente",
        sorted(inad['Razão Social'].dropna().unique())
    )

    data_venc = st.date_input(
        "Vencimento",
        [inad['Dt.Vencimento'].min(), inad['Dt.Vencimento'].max()]
    )

    inad_f = inad.copy()

    if vend_fin:
        inad_f = inad_f[inad_f['Funcionário'].isin(vend_fin)]

    if cli_fin:
        inad_f = inad_f[inad_f['Razão Social'].isin(cli_fin)]

    inad_f = inad_f[
        (inad_f['Dt.Vencimento'] >= pd.to_datetime(data_venc[0])) &
        (inad_f['Dt.Vencimento'] <= pd.to_datetime(data_venc[1]))
    ]

    st.dataframe(
        inad_f[['Razão Social', 'Funcionário', 'Vr.Líquido', 'Dt.Vencimento', 'Nº Doc']]
    )

    st.download_button(
        "Exportar CSV",
        inad_f.to_csv(index=False).encode("utf-8"),
        "inadimplencia.csv",
        "text/csv"
    )
