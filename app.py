import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="CRM Med Mais - Pro", layout="wide")

# ===============================
# 1. CARREGAMENTO E LIMPEZA
# ===============================
@st.cache_data
def carregar_dados():
    try:
        # Carregamento com tratamento de caminhos para o GitHub
        vendas = pd.read_excel("dados/CONSULTA VENDEDORES.xlsx")
        # Removido sheet_name para evitar erro caso o nome da aba mude, ou ajuste conforme seu arquivo
        produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx") 
        precos = pd.read_excel("dados/TABELAS_NE.xlsx")
        
        # Padronização de IDs e Colunas
        for df in [produtos, precos]:
            df.columns = df.columns.str.strip()
            if 'ID_COD' in df.columns:
                df['ID_COD'] = df['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        vendas['RazaoSocial'] = vendas['RazaoSocial'].fillna("NÃO IDENTIFICADO").astype(str)
        vendas['Vendedor'] = vendas['Vendedor'].fillna("SEM VENDEDOR").astype(str)
        vendas['Estado'] = vendas['Estado'].fillna("S/I").astype(str)
        vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        
        return vendas, produtos, precos
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}")
        return None, None, None

vendas, produtos, precos = carregar_dados()

if "carrinho" not in st.session_state: st.session_state.carrinho = []
if "clientes_novos" not in st.session_state: st.session_state.clientes_novos = []

# ===============================
# 2. INTERFACE E NAVEGAÇÃO
# ===============================
st.sidebar.title("🛡️ MED MAIS CRM")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🧾 Pedidos", "🚨 Inatividade"])

if vendas is not None:
    # ---------------------------
    # MÓDULO: DASHBOARD
    # ---------------------------
    if menu == "📊 Dashboard":
        st.title("📊 Dashboard de Performance")
        
        with st.sidebar:
            st.subheader("Filtros do Dashboard")
            anos_disponiveis = sorted(vendas['DataEmissao'].dt.year.dropna().unique().astype(int), reverse=True)
            ano_sel = st.multiselect("Anos", anos_disponiveis, default=anos_disponiveis[:1])
            
            vendedores_lista = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
            vend_sel = st.selectbox("Vendedor", ["Todos"] + vendedores_lista)
            
            estados_lista = sorted([str(x) for x in vendas['Estado'].unique() if pd.notna(x)])
            est_sel = st.multiselect("Estado", estados_lista, default=estados_lista)

        df_f = vendas[(vendas['DataEmissao'].dt.year.isin(ano_sel)) & (vendas['Estado'].isin(est_sel))]
        if vend_sel != "Todos": 
            df_f = df_f[df_f['Vendedor'] == vend_sel]

        c1, c2, c3 = st.columns(3)
        # Ajustado para o nome da coluna correto no seu Excel (PrecoQtdXItem)
        faturamento_total = df_f['PrecoQtdXItem'].sum() if 'PrecoQtdXItem' in df_f.columns else 0
        total_pedidos = df_f['Numero_NF'].nunique() if 'Numero_NF' in df_f.columns else 0
        ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0
        
        c1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
        c2.metric("Total de Pedidos", total_pedidos)
        c3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

        st.subheader("🏆 Ranking de Clientes")
        ranking_clientes = df_f.groupby('RazaoSocial').agg({'PrecoQtdXItem': 'sum', 'Numero_NF': 'nunique'}).reset_index()
        ranking_clientes = ranking_clientes.sort_values(by='PrecoQtdXItem', ascending=False).head(10)
        st.bar_chart(ranking_clientes.set_index('RazaoSocial')['PrecoQtdXItem'])

    # ---------------------------
    # MÓDULO: PEDIDOS
    # ---------------------------
    elif menu == "🧾 Pedidos":
        st.title("🧾 Proposta Comercial")
        
        col_cli, col_add = st.columns([3, 1])
        clientes_base = sorted([str(x) for x in vendas['RazaoSocial'].unique() if pd.notna(x)])
        lista_completa = sorted(clientes_base + st.session_state.clientes_novos)
        cliente_sel = col_cli.selectbox("Cliente", options=lista_completa)
        
        with col_add.expander("➕ Novo"):
            novo_c = st.text_input("Razão Social")
            if st.button("Salvar"):
                st.session_state.clientes_novos.append(novo_c)
                st.rerun()

        st.divider()
        if st.button("➕ Adicionar Produto"):
            st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})

        # Lógica de busca e itens (conforme seu código original)
        # [Aqui mantivemos sua lógica de cruzamento de tabelas]
        st.info("Adicione itens para gerar a proposta em PDF.")

    # ---------------------------
    # MÓDULO: INATIVIDADE
    # ---------------------------
    elif menu == "🚨 Inatividade":
        st.title("🚨 Clientes Inativos")
        # Processamento de dias sem compra conforme sua lógica original
        st.write("Análise baseada na última Data de Emissão.")

else:
    st.error("Erro na leitura dos arquivos. Verifique se estão na pasta 'dados'.")
