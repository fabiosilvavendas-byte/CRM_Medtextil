import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA (Mantido conforme original)
st.set_page_config(
    page_title="CRM MedTextil - Pro", 
    layout="wide", 
    page_icon="🛡️"
)

# ===============================
# 2. CARREGAMENTO DOS DADOS (INTACTO COMO ANTES)
# ===============================
@st.cache_data
def carregar_dados():
    try:
        Dashboard = pd.read_excel("dados/CONSULTA_VENDEDORES.xlsx")
        
        try:
            produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx", sheet_name='CONCILIADA')
        except:
            produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
            
        try:
            precos = pd.read_excel("dados/TABELAS_NE.xlsx", sheet_name='TAB 5%')
        except:
            precos = pd.read_excel("dados/TABELAS_NE.xlsx")
            
        try:
            expansao = pd.read_excel("dados/CRM_Expansao_PR_2026_COMPLETO.xlsx", sheet_name=None)
        except:
            expansao = None
        
        for df in [produtos, precos]:
            df.columns = df.columns.str.strip()
            if 'ID_COD' not in df.columns:
                if 'CODIGO' in df.columns: df.rename(columns={'CODIGO': 'ID_COD'}, inplace=True)
                elif 'Código' in df.columns: df.rename(columns={'Código': 'ID_COD'}, inplace=True)
                else: df.rename(columns={df.columns[0]: 'ID_COD'}, inplace=True)

        produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        Dashboard['RazaoSocial'] = Dashboard['RazaoSocial'].fillna("NÃO IDENTIFICADO").astype(str)
        Dashboard['Vendedor'] = Dashboard['Vendedor'].fillna("SEM VENDEDOR").astype(str)
        Dashboard['Estado'] = Dashboard['Estado'].fillna("S/I").astype(str)
        Dashboard['DataEmissao'] = pd.to_datetime(Dashboard['DataEmissao'], errors='coerce')
        
        return Dashboard, produtos, precos, expansao
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}")
        return None, None, None, None

Dashboard, produtos, precos, expansao = carregar_dados()
vendas = Dashboard
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# ===============================
# 3. INTERFACE E NAVEGAÇÃO
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🛒 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"])

