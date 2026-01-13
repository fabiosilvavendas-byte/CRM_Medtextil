import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="CRM MedTextil - Pro",
    layout="wide",
    page_icon="🛡️"
)

# ===============================
# CARREGAMENTO DOS DADOS
# ===============================
@st.cache_data
def carregar_dados():
    vendas = pd.read_excel("dados/CONSULTA_VENDEDORES.xlsx")
    produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
    precos = pd.read_excel("dados/TABELAS_NE.xlsx", sheet_name="TAB 5%")
    tabelas_ne = pd.read_excel("dados/TABELAS_NE.xlsx")
    expansao = pd.read_excel("dados/CRM_Expansao_PR_2026_COMPLETO.xlsx", sheet_name=None)

    for df in [produtos, precos, tabelas_ne]:
        df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")
        if "ID_COD" not in df.columns:
            df.rename(columns={df.columns[0]: "ID_COD"}, inplace=True)
        df["ID_COD"] = df["ID_COD"].astype(str).str.replace(".0", "", regex=False)

    vendas["DataEmissao"] = pd.to_datetime(vendas["DataEmissao"], errors="coerce")
    vendas["RazaoSocial"] = vendas["RazaoSocial"].fillna("NÃO IDENTIFICADO")
    vendas["Vendedor"] = vendas["Vendedor"].fillna("SEM VENDEDOR")
    vendas["Estado"] = vendas["Estado"].fillna("S/I")

    return vendas, produtos, precos, tabelas_ne, expansao


vendas, produtos, precos, tabelas_ne, expansao = carregar_dados()

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

# ===============================
# MENU
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Vendas", "🧾 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"]
)

# ===============================
# MÓDULO 1 — VENDAS
# ===============================
if menu == "📊 Vendas":
    st.title("📊 Vendas de Performance")

    anos = vendas["DataEmissao"].dt.year.dropna().unique()
    ano_sel = st.multiselect("Ano", sorted(anos), default=max(anos))

    df_f = vendas[vendas["DataEmissao"].dt.year.isin([ano_sel])]

    fat = df_f["TotalProduto2"].sum()
    ped = df_f["Numero_NF"].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {fat:,.2f}")
    c2.metric("Pedidos", ped)
    c3.metric("Ticket Médio", f"R$ {(fat/ped if ped else 0):,.2f}")

# ===============================
# MÓDULO 2 — PEDIDOS
# ===============================
elif menu == "🧾 Pedidos":
    st.title("🧾 Proposta Comercial")

    if st.button("➕ Adicionar Produto"):
        st.session_state.carrinho.append({})

    df_comb = (
        produtos
        .merge(precos[["ID_COD", "PRECO"]], on="ID_COD", how="left")
        .merge(tabelas_ne[["ID_COD", "LINHA", "GRAMAT"]], on="ID_COD", how="left")
    ).fillna("")

    df_comb["PRECO"] = df_comb["PRECO"].astype(float).fillna(0)
    df_comb["DISPLAY"] = df_comb["ID_COD"] + " | " + df_comb["DESCRICAONF"]

    total = 0
    for i in range(len(st.session_state.carrinho)):
        escolha = st.selectbox(
            f"Produto {i+1}",
            df_comb["DISPLAY"],
            key=f"prod_{i}"
        )

        item = df_comb[df_comb["DISPLAY"] == escolha].iloc[0]

        st.caption(f"**Marca:** {item['LINHA']} | **Gramatura:** {item['GRAMAT']}")

        qtd = st.number_input("Qtd", 1, key=f"q_{i}")
        total += qtd * item["PRECO"]

    st.subheader(f"Total: R$ {total:,.2f}")

# ===============================
# MÓDULO 3 — INATIVIDADE
# ===============================
elif menu == "🚨 Inatividade":
    st.title("🚨 Clientes Inativos")

    limite = st.number_input("Dias sem compra", 30)
    base = vendas.groupby("RazaoSocial")["DataEmissao"].max().reset_index()
    base["Dias"] = (datetime.now() - base["DataEmissao"]).dt.days

    st.dataframe(base[base["Dias"] >= limite])

# ===============================
# MÓDULO 4 — EXPANSÃO PR
# ===============================
elif menu == "🚀 Expansão PR":
    st.title("🚀 Expansão PR 2026")
    st.write(expansao)
