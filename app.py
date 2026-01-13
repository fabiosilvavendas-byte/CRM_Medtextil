import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
import io

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="CRM Medtextil",
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

    tabelas_ne = pd.read_excel("dados/TABELAS_NE.xlsx")

    # padronização SEM alterar nomes
    for df in [produtos, tabelas_ne]:
        df.columns = df.columns.str.strip()
        df["ID_COD"] = df["ID_COD"].astype(str).str.replace(".0", "", regex=False)

    vendas["RazaoSocial"] = vendas["RazaoSocial"].fillna("NÃO IDENTIFICADO")
    vendas["DataEmissao"] = pd.to_datetime(vendas["DataEmissao"], errors="coerce")

    return vendas, produtos, tabelas_ne

vendas, produtos, tabelas_ne = carregar_dados()

# ===============================
# SESSION STATE
# ===============================
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

if "historico_pedidos" not in st.session_state:
    st.session_state.historico_pedidos = []

# ===============================
# MENU
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Vendas", "🧾 Pedidos", "🚨 Inatividade"]
)

# ===============================
# VENDAS
# ===============================
if menu == "📊 Vendas":
    st.title("📊 Vendas")

    c1, c2 = st.columns(2)
    c1.metric("Faturamento", f"R$ {vendas['TotalProduto2'].sum():,.2f}")
    c2.metric("Pedidos", vendas["Numero_NF"].nunique())

    st.dataframe(vendas, use_container_width=True)

# ===============================
# PEDIDOS
# ===============================
elif menu == "🧾 Pedidos":
    st.title("🧾 Pedido Comercial")

    cliente = st.text_input("Cliente")
    data_venda = datetime.now()

    if st.button("➕ Adicionar Produto"):
        st.session_state.carrinho.append({})

    # BASE COM MARCA E GRAMATURA
    df_comb = produtos.merge(
        tabelas_ne[["ID_COD", "LINHA", "GRAMAT"]],
        on="ID_COD",
        how="left"
    )

    df_comb["DISPLAY"] = (
        df_comb["ID_COD"] + " | " + df_comb["DESCRICAONF"]
    )

    total = 0
    itens = []

    for i in range(len(st.session_state.carrinho)):
        escolha = st.selectbox(
            f"Produto {i+1}",
            df_comb["DISPLAY"].unique(),
            key=f"prod_{i}"
        )

        item = df_comb[df_comb["DISPLAY"] == escolha].iloc[0]

        st.caption(
            f"Marca: {item['LINHA']} | Gramatura: {item['GRAMAT']}"
        )

        qtd = st.number_input("Qtd", 1, key=f"qtd_{i}")
        valor = st.number_input("Valor Unit.", 0.0, key=f"val_{i}")

        subtotal = qtd * valor
        total += subtotal

        itens.append({
            "Código": item["ID_COD"],
            "Produto": item["DESCRICAONF"],
            "Marca": item["LINHA"],
            "Gramatura": item["GRAMAT"],
            "Qtd": qtd,
            "Valor": valor,
            "Total": subtotal
        })

    st.subheader(f"Total: R$ {total:,.2f}")

    # ===============================
    # EXPORTAR EXCEL
    # ===============================
    if itens:
        df_excel = pd.DataFrame(itens)
        buffer = io.BytesIO()
        df_excel.to_excel(buffer, index=False)
        st.download_button(
            "📥 Exportar Pedido Excel",
            buffer.getvalue(),
            "pedido_medtextil.xlsx"
        )

    # ===============================
    # GERAR PDF
    # ===============================
    if st.button("🖨️ Gerar PDF"):
        linhas = "".join([
            f"<tr><td>{i['Código']}</td><td>{i['Produto']}</td><td>{i['Qtd']}</td><td>R$ {i['Total']:,.2f}</td></tr>"
            for i in itens
        ])

        html = f"""
        <h2>Pedido Medtextil</h2>
        <p><b>Cliente:</b> {cliente}</p>
        <p><b>Data:</b> {data_venda.strftime('%d/%m/%Y')}</p>
        <table border=1 width=100%>
        <tr><th>Código</th><th>Produto</th><th>Qtd</th><th>Total</th></tr>
        {linhas}
        </table>
        <h3>Total: R$ {total:,.2f}</h3>
        <script>window.print()</script>
        """

        components.html(html, height=600)

        st.session_state.historico_pedidos.append({
            "Cliente": cliente,
            "Data": data_venda,
            "Total": total
        })

# ===============================
# INATIVIDADE
# ===============================
elif menu == "🚨 Inatividade":
    st.title("🚨 Clientes Inativos")

    limite = st.number_input("Dias sem compra", 30)

    base = vendas.groupby("RazaoSocial")["DataEmissao"].max().reset_index()
    base["Dias"] = (datetime.now() - base["DataEmissao"]).dt.days

    st.dataframe(base[base["Dias"] > limite], use_container_width=True)

# ===============================
# HISTÓRICO
# ===============================
st.sidebar.divider()
st.sidebar.subheader("📚 Histórico de Pedidos")

if st.session_state.historico_pedidos:
    st.sidebar.dataframe(
        pd.DataFrame(st.session_state.historico_pedidos),
        use_container_width=True
    )