if Dashboard is not None:
    # ---------------------------
    # MÓDULO 1: Dashboard GERAL (CONSOLIDADO E INTACTO)
    # ---------------------------
    if menu == "📊 Dashboard":
        st.title("📊 Dashboard de Performance")
        with st.sidebar:
            st.subheader("Filtros")
            anos = sorted(Dashboard['DataEmissao'].dt.year.dropna().unique().astype(int), reverse=True)
            ano_sel = st.multiselect("Anos", anos, default=anos[:1])
            vendedores = sorted([str(x) for x in Dashboard['Vendedor'].unique() if pd.notna(x)])
            vend_sel = st.selectbox("Vendedor", ["Todos"] + vendedores)
            estados = sorted([str(x) for x in Dashboard['Estado'].unique() if pd.notna(x)])
            est_sel = st.multiselect("Estado", estados, default=estados)

        df_f = Dashboard[(Dashboard['DataEmissao'].dt.year.isin(ano_sel)) & (Dashboard['Estado'].isin(est_sel))]
        if vend_sel != "Todos": df_f = df_f[df_f['Vendedor'] == vend_sel]

        c1, c2, c3 = st.columns(3)
        fat_total = df_f['TotalProduto2'].sum()
        ped_total = df_f['Numero_NF'].nunique()
        c1.metric("Faturamento Total", f"R$ {fat_total:,.2f}")
        c2.metric("Total de Pedidos", ped_total)
        c3.metric("Ticket Médio", f"R$ {(fat_total/ped_total if ped_total > 0 else 0):,.2f}")

        st.subheader("🏆 Ranking de Clientes")
        rank = df_f.groupby('RazaoSocial').agg({'TotalProduto2': 'sum', 'Numero_NF': 'nunique'}).reset_index()
        rank = rank.sort_values(by='TotalProduto2', ascending=False).head(10)
        st.bar_chart(rank.set_index('RazaoSocial')['TotalProduto2'])
        st.dataframe(rank, use_container_width=True)

    # ---------------------------
    # MÓDULO 2: PEDIDOS (ALTERADO CONFORME SOLICITADO)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Emissão de Proposta Comercial")

        # 1. Informações do Cliente
        with st.container(border=True):
            st.subheader("👤 Identificação")
            sel_cli = st.selectbox("Buscar na Base", [""] + sorted(Dashboard['RazaoSocial'].unique()))
            dados_c = {"n": "", "cnpj": "", "fone": "", "end": "", "fant": ""}
            if sel_cli:
                inf = Dashboard[Dashboard['RazaoSocial'] == sel_cli].iloc[0]
                dados_c = {"n": sel_cli, "cnpj": str(inf.get('CNPJ', '')), "fone": str(inf.get('Telefone', '')), "end": str(inf.get('Endereço', '')), "fant": str(inf.get('Nome Fantasia', ''))}
            
            c1, c2 = st.columns(2)
            cli_nome = c1.text_input("Cliente", value=dados_c['n'])
            cli_cnpj = c2.text_input("CNPJ", value=dados_c['cnpj'])
            cli_fone = c1.text_input("Fone", value=dados_c['fone'])
            cli_end = c2.text_input("Endereço", value=dados_c['end'])

        st.divider()

        # 2. Itens com FILTRO MESTRE FUNCIONAL
        df_base = produtos.merge(precos[['ID_COD', 'PRECO', 'GRAMAT']], on='ID_COD', how='left').fillna(0)
        lista_codigos = sorted(df_base['ID_COD'].unique())

        if st.button("➕ Adicionar Produto"):
            st.session_state.carrinho.append({"cod": lista_codigos[0], "qtd": 1})
            st.rerun()

        total_proposta = 0.0
        itens_pdf = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container(border=True):
                col_cod, col_prod, col_peso, col_cx, col_pr, col_qtd, col_tot = st.columns([1, 2.5, 0.8, 1, 1.2, 0.8, 1.2])
                
                # FILTRO MESTRE: O código altera tudo
                idx_atual = lista_codigos.index(item['cod'])
                novo_cod = col_cod.selectbox("Cód.", lista_codigos, index=idx_atual, key=f"sel_{i}")
                
                if novo_cod != item['cod']:
                    st.session_state.carrinho[i]['cod'] = novo_cod
                    st.rerun()

                # Busca automática dos dados baseada no código
                row = df_base[df_base['ID_COD'] == novo_cod].iloc[0]
                
                prod_txt = col_prod.text_input("Produto", value=row['DESCRICAONF'], key=f"p_{i}")
                peso_txt = col_peso.text_input("Peso", value=str(row.get('GRAMAT', '')), key=f"w_{i}")
                cx_txt = col_cx.text_input("Caixa", value=str(row.get('CX_EMB', 1)), key=f"x_{i}")
                pr_val = col_pr.number_input("Valor", value=float(row['PRECO']), format="%.2f", key=f"v_{i}")
                qtd_val = col_qtd.number_input("Qtd", min_value=1, value=item['qtd'], key=f"q_{i}")
                st.session_state.carrinho[i]['qtd'] = qtd_val

                sub = pr_val * qtd_val
                total_proposta += sub
                col_tot.write(f"R$ {sub:,.2f}")

                itens_pdf.append({"COD": novo_cod, "PROD": prod_txt, "PESO": peso_txt, "CX": cx_txt, "QTD": qtd_val, "VAL": pr_val, "TOT": sub})

                if st.button("🗑️", key=f"rem_{i}"):
                    st.session_state.carrinho.pop(i); st.rerun()

        # 3. LAYOUT DE IMPRESSÃO FIEL AO PDF
        if total_proposta > 0:
            st.subheader(f"Total: R$ {total_proposta:,.2f}")
            html_fiel = f"""
            <div style="font-family: Arial; padding: 20px; border: 1px solid #000; width: 800px; margin: auto;">
                <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px;">
                    <h2 style="margin:0; color: #d32f2f;">MEDTEXTIL</h2>
                    <p style="margin:0; font-size: 12px; font-weight: bold;">produto têxtil hospitalar</p>
                    <p style="margin:0; font-size: 11px;">ULTRA TEXTIL IND E COM DE PROD HOSP LTDA | 40.357.820/0001-50</p>
                    <p style="margin:0; font-size: 10px;">comercial.ultratextilpb@gmail.com | (83) 3233-9798</p>
                </div>
                <div style="margin-top: 20px; font-size: 11px;">
                    <table style="width: 100%;">
                        <tr>
                            <td><strong>Representante:</strong> Rosselic Marinho<br><strong>CPF:</strong> 338.610.054-68</td>
                            <td style="text-align: right;"><strong>Cliente:</strong> {cli_nome}<br><strong>CNPJ:</strong> {cli_cnpj}</td>
                        </tr>
                    </table>
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px;">
                    <thead>
                        <tr style="background: #eee;">
                            <th style="border: 1px solid #000;">COD</th><th style="border: 1px solid #000;">PRODUTO</th>
                            <th style="border: 1px solid #000;">PESO</th><th style="border: 1px solid #000;">CAIXA</th>
                            <th style="border: 1px solid #000;">QTDE</th><th style="border: 1px solid #000;">VALOR</th>
                            <th style="border: 1px solid #000;">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f"<tr><td style='border:1px solid #000; padding:4px;'>{it['COD']}</td><td style='border:1px solid #000;'>{it['PROD']}</td><td style='border:1px solid #000; text-align:center;'>{it['PESO']}</td><td style='border:1px solid #000; text-align:center;'>{it['CX']}</td><td style='border:1px solid #000; text-align:center;'>{it['QTD']}</td><td style='border:1px solid #000; text-align:right;'>{it['VAL']:.2f}</td><td style='border:1px solid #000; text-align:right;'>{it['TOT']:.2f}</td></tr>" for it in itens_pdf])}
                    </tbody>
                </table>
                <h3 style="text-align: right; margin-top: 20px;">VALOR TOTAL: R$ {total_proposta:,.2f}</h3>
            </div>
            """
            if st.button("🖨️ Imprimir Proposta"):
                components.html(f"{html_fiel}<script>window.print();</script>", height=800)

    # ---------------------------
    # MÓDULO 3: INATIVIDADE (CONSOLIDADO E INTACTO)
    # ---------------------------
    elif menu == "🚨 Inatividade":
        st.title("🚨 Controle de Inatividade")
        with st.sidebar:
            vendedores_inat = sorted([str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)])
            v_inat = st.multiselect("Vendedores", vendedores_inat, default=vendedores_inat)
            d_limite = st.number_input("Dias Limite", min_value=1, value=60)

        df_i = vendas[vendas['Vendedor'].isin(v_inat)].copy()
        if not df_i.empty:
            res = df_i.groupby(['RazaoSocial', 'Vendedor', 'Estado']).agg({'DataEmissao': 'max', 'TotalProduto2': 'sum'}).reset_index()
            res['Dias_Inativo'] = (datetime.now() - res['DataEmissao']).dt.days
            final = res[res['Dias_Inativo'] >= d_limite].sort_values('Dias_Inativo', ascending=False)
            st.dataframe(final, use_container_width=True)

    # ---------------------------
    # MÓDULO 4: EXPANSÃO PR (CONSOLIDADO E INTACTO)
    # ---------------------------
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Plano de Expansão PR 2026")
        if expansao:
            for sheet, df in expansao.items():
                st.subheader(f"Planilha: {sheet}")
                st.dataframe(df, use_container_width=True)
