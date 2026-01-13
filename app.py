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

    produtos = pd.read_excel(
        "dados/Produtos_Agrupados_Completos_conciliados.xlsx",
        sheet_name="CONCILIADA"
    )

    # <<< AJUSTE: carregamento único da TABELAS_NE (sem TAB 5%)
    tabelas_ne = pd.read_excel("dados/TABELAS_NE.xlsx")

    for df in [produtos, tabelas_ne]:
        df.columns = df.columns.str.strip()
        df["ID_COD"] = (
            df["ID_COD"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

    vendas["RazaoSocial"] = vendas["RazaoSocial"].fillna("NÃO IDENTIFICADO")
    vendas["Vendedor"] = vendas["Vendedor"].fillna("SEM VENDEDOR")
    vendas["Estado"] = vendas["Estado"].fillna("S/I")
    vendas["DataEmissao"] = pd.to_datetime(vendas["DataEmissao"], errors="coerce")

    return vendas, produtos, tabelas_ne

vendas, produtos, tabelas_ne = carregar_dados()

# ===============================
# SESSION STATE
# ===============================
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

if "clientes_novos" not in st.session_state:
    st.session_state.clientes_novos = []

if "historico_pedidos" not in st.session_state:
    st.session_state.historico_pedidos = []

# ===============================
# MENU
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Vendas", "🧾 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"]
)

# ===============================
# MÓDULO VENDAS
# ===============================
if menu == "📊 Vendas":
    st.title("📊 Vendas de Performance")

    anos = sorted(vendas["DataEmissao"].dt.year.dropna().unique(), reverse=True)
    ano_sel = st.multiselect("Ano", anos, default=anos[:1])

    df_f = vendas[vendas["DataEmissao"].dt.year.isin(ano_sel)]

    c1, c2, c3 = st.columns(3)
    fat = df_f["TotalProduto2"].sum()
    ped = df_f["Numero_NF"].nunique()

    c1.metric("Faturamento", f"R$ {fat:,.2f}")
    c2.metric("Pedidos", ped)
    c3.metric("Ticket Médio", f"R$ {(fat/ped if ped else 0):,.2f}")

    st.dataframe(df_f, use_container_width=True)

# ===============================
# MÓDULO PEDIDOS
# ===============================
elif menu == "🧾 Pedidos":
    st.title("🧾 Proposta Comercial Medtextil")

    # BASE COM MARCA E GRAMATURA
    df_comb = produtos.merge(
        tabelas_ne[["ID_COD", "LINHA", "GRAMAT"]],
        on="ID_COD",
        how="left"
    )

    df_comb["DISPLAY"] = (
        df_comb["ID_COD"] + " | " + df_comb["DESCRICAONF"]
    )

    if st.button("➕ Adicionar Produto"):
        st.session_state.carrinho.append({})

    total = 0
    itens_final = []

    for i in range(len(st.session_state.carrinho)):
        escolha = st.selectbox(
            f"Item {i+1}",
            df_comb["DISPLAY"].unique(),
            key=f"item_{i}"
        )

        dados = df_comb[df_comb["DISPLAY"] == escolha].iloc[0]

        st.caption(
            f"Marca: {dados['LINHA']} | Gramatura: {dados['GRAMAT']}"
        )

        qtd = st.number_input("Qtd", 1, key=f"q_{i}")
        valor = st.number_input("Valor Unit.", 0.0, key=f"v_{i}")

        sub = qtd * valor
        total += sub

        itens_final.append({
            "COD": dados["ID_COD"],
            "PRODUTO": dados["DESCRICAONF"],
            "MARCA": dados["LINHA"],
            "GRAMATURA": dados["GRAMAT"],
            "QTD": qtd,
            "VALOR": valor,
            "TOTAL": sub
        })

    st.subheader(f"Total: R$ {total:,.2f}")

# ===============================
# MÓDULO INATIVIDADE
# ===============================
elif menu == "🚨 Inatividade":
    st.title("🚨 Clientes Inativos")

    dias = st.number_input("Dias sem compra", 60)

    base = vendas.groupby("RazaoSocial")["DataEmissao"].max().reset_index()
    base["Dias"] = (datetime.now() - base["DataEmissao"]).dt.days

    st.dataframe(base[base["Dias"] >= dias], use_container_width=True)

# ===============================
# MÓDULO EXPANSÃO
# ===============================
elif menu == "🚀 Expansão PR":
    st.title("🚀 Expansão PR 2026")
    st.info("Módulo preservado conforme versão original")
