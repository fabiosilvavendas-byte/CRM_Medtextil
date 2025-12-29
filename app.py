import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM MEDTEXTIL", layout="wide")

# --- CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados():
    try:
        # 1. Leitura dos Arquivos
        vendas = pd.read_excel("dados/CONSULTA VENDEDORES.xlsx")
        produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
        precos = pd.read_excel("dados/TABELAS_NE.xlsx")

        # 2. Tratamento de Datas
        vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        vendas = vendas.dropna(subset=['DataEmissao'])
        
        # 3. Padronização de Colunas (Evita o erro 'ID_COD')
        for df in [produtos, precos]:
            df.columns = df.columns.str.strip() # Remove espaços invisíveis
            # Se não achar ID_COD, tenta renomear variações
            if 'ID_COD' not in df.columns:
                if 'CODIGO' in df.columns: df.rename(columns={'CODIGO': 'ID_COD'}, inplace=True)
                elif 'Código' in df.columns: df.rename(columns={'Código': 'ID_COD'}, inplace=True)

        # 4. Formatação dos IDs para texto
        if 'ID_COD' in produtos.columns:
            produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).strip()
        if 'ID_COD' in precos.columns:
            precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).strip()
            
        return vendas, produtos, precos

    except Exception as e:
        st.error(f"Erro detalhado: {e}")
        return None, None, None

# Chamada da função (Onde estava o erro de sintaxe)
vendas, produtos, precos = carregar_dados()

# --- CONTINUAÇÃO DO APP ---
if vendas is not None:
    menu = st.sidebar.selectbox("Menu Principal", ["📊 Dashboard", "📝 Gerar Pedido", "📦 Catálogo"])

    if menu == "📊 Dashboard":
        st.title("📊 Performance MEDTEXTIL")
        anos = sorted(vendas['DataEmissao'].dt.year.unique(), reverse=True)
        ano_sel = st.selectbox("Ano", anos)
        df_f = vendas[vendas['DataEmissao'].dt.year == ano_sel]
        
        c1, c2 = st.columns(2)
        c1.metric("Venda Total", f"R$ {df_f['ValorTotal'].sum():,.2f}")
        c2.metric("Pedidos", len(df_f))
        st.bar_chart(df_f.groupby('Vendedor')['ValorTotal'].sum())

    elif menu == "📝 Gerar Pedido":
        st.title("📝 Novo Pedido")
        # Interface de pedido...
        st.write("Selecione os itens abaixo conforme sua tabela de preços.")
        if 'carrinho' not in st.session_state: st.session_state.carrinho = []
        
        busca = st.text_input("Buscar Produto")
        sugestao = precos[precos['NOME_PRODUTO'].str.contains(busca, case=False, na=False)]
        
        if not sugestao.empty:
            prod = st.selectbox("Item", sugestao['NOME_PRODUTO'].tolist())
            if st.button("Adicionar"):
                st.session_state.carrinho.append({"PRODUTO": prod})
                st.success("Adicionado!")

    elif menu == "📦 Catálogo":
        st.title("📦 Tabela de Preços")
        st.dataframe(precos)
else:
    st.warning("Verifique se os arquivos Excel estão na pasta 'dados' no GitHub.")
