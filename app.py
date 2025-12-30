import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA (Mantendo o ícone para o app no iPhone)
st.set_page_config(
    page_title="CRM Med Mais - Pro", 
    layout="wide", 
    page_icon="🛡️" # Aqui você pode trocar pelo link da sua logo se preferir
)

# ===============================
# 2. CARREGAMENTO DOS DADOS (SISTEMA ROBUSTO)
# ===============================
@st.cache_data
def carregar_dados():
    try:
        # Arquivos Originais
        vendas = pd.read_excel("dados/CONSULTA VENDEDORES.xlsx")
        
        try:
            produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx", sheet_name='CONCILIADA')
        except:
            produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
            
        try:
            precos = pd.read_excel("dados/TABELAS_NE.xlsx", sheet_name='TAB 5%')
        except:
            precos = pd.read_excel("dados/TABELAS_NE.xlsx")
            
        # NOVO ARQUIVO DE EXPANSÃO (Baseado no seu novo relatório)
        try:
            expansao = pd.read_excel("dados/CRM_Expansao_PR_2026_COMPLETO.xlsx", sheet_name=None)
        except:
            expansao = None
        
        # Padronização de Colunas (ID_COD)
        for df in [produtos, precos]:
            df.columns = df.columns.str.strip()
            if 'ID_COD' not in df.columns:
                if 'CODIGO' in df.columns: df.rename(columns={'CODIGO': 'ID_COD'}, inplace=True)
                elif 'Código' in df.columns: df.rename(columns={'Código': 'ID_COD'}, inplace=True)
                else: df.rename(columns={df.columns[0]: 'ID_COD'}, inplace=True)

        produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        vendas['RazaoSocial'] = vendas['RazaoSocial'].fillna("NÃO IDENTIFICADO").astype(str)
        vendas['Vendedor'] = vendas['Vendedor'].fillna("SEM VENDEDOR").astype(str)
        vendas['Estado'] = vendas['Estado'].fillna("S/I").astype(str)
        vendas['DataEmissao'] = pd.to_datetime(vendas['DataEmissao'], errors='coerce')
        
        return vendas, produtos, precos, expansao
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}")
        return None, None, None, None

vendas, produtos, precos, expansao = carregar_dados()

if "carrinho" not in st.session_state: st.session_state.carrinho = []
if "clientes_novos" not in st.session_state: st.session_state.clientes_novos = []

# ===============================
# 3. INTERFACE E NAVEGAÇÃO
# ===============================
st.sidebar.title("🛡️ MED MAIS CRM")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🧾 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"])

