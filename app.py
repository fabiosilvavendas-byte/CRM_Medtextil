import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM MEDTEXTIL", layout="wide")

# --- CARREGAMENTO DOS DADOS COM TRATAMENTO DE ERROS ---
@st.cache_data
def carregar_dados():
    try:
        # Caminhos relativos para o GitHub
        vendas = pd.read_excel("dados/CONSULTA VENDEDORES.xlsx")
        produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
        precos = pd.read_excel("dados/TABELAS_NE.xlsx")

        # CORREÇÃO DO ERRO DE DATA (O que estava travando o app)
        vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        vendas = vendas.dropna(subset=['DataEmissao'])
        
        # Limpeza de IDs para cruzamento
        produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).strip()
        precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).strip()
        
        return vendas, produtos, precos
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}. Verifique a pasta 'dados' no GitHub.")
        return None, None, None

vendas, produtos, precos = carregar_dados()

if vendas is not None:
    menu = st.sidebar.selectbox("Menu Principal", ["📊 Dashboard", "📝 Gerar Pedido", "📦 Catálogo de Produtos"])

    # --- ABA 1: DASHBOARD DE PERFORMANCE ---
    if menu == "📊 Dashboard":
        st.title("📊 Dashboard de Performance - MEDTEXTIL")
        
        anos_disponiveis = sorted(vendas['DataEmissao'].dt.year.unique(), reverse=True)
        ano_selecionado = st.selectbox("Selecione o Ano", anos_disponiveis)
        
        df_filtrado = vendas[vendas['DataEmissao'].dt.year == ano_selecionado]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Venda Total", f"R$ {df_filtrado['ValorTotal'].sum():,.2f}")
        c2.metric("Qtd Pedidos", len(df_filtrado))
        c3.metric("Ticket Médio", f"R$ {df_filtrado['ValorTotal'].mean():,.2f}")
        
        st.subheader("Vendas por Vendedor")
        st.bar_chart(df_filtrado.groupby('Vendedor')['ValorTotal'].sum())

    # --- ABA 2: GERADOR DE PEDIDO (A versão completa que você pediu) ---
    elif menu == "📝 Gerar Pedido":
        st.title("📝 Novo Pedido de Venda")
        
        with st.expander("1. Dados do Cliente", expanded=True):
            col_cli1, col_cli2 = st.columns(2)
            nome_cliente = col_cli1.text_input("Razão Social / Nome")
            cnpj_cliente = col_cli2.text_input("CNPJ / CPF")
            endereco = st.text_input("Endereço Completo")

        # Carrinho de compras
        if 'carrinho' not in st.session_state:
            st.session_state.carrinho = []

        with st.expander("2. Adicionar Itens", expanded=True):
            busca = st.text_input("Buscar Produto por Nome ou Código")
            sugestoes = precos[precos['NOME_PRODUTO'].str.contains(busca, case=False, na=False)]
            
            if not sugestoes.empty:
                prod_escolhido = st.selectbox("Selecione o item", sugestoes['NOME_PRODUTO'].tolist())
                item_info = precos[precos['NOME_PRODUTO'] == prod_escolhido].iloc[0]
                
                # Buscar informações extras na planilha de produtos (Peso e Caixa)
                extra_info = produtos[produtos['ID_COD'] == str(item_info['ID_COD'])]
                peso_un = extra_info['PESO'].values[0] if not extra_info.empty else "N/A"
                caixa_un = extra_info['CAIXA_EMBARQUE'].values[0] if not extra_info.empty else "N/A"

                col_item1, col_item2, col_item3 = st.columns(3)
                qtd = col_item1.number_input("Quantidade", min_value=1, value=1)
                preco_un = col_item2.number_input("Preço Unitário (R$)", value=float(item_info['VALOR_TABELA']))
                
                if st.button("Adicionar ao Carrinho"):
                    st.session_state.carrinho.append({
                        "COD": item_info['ID_COD'],
                        "PRODUTO": prod_escolhido,
                        "PESO": peso_un,
                        "CAIXA": caixa_un,
                        "QTDE": qtd,
                        "VALOR": preco_un,
                        "TOTAL": qtd * preco_un
                    })
                    st.success("Item adicionado!")

        if st.session_state.carrinho:
            st.subheader("Itens do Pedido")
            df_carrinho = pd.DataFrame(st.session_state.carrinho)
            st.table(df_carrinho)
            
            total_geral = df_carrinho['TOTAL'].sum()
            st.write(f"### Total do Pedido: R$ {total_geral:,.2f}")

            if st.button("Finalizar e Gerar PDF"):
                # Lógica simplificada do PDF para o exemplo
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "MEDTEXTIL - PEDIDO DE VENDA", ln=True, align='C')
                pdf.set_font("Arial", '', 10)
                pdf.cell(200, 10, f"Cliente: {nome_cliente} - CNPJ: {cnpj_cliente}", ln=True)
                pdf.cell(200, 10, "-"*50, ln=True)
                for item in st.session_state.carrinho:
                    pdf.cell(200, 8, f"{item['QTDE']}x {item['PRODUTO']} - R$ {item['TOTAL']:.2f}", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("Baixar Pedido PDF", data=pdf_output, file_name=f"Pedido_{nome_cliente}.pdf")

    # --- ABA 3: CATÁLOGO ---
    elif menu == "📦 Catálogo de Produtos":
        st.title("📦 Consulta de Estoque e Preços")
        st.dataframe(precos)

else:
    st.info("Configure os arquivos no GitHub para ativar o sistema.")
