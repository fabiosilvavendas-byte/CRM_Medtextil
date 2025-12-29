import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

@st.cache_data
def carregar_dados():
    try:
        # Tenta ler os arquivos pegando sempre a PRIMEIRA ABA (evita erro de nome de aba)
        vendas = pd.read_excel("dados/CONSULTA VENDEDORES.xlsx")
        produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
        precos = pd.read_excel("dados/TABELAS_NE.xlsx")
        
        # PADRONIZAÇÃO AUTOMÁTICA DE COLUNAS
        for df in [produtos, precos]:
            df.columns = df.columns.str.strip() # Remove espaços
            # Se não achar 'ID_COD', procura por 'CODIGO' ou 'CÓDIGO' e renomeia
            colunas_possiveis = ['ID_COD', 'CODIGO', 'Código', 'id_cod', 'COD']
            for col in colunas_possiveis:
                if col in df.columns:
                    df.rename(columns={col: 'ID_COD'}, inplace=True)
                    break
        
        # Limpeza de códigos para texto (Garante o vínculo dos Pedidos)
        produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        vendas['RazaoSocial'] = vendas['RazaoSocial'].fillna("NÃO IDENTIFICADO").astype(str)
        vendas['Vendedor'] = vendas['Vendedor'].fillna("SEM VENDEDOR").astype(str)
        vendas['Estado'] = vendas['Estado'].fillna("S/I").astype(str)
        vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        
        return vendas, produtos, precos
    except Exception as e:
        st.error(f"Erro detalhado: {e}")
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

        # Filtragem
        df_f = vendas[(vendas['DataEmissao'].dt.year.isin(ano_sel)) & (vendas['Estado'].isin(est_sel))]
        if vend_sel != "Todos": 
            df_f = df_f[df_f['Vendedor'] == vend_sel]

        # KPI's
        c1, c2, c3 = st.columns(3)
        faturamento_total = df_f['PrecoQtdXItem'].sum()
        total_pedidos = df_f['Numero_NF'].nunique()
        ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0
        
        c1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
        c2.metric("Total de Pedidos", total_pedidos)
        c3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

        st.divider()

        # Ranking de Clientes
        st.subheader("🏆 Ranking de Clientes")
        ranking_clientes = df_f.groupby('RazaoSocial').agg({
            'PrecoQtdXItem': 'sum',
            'Numero_NF': 'nunique'
        }).reset_index()
        ranking_clientes.columns = ['Nome do Cliente', 'Total Comprado (R$)', 'Qtd Pedidos']
        ranking_clientes = ranking_clientes.sort_values(by='Total Comprado (R$)', ascending=False).reset_index(drop=True)
        ranking_clientes.index += 1

        col_rank1, col_rank2 = st.columns([2, 1])
        with col_rank1:
            st.bar_chart(ranking_clientes.head(10).set_index('Nome do Cliente')['Total Comprado (R$)'])
        with col_rank2:
            st.dataframe(ranking_clientes, use_container_width=True)

    # ---------------------------
    # MÓDULO: PEDIDOS
    # ---------------------------
    elif menu == "🧾 Pedidos":
        st.title("🧾 Proposta Comercial")
        
        col_cli, col_add = st.columns([3, 1])
        clientes_base = sorted([str(x) for x in vendas['RazaoSocial'].unique() if pd.notna(x)])
        lista_completa = sorted(clientes_base + st.session_state.clientes_novos)
        cliente_sel = col_cli.selectbox("Informações sobre o Cliente", options=lista_completa)
        
        with col_add.expander("➕ Novo Cliente"):
            novo_c = st.text_input("Razão Social")
            if st.button("Salvar Cliente"):
                if novo_c:
                    st.session_state.clientes_novos.append(novo_c)
                    st.rerun()

        c1, c2, c3 = st.columns(3)
        cond_pagto = c1.text_input("Condições de Pagto", value="A Vista")
        tipo_frete = c2.selectbox("Tipo de Frete", ["CIF", "FOB"], index=0)
        data_venda = c3.date_input("Data da Venda", datetime.now())

        st.divider()
        
        if st.button("➕ Adicionar Produto"):
            st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})

        # União das tabelas para busca (Cruzando Produtos com Preços pelo ID_COD)
        df_comb = pd.merge(produtos, precos[['ID_COD', 'PRECO']], on='ID_COD', how='left')
        df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)
        df_comb['DISPLAY'] = df_comb['DESCRICAONF'].astype(str) + " | CÓD: " + df_comb['ID_COD'].astype(str)
        lista_opcoes = sorted(df_comb['DISPLAY'].unique())

        total_proposta = 0.0
        itens_final = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container():
                c_busca, c_cx, c_pr, c_qtd = st.columns([4, 1, 1, 1])
                escolha = c_busca.selectbox(f"Pesquisar Item {i+1}", options=lista_opcoes, key=f"sel_{i}")
                
                if escolha:
                    dados_item = df_comb[df_comb['DISPLAY'] == escolha].iloc[0]
                    cx_e = c_cx.text_input("Cx Emb", value=dados_item['CX_EMB'], key=f"x_{i}")
                    pr_u = c_pr.number_input("Valor Unit.", value=float(dados_item['PRECO']), key=f"p_{i}")
                    qtd = c_qtd.number_input("Qtde", min_value=1, value=1, key=f"q_{i}")
                    
                    sub = pr_u * qtd
                    total_proposta += sub
                    itens_final.append({
                        "COD": dados_item['ID_COD'], 
                        "PRODUTO": dados_item['DESCRICAONF'],
                        "PESO": "-", "CX": cx_e, "QTDE": qtd, "VALOR": pr_u, "TOTAL": sub
                    })
                
                if st.button(f"🗑️ Remover {i+1}", key=f"btn_rem_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()
            st.divider()

        st.subheader(f"Total Final: R$ {total_proposta:,.2f}")

        if st.button("🖨️ Gerar Pedido para Impressão"):
            linhas_html = "".join([
                f"<tr><td>{d['COD']}</td><td>{d['PRODUTO']}</td><td>{d['PESO']}</td><td>{d['CX']}</td>"
                f"<td>{d['QTDE']}</td><td>R$ {d['VALOR']:.2f}</td><td>R$ {d['TOTAL']:.2f}</td></tr>" 
                for d in itens_final
            ])
            
            html_final = f"""
            <div style="font-family: Arial; border: 1px solid black; padding: 20px;">
                <h2>MEDTEXTIL - PEDIDO DE VENDA</h2>
                <p><b>Cliente:</b> {cliente_sel} | <b>Data:</b> {data_venda}</p>
                <table border="1" style="width:100%; border-collapse: collapse;">
                    <thead><tr><th>COD</th><th>PRODUTO</th><th>PESO</th><th>CX</th><th>QTDE</th><th>VALOR</th><th>TOTAL</th></tr></thead>
                    <tbody>{linhas_html}</tbody>
                </table>
                <h3>Total Geral: R$ {total_proposta:,.2f}</h3>
                <button onclick="window.print()">Imprimir PDF</button>
            </div>
            """
            components.html(html_final, height=600, scrolling=True)

    # ---------------------------
    # MÓDULO: INATIVIDADE
    # ---------------------------
    elif menu == "🚨 Inatividade":
        st.title("🚨 Clientes Inativos")
        hoje = datetime.now()
        vendedores_inat = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
        v_inat = st.multiselect("Filtrar Vendedores", vendedores_inat, default=vendedores_inat)
        d_limite = st.number_input("Dias sem compra (Limite)", min_value=1, value=60)

        df_i = vendas[vendas['Vendedor'].isin(v_inat)].copy()
        if not df_i.empty:
            res = df_i.groupby(['RazaoSocial', 'Vendedor', 'Estado']).agg({'DataEmissao': 'max', 'PrecoQtdXItem': 'sum'}).reset_index()
            res['Dias_Inativo'] = (hoje - res['DataEmissao']).dt.days
            final = res[res['Dias_Inativo'] >= d_limite].sort_values('Dias_Inativo', ascending=False)
            st.dataframe(final, use_container_width=True)
else:
    st.error("Arquivos não encontrados.")

