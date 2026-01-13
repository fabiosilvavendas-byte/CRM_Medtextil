import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="CRM MedTextil - Pro",
    layout="wide",
    page_icon="🛡️"
)

# ===============================
# 2. CARREGAMENTO DOS DADOS
# ===============================
@st.cache_data
def carregar_dados():
    Dashboard = pd.read_excel("dados/CONSULTA_VENDEDORES.xlsx")

    try:
        produtos = pd.read_excel(
            "dados/Produtos_Agrupados_Completos_conciliados.xlsx",
            sheet_name="CONCILIADA"
        )
    except:
        produtos = pd.read_excel(
            "dados/Produtos_Agrupados_Completos_conciliados.xlsx"
        )

    precos = pd.read_excel("dados/TABELAS_NE.xlsx")

    expansao = None
    try:
        expansao = pd.read_excel(
            "dados/CRM_Expansao_PR_2026_COMPLETO.xlsx",
            sheet_name=None
        )
    except:
        pass

    for df in [produtos, precos]:
        df.columns = df.columns.str.strip()

    produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False)
    precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False)

    Dashboard['RazaoSocial'] = Dashboard['RazaoSocial'].fillna("NÃO IDENTIFICADO")
    Dashboard['Vendedor'] = Dashboard['Vendedor'].fillna("SEM VENDEDOR")
    Dashboard['Estado'] = Dashboard['Estado'].fillna("S/I")
    Dashboard['DataEmissao'] = pd.to_datetime(Dashboard['DataEmissao'], errors="coerce")

    return Dashboard, produtos, precos, expansao


Dashboard, produtos, precos, expansao = carregar_dados()
vendas = Dashboard

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

if "clientes_novos" not in st.session_state:
    st.session_state.clientes_novos = []

# ===============================
# BASE GLOBAL PARA PEDIDOS
# ===============================
df_comb_global = produtos.merge(
    precos[['ID_COD', 'PRECO', 'GRAMAT']],
    on='ID_COD',
    how='left'
)

# ===============================
# 3. INTERFACE
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard", "🛒 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"]
)

# ---------------------------
# MÓDULO 1: DASHBOARD (INALTERADO)
# ---------------------------
if menu == "📊 Dashboard":
    st.title("📊 Dashboard de Performance")

# ---------------------------
# MÓDULO 2: PEDIDOS (🔧 AJUSTADO)
# ---------------------------
elif menu == "🛒 Pedidos":
    st.title("🛒 Pedidos")

    # ===== MAPA DE PRODUTOS (lookup por código)
    mapa_produtos = df_comb_global.set_index("ID_COD").to_dict("index")
    lista_codigos = sorted(mapa_produtos.keys())

    # ===== CLIENTE
    with st.container(border=True):
        st.subheader("👤 Cliente")
        sel_cli = st.selectbox(
            "Buscar Cliente",
            [""] + sorted(Dashboard['RazaoSocial'].unique())
        )

    # ===== ADICIONAR ITEM
    if st.button("➕ Adicionar Item"):
        st.session_state.carrinho.append({
            "ID_COD": lista_codigos[0],
            "QTD": 1
        })
        st.rerun()

    total_pedido = 0

    # ===== ITENS DO PEDIDO
    for i, item in enumerate(st.session_state.carrinho):
        dados = mapa_produtos[item["ID_COD"]]

        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([1, 3, 1, 1, 1, 1])

            cod = c1.selectbox(
                "Código",
                lista_codigos,
                index=lista_codigos.index(item["ID_COD"]),
                key=f"cod_{i}"
            )
            item["ID_COD"] = cod
            dados = mapa_produtos[cod]

            c2.text_input("Descrição", dados["DESCRICAONF"], disabled=True)
            c3.text_input("CX", dados.get("CX_EMB", ""), disabled=True)
            c4.text_input("Preço", f"{dados['PRECO']:.2f}", disabled=True)

            qtd = c5.number_input(
                "Qtd",
                min_value=1,
                value=item["QTD"],
                key=f"qtd_{i}"
            )
            item["QTD"] = qtd

            subtotal = dados["PRECO"] * qtd
            total_pedido += subtotal
            c6.metric("Subtotal", f"R$ {subtotal:,.2f}")

            if st.button("🗑️ Remover", key=f"rem_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()

    # ===== CONSOLIDAÇÃO FINAL
    if total_pedido > 0:
        df_pedido = pd.DataFrame(st.session_state.carrinho)

        pedido_final = (
            df_pedido
            .groupby("ID_COD", as_index=False)
            .agg({"QTD": "sum"})
            .merge(df_comb_global, on="ID_COD", how="left")
        )

        pedido_final["VALOR_TOTAL"] = pedido_final["QTD"] * pedido_final["PRECO"]

        st.divider()
        st.subheader("📦 Pedido Consolidado")

        st.dataframe(
            pedido_final[
                ["ID_COD", "DESCRICAONF", "QTD", "PRECO", "VALOR_TOTAL"]
            ],
            use_container_width=True
        )

        st.metric(
            "💰 Total do Pedido",
            f"R$ {pedido_final['VALOR_TOTAL'].sum():,.2f}"
        )

# ---------------------------
# MÓDULO 3: INATIVIDADE (INALTERADO)
# ---------------------------
elif menu == "🚨 Inatividade":
    st.title("🚨 Inatividade")
    with st.sidebar:
        vendedores_inat = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
        v_inat = st.multiselect("Vendedores", vendedores_inat, default=vendedores_inat)
        d_limite = st.number_input("Dias Limite", min_value=1, value=60)

    df_i = vendas[vendas['Vendedor'].isin(v_inat)].copy()
    if not df_i.empty:
        res = df_i.groupby(
            ['RazaoSocial', 'Vendedor', 'Estado']
        ).agg(
            {'DataEmissao': 'max', 'TotalProduto2': 'sum'}
        ).reset_index()

        res['Dias_Inativo'] = (datetime.now() - res['DataEmissao']).dt.days
        final = res[res['Dias_Inativo'] >= d_limite]
        st.dataframe(final, use_container_width=True)

# ---------------------------
# MÓDULO 4: EXPANSÃO (INALTERADO)
# ---------------------------
elif menu == "🚀 Expansão PR":
    st.title("🚀 Plano de Expansão PR 2026")


