import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRM Med Mais - Pro", layout="wide")

# ===============================
# 1. CARREGAMENTO E LIMPEZA (Garantindo que os filtros funcionem)
# ===============================
@st.cache_data
def carregar_dados():
    try:
        vendas = pd.read_excel("dados/CONSULTA VENDEDORES.xlsx")
        produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx", sheet_name='CONCILIADA')
        precos = pd.read_excel("dados/TABELAS_NE.xlsx", sheet_name='TAB 5%')
        
        # Padronização para evitar erros de busca e sorted
        produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
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

# ---------------------------
# ---------------------------
# MÓDULO: DASHBOARD (COM RANKING DE CLIENTES)
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

    # Filtragem dos dados
    df_f = vendas[(vendas['DataEmissao'].dt.year.isin(ano_sel)) & (vendas['Estado'].isin(est_sel))]
    if vend_sel != "Todos": 
        df_f = df_f[df_f['Vendedor'] == vend_sel]

    # --- KPI's Principais ---
    c1, c2, c3 = st.columns(3)
    faturamento_total = df_f['PrecoQtdXItem'].sum()
    total_pedidos = df_f['Numero_NF'].nunique()
    ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0
    
    c1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
    c2.metric("Total de Pedidos", total_pedidos)
    c3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

    st.divider()

    # --- RANKING DE CLIENTES ---
    st.subheader("🏆 Ranking de Clientes (Maiores Compradores)")
    
    # Agrupamento por Cliente
    ranking_clientes = df_f.groupby('RazaoSocial').agg({
        'PrecoQtdXItem': 'sum',
        'Numero_NF': 'nunique'
    }).reset_index()
    
    ranking_clientes.columns = ['Nome do Cliente', 'Total Comprado (R$)', 'Qtd Pedidos']
    ranking_clientes = ranking_clientes.sort_values(by='Total Comprado (R$)', ascending=False).reset_index(drop=True)
    ranking_clientes.index += 1 # Começar o ranking do 1

    col_rank1, col_rank2 = st.columns([2, 1])

    with col_rank1:
        # Gráfico dos Top 10
        top_10 = ranking_clientes.head(10)
        st.bar_chart(top_10.set_index('Nome do Cliente')['Total Comprado (R$)'])

    with col_rank2:
        # Tabela detalhada
        st.dataframe(
            ranking_clientes,
            column_config={
                "Total Comprado (R$)": st.column_config.NumberColumn("Total (R$)", format="R$ %.2f"),
                "Qtd Pedidos": st.column_config.NumberColumn("Pedidos")
            },
            use_container_width=True
        )

    # --- EVOLUÇÃO MENSAL ---
    st.subheader("📈 Evolução Mensal de Vendas")
    df_f['Mes_Ano'] = df_f['DataEmissao'].dt.strftime('%Y-%m')
    vendas_mensais = df_f.groupby('Mes_Ano')['PrecoQtdXItem'].sum()
    st.line_chart(vendas_mensais)