if vendas is not None:
    # ---------------------------
    # MÓDULO 1: DASHBOARD GERAL
    # ---------------------------
    if menu == "📊 Dashboard":
        st.title("📊 Dashboard de Performance")
        with st.sidebar:
            st.subheader("Filtros")
            anos = sorted(vendas['DataEmissao'].dt.year.dropna().unique().astype(int), reverse=True)
            ano_sel = st.multiselect("Anos", anos, default=anos[:1])
            vendedores = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
            vend_sel = st.selectbox("Vendedor", ["Todos"] + vendedores)
            estados = sorted([str(x) for x in vendas['Estado'].unique() if pd.notna(x)])
            est_sel = st.multiselect("Estado", estados, default=estados)

        df_f = vendas[(vendas['DataEmissao'].dt.year.isin(ano_sel)) & (vendas['Estado'].isin(est_sel))]
        if vend_sel != "Todos": df_f = df_f[df_f['Vendedor'] == vend_sel]

        c1, c2, c3 = st.columns(3)
        fat_total = df_f['PrecoQtdXItem'].sum()
        ped_total = df_f['Numero_NF'].nunique()
        c1.metric("Faturamento Total", f"R$ {fat_total:,.2f}")
        c2.metric("Total de Pedidos", ped_total)
        c3.metric("Ticket Médio", f"R$ {(fat_total/ped_total if ped_total > 0 else 0):,.2f}")

        st.subheader("🏆 Ranking de Clientes")
        rank = df_f.groupby('RazaoSocial').agg({'PrecoQtdXItem': 'sum', 'Numero_NF': 'nunique'}).reset_index()
        rank = rank.sort_values(by='PrecoQtdXItem', ascending=False).head(10)
        st.bar_chart(rank.set_index('RazaoSocial')['PrecoQtdXItem'])
        st.dataframe(rank, use_container_width=True)

    # ---------------------------
    # MÓDULO 2: PEDIDOS (SISTEMA INTEGRAL)
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
                if novo_c: st.session_state.clientes_novos.append(novo_c); st.rerun()

        c1, c2, c3 = st.columns(3)
        cond_pagto = c1.text_input("Pagamento", value="A Vista")
        tipo_frete = c2.selectbox("Frete", ["CIF", "FOB"])
        data_venda = c3.date_input("Data", datetime.now())

        st.divider()
        if st.button("➕ Adicionar Produto"):
            st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})

        df_comb = pd.merge(produtos, precos[['ID_COD', 'PRECO']], on='ID_COD', how='left')
        df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)
        df_comb['DISPLAY'] = df_comb['DESCRICAONF'].astype(str) + " | CÓD: " + df_comb['ID_COD'].astype(str)
        
        total_proposta = 0.0
        itens_final = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container():
                c_busca, c_cx, c_pr, c_qtd = st.columns([4, 1, 1, 1])
                escolha = c_busca.selectbox(f"Item {i+1}", options=sorted(df_comb['DISPLAY'].unique()), key=f"sel_{i}")
                if escolha:
                    dados_item = df_comb[df_comb['DISPLAY'] == escolha].iloc[0]
                    cx_e = c_cx.text_input("Cx", value=dados_item['CX_EMB'], key=f"x_{i}")
                    pr_u = c_pr.number_input("Unit.", value=float(dados_item['PRECO']), key=f"p_{i}")
                    qtd = c_qtd.number_input("Qtd", min_value=1, value=1, key=f"q_{i}")
                    sub = pr_u * qtd
                    total_proposta += sub
                    itens_final.append({"COD": dados_item['ID_COD'], "PRODUTO": dados_item['DESCRICAONF'], "CX": cx_e, "QTDE": qtd, "VALOR": pr_u, "TOTAL": sub})
                if st.button(f"🗑️ Remover {i+1}", key=f"btn_rem_{i}"):
                    st.session_state.carrinho.pop(i); st.rerun()
            st.divider()

        st.subheader(f"Total Final: R$ {total_proposta:,.2f}")

        if st.button("🖨️ Gerar PDF / Impressão"):
            linhas = "".join([f"<tr><td>{d['COD']}</td><td>{d['PRODUTO']}</td><td>{d['CX']}</td><td>{d['QTDE']}</td><td>R$ {d['VALOR']:.2f}</td><td>R$ {d['TOTAL']:.2f}</td></tr>" for d in itens_final])
            html = f"""<div style="font-family:Arial;border:1px solid #000;padding:20px;"><h2>MEDTEXTIL - PEDIDO</h2><p><b>Cliente:</b> {cliente_sel}</p><table border="1" style="width:100%;border-collapse:collapse;"><thead><tr><th>COD</th><th>PRODUTO</th><th>CX</th><th>QTDE</th><th>VALOR</th><th>TOTAL</th></tr></thead><tbody>{linhas}</tbody></table><h3>Total: R$ {total_proposta:,.2f}</h3><button onclick="window.print()">Imprimir</button></div>"""
            components.html(html, height=600, scrolling=True)

    # ---------------------------
    # MÓDULO 3: INATIVIDADE
    # ---------------------------
    elif menu == "🚨 Inatividade":
        st.title("🚨 Clientes Inativos")
        with st.sidebar:
            vendedores_inat = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
            v_inat = st.multiselect("Vendedores", vendedores_inat, default=vendedores_inat)
            d_limite = st.number_input("Dias Limite", min_value=1, value=60)
        
        df_i = vendas[vendas['Vendedor'].isin(v_inat)].copy()
        if not df_i.empty:
            res = df_i.groupby(['RazaoSocial', 'Vendedor', 'Estado']).agg({'DataEmissao': 'max', 'PrecoQtdXItem': 'sum'}).reset_index()
            res['Dias_Inativo'] = (datetime.now() - res['DataEmissao']).dt.days
            final = res[res['Dias_Inativo'] >= d_limite].sort_values('Dias_Inativo', ascending=False)
            st.dataframe(final, use_container_width=True)

    # ---------------------------
    # MÓDULO 4: NOVO - EXPANSÃO PR (BASEADO NO RELATÓRIO)
    # ---------------------------
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Plano de Expansão PR 2026")
        if expansao:
            tab1, tab2, tab3 = st.tabs(["🎯 Leads", "📈 Funil", "📊 KPIs"])
            with tab1: st.dataframe(expansao.get('Gestão de Leads', pd.DataFrame()), use_container_width=True)
            with tab2: st.dataframe(expansao.get('Funil de Vendas', pd.DataFrame()), use_container_width=True)
            with tab3: st.dataframe(expansao.get('Dashboard KPIs', pd.DataFrame()), use_container_width=True)
        else:
            st.warning("Arquivo de expansão não encontrado na pasta 'dados'.")
else:
    st.error("Erro no carregamento. Verifique a pasta 'dados' no GitHub.")