# ---------------------------
# MÓDULO: PEDIDOS (VÍNCULO CORRIGIDO)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (VÍNCULO TOTALMENTE REATIVO)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (CORREÇÃO DE ATUALIZAÇÃO IMEDIATA)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (PESQUISA POR DESCRIÇÃO + CÓDIGO)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (BUSCA OTIMIZADA)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (LAYOUT MEDTEXTIL FIEL AO PDF)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (LAYOUT FINAL MEDTEXTIL)
# ---------------------------
# ---------------------------
# MÓDULO: PEDIDOS (SISTEMA COMPLETO MEDTEXTIL)
# ---------------------------
elif menu == "🧾 Pedidos":
    st.title("🧾 Proposta Comercial")
    
    # --- SEÇÃO DE CLIENTE ---
    col_cli, col_add = st.columns([3, 1])
    clientes_base = sorted([str(x) for x in vendas['RazaoSocial'].unique() if pd.notna(x)])
    lista_completa = sorted(clientes_base + st.session_state.clientes_novos)
    cliente_sel = col_cli.selectbox("Informações sobre o Cliente", options=lista_completa) # 
    
    with col_add.expander("➕ Novo Cliente"):
        novo_c = st.text_input("Razão Social")
        if st.button("Salvar Cliente"):
            if novo_c:
                st.session_state.clientes_novos.append(novo_c)
                st.rerun()

    # --- DETALHES DA VENDA ---
    c1, c2, c3 = st.columns(3)
    cond_pagto = c1.text_input("Condições de Pagto", value="A Vista") # [cite: 7]
    tipo_frete = c2.selectbox("Tipo de Frete", ["CIF", "FOB"], index=0) # [cite: 20, 21]
    data_venda = c3.date_input("Data da Venda", datetime.now()) # [cite: 8]

    st.divider()
    
    if st.button("➕ Adicionar Produto"):
        st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})

    # Preparação da base de dados para a busca
    df_comb = pd.merge(produtos, precos[['ID_COD', 'PRECO']], on='ID_COD', how='left')
    df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)
    df_comb['DISPLAY'] = df_comb['DESCRICAONF'].astype(str) + " | CÓD: " + df_comb['ID_COD'].astype(str)
    lista_opcoes = sorted(df_comb['DISPLAY'].unique())

    total_proposta = 0.0
    itens_final = []

    # --- LISTAGEM DINÂMICA DE ITENS ---
    for i, item in enumerate(st.session_state.carrinho):
        with st.container():
            c_busca, c_cx, c_pr, c_qtd = st.columns([4, 1, 1, 1])
            escolha = c_busca.selectbox(f"Pesquisar Item {i+1}", options=lista_opcoes, key=f"sel_{i}")
            
            if escolha:
                dados_item = df_comb[df_comb['DISPLAY'] == escolha].iloc[0]
                
                # Campos automáticos e editáveis
                cx_e = c_cx.text_input("Cx Emb", value=dados_item['CX_EMB'], key=f"x_{i}") # 
                pr_u = c_pr.number_input("Valor Unit.", value=float(dados_item['PRECO']), key=f"p_{i}", format="%.2f") # 
                qtd = c_qtd.number_input("Qtde", min_value=1, value=1, key=f"q_{i}") # [cite: 10, 12]
                
                sub = pr_u * qtd
                total_proposta += sub
                
                itens_final.append({
                    "COD": dados_item['ID_COD'], 
                    "PRODUTO": dados_item['DESCRICAONF'],
                    "PESO": "-", 
                    "CX": cx_e, 
                    "QTDE": qtd, 
                    "VALOR": pr_u, 
                    "TOTAL": sub
                })
            
            if st.button(f"🗑️ Remover Item {i+1}", key=f"btn_rem_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()
            st.divider()

    st.subheader(f"Total Final: R$ {total_proposta:,.2f}") # [cite: 12]

    # --- GERADOR DE IMPRESSÃO A4 (FORMATO MEDTEXTIL) ---
    if st.button("🖨️ Gerar Pedido para Impressão"):
        # Importação do componente de renderização
        import streamlit.components.v1 as components
        
        # Construção das linhas da tabela de produtos 
        linhas_html = "".join([
            f"""<tr>
                <td>{d['COD']}</td>
                <td>{d['PRODUTO']}</td>
                <td>{d['PESO']}</td>
                <td>{d['CX']}</td>
                <td style="text-align:center">{d['QTDE']}</td>
                <td style="text-align:right">R$ {d['VALOR']:.2f}</td>
                <td style="text-align:right">R$ {d['TOTAL']:.2f}</td>
            </tr>""" for d in itens_final
        ])

        # Estrutura HTML completa baseada no seu PDF
        html_final = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 10px; }}
                .invoice-box {{ padding: 20px; border: 1px solid #000; width: 185mm; margin: auto; background: #fff; }}
                .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px; }}
                .section-title {{ background: #eee; padding: 5px; font-weight: bold; border: 1px solid #000; margin-top: 15px; font-size: 12px; }}
                .data-box {{ border: 1px solid #000; border-top: none; padding: 10px; font-size: 11px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 5px; font-size: 10px; }}
                th, td {{ border: 1px solid #000; padding: 6px; text-align: left; }}
                th {{ background: #f2f2f2; }}
                .footer-summary {{ margin-top: 20px; }}
                .no-print {{ text-align: center; margin-bottom: 20px; }}
                .btn-print {{ background: #1a5276; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
                @media print {{ .no-print {{ display: none; }} }}
            </style>
        </head>
        <body>
            <div class="no-print">
                <button class="btn-print" onclick="window.print()">🖨️ ABRIR JANELA DE IMPRESSÃO (PDF)</button>
            </div>
            
            <div class="invoice-box">
                <div class="header">
                    <div>
                        <h2 style="margin:0;">MEDTEXTIL</h2>
                        <p style="margin:0;">PRODUTOS TEXTIL HOSPITALARES</p>
                        <p style="margin:0;">CNPJ: 40.357.820/0001-50 | IE: 16.390.286-0</p>
                    </div>
                    <div style="text-align: right;">
                        <b>PEDIDO Nº: {datetime.now().strftime('%H%M%S')}</b><br>
                        Data da Venda: {data_venda.strftime('%d/%m/%Y')}
                    </div>
                </div>

                <div class="section-title">Informações sobre o Cliente</div>
                <div class="data-box">
                    <b>Cliente:</b> {cliente_sel}<br>
                    <b>Condições de Pagto:</b> {cond_pagto} | <b>Frete:</b> {tipo_frete}
                </div>

                <div class="section-title">Detalhe do Pedido</div>
                <table>
                    <thead>
                        <tr>
                            <th>COD.</th><th>PRODUTO</th><th>PESO</th><th>CAIXA DE EMBARQUE</th><th>QTDE</th><th>VALOR</th><th>TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>

                <div class="footer-summary">
                    <table>
                        <tr>
                            <td style="width: 60%;"><b>Observação:</b> Sujeito a disponibilidade de estoque.</td>
                            <td style="text-align: right;">
                                <b>Qtde Itens:</b> {len(itens_final)}<br>
                                <b>Tipo de Frete:</b> {tipo_frete}<br>
                                <h3 style="margin:0;">Total Final: R$ {total_proposta:,.2f}</h3>
                            </td>
                        </tr>
                    </table>
                </div>

                <div style="margin-top: 30px; text-align: center; font-size: 10px; font-weight: bold; border-top: 1px dotted #000; padding-top: 10px;">
                    MEDTEXTIL PRODUTOS TEXTIL HOSPITALAR
                </div>
            </div>
        </body>
        </html>
        """
        # Renderização do quadro de impressão
        components.html(html_final, height=1100, scrolling=True)
        # ---------------------------
# MÓDULO: INATIVIDADE (CORRIGIDO)
# ---------------------------
elif menu == "🚨 Inatividade":
    st.title("🚨 Clientes Inativos")
    
    # 1. Filtros Laterais
    with st.sidebar:
        st.subheader("Configurações de Alerta")
        # Lista vendedores únicos garantindo que não haja erro de tipo
        vendedores_inat = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
        v_inat = st.multiselect("Filtrar Vendedores", vendedores_inat, default=vendedores_inat)
        d_limite = st.number_input("Dias sem compra (Limite)", min_value=1, value=60)

    # 2. Processamento dos Dados
    hoje = datetime.now()
    
    # Filtra as vendas pelos vendedores selecionados
    df_i = vendas[vendas['Vendedor'].isin(v_inat)].copy()
    
    if not df_i.empty:
        # Agrupa para achar a última data de compra por cliente
        # Usamos as colunas extraídas do seu arquivo de vendas [cite: 6]
        res = df_i.groupby(['RazaoSocial', 'Vendedor', 'Estado']).agg({
            'DataEmissao': 'max', 
            'PrecoQtdXItem': 'sum'
        }).reset_index()
        
        # Remove linhas onde a data é inválida
        res = res.dropna(subset=['DataEmissao'])
        
        # Calcula os dias de inatividade
        res['Dias_Inativo'] = (hoje - res['DataEmissao']).dt.days
        
        # Filtra apenas quem ultrapassou o limite de dias
        final = res[res['Dias_Inativo'] >= d_limite].sort_values('Dias_Inativo', ascending=False)
        
        if not final.empty:
            # Métricas de Resumo
            c1, c2 = st.columns(2)
            c1.metric("Clientes Inativos", len(final))
            c2.metric("Faturamento em Risco", f"R$ {final['PrecoQtdXItem'].sum():,.2f}")
            
            # Exibição da Tabela
            st.dataframe(
                final[['RazaoSocial', 'Vendedor', 'Estado', 'DataEmissao', 'Dias_Inativo', 'PrecoQtdXItem']],
                column_config={
                    "DataEmissao": st.column_config.DateColumn("Última Compra"),
                    "PrecoQtdXItem": st.column_config.NumberColumn("Valor Histórico", format="R$ %.2f"),
                    "Dias_Inativo": st.column_config.NumberColumn("Dias Parado", format="%d ⚠️")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"✅ Nenhum cliente está inativo há mais de {d_limite} dias para os vendedores selecionados.")
    else:
        st.warning("⚠️ Não foram encontrados dados de vendas para os vendedores selecionados.")