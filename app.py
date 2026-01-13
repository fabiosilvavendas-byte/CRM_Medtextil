import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA (Padrão Web Consolidado)
st.set_page_config(
    page_title="CRM MedTextil - Pro", 
    layout="wide", 
    page_icon="🛡️"
)

# ===============================
# 2. CARREGAMENTO DOS DADOS (ESTRUTURA ORIGINAL)
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
    # MÓDULO 1: Dashboard (MANTIDO)
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
    # MÓDULO 2: Pedidos (NOVA LÓGICA DE SINCRONIZAÇÃO)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Módulo de Pedidos e Propostas")

        # CABEÇALHO DO CLIENTE
        with st.container(border=True):
            st.subheader("👤 Cadastro / Seleção de Cliente")
            sel_c = st.selectbox("Buscar Cliente Existente", [""] + sorted(Dashboard['RazaoSocial'].unique()))
            
            dados_c = {"nome": "", "cnpj": "", "fone": "", "email": "", "end": "", "fantasia": ""}
            if sel_c:
                inf = Dashboard[Dashboard['RazaoSocial'] == sel_c].iloc[0]
                dados_c = {
                    "nome": sel_c, "cnpj": str(inf.get('CNPJ', '')),
                    "fone": str(inf.get('Telefone', '')), "email": str(inf.get('Email NF-e', '')),
                    "end": f"{inf.get('Endereço', '')}", "fantasia": str(inf.get('Nome Fantasia', ''))
                }
            
            c1, c2 = st.columns(2)
            nome_c = c1.text_input("Razão Social", value=dados_c['nome'])
            cnpj_c = c2.text_input("CNPJ", value=dados_c['cnpj'])
            end_c = c1.text_input("Endereço", value=dados_c['end'])
            fone_c = c2.text_input("Telefone", value=dados_c['fone'])

        st.divider()

        # PREPARAÇÃO PRODUTOS
        df_base = produtos.merge(precos[['ID_COD', 'PRECO', 'LINHA', 'GRAMAT']], on='ID_COD', how='left')
        df_base['PRECO'] = df_base['PRECO'].fillna(0.0)

        if st.button("➕ Adicionar Novo Item"):
            st.session_state.carrinho.append({"id": datetime.now().timestamp()})
            st.rerun()

        total_proposta = 0.0
        itens_para_pdf = []

        # COLUNAS DO CARRINHO
        for i, item in enumerate(st.session_state.carrinho):
            with st.container(border=True):
                col_cod, col_prod, col_peso, col_cx, col_pr, col_qtd, col_tot = st.columns([1, 2.5, 0.8, 1, 1.2, 0.8, 1.2])
                
                # CÓDIGO MESTRE
                cod_sel = col_cod.selectbox("Cód.", sorted(df_base['ID_COD'].unique()), key=f"cod_{i}")
                
                # SINCRONIZAÇÃO AUTOMÁTICA
                row = df_base[df_base['ID_COD'] == cod_sel].iloc[0]
                
                prod_txt = col_prod.text_input("Produto", value=row['DESCRICAONF'], key=f"prod_{i}")
                peso_txt = col_peso.text_input("Peso", value=str(row.get('GRAMAT', 'S/I')), key=f"peso_{i}")
                cx_txt = col_cx.text_input("Cx Emb.", value=str(row.get('CX_EMB', 1)), key=f"cx_{i}")
                preco_val = col_pr.number_input("Preço (R$)", value=float(row['PRECO']), format="%.2f", key=f"pr_{i}")
                qtd_val = col_qtd.number_input("Qtd", min_value=1, value=1, key=f"qtd_{i}")
                
                subtotal = preco_val * qtd_val
                total_proposta += subtotal
                col_tot.write(f"**Total**\nR$ {subtotal:,.2f}")

                itens_para_pdf.append({
                    "COD": cod_sel, "PRODUTO": prod_txt, "PESO": peso_txt, 
                    "CX": cx_txt, "QTDE": qtd_val, "VALOR": preco_val, "TOTAL": subtotal
                })

                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()

        # BOTÕES DE AÇÃO E PDF
        if total_proposta > 0:
            st.subheader(f"Total Geral: R$ {total_proposta:,.2f}")
            c1, c2 = st.columns(2)
            
            html_proposta = f"""
            <div style="font-family: Arial; padding: 30px; border: 1px solid #000; width: 850px; margin: auto;">
                <div style="text-align: center; border-bottom: 2px solid #000;">
                    <h1 style="margin:0; color: #d32f2f;">MEDTEXTIL</h1>
                    <p style="margin:0;">ULTRA TEXTIL INDUSTRIA E COMERCIO DE PRODUTOS HOSPITALARES LTDA</p>
                    <p style="font-size: 11px;">40.357.820/0001-50 | comercial.ultratextilpb@gmail.com | (83) 3233-9798</p>
                    <h3 style="background: #eee; padding: 5px; border: 1px solid #000;">PROPOSTA COMERCIAL</h3>
                </div>
                <div style="margin-top: 15px; font-size: 12px;">
                    <strong>Representante:</strong> Rosselic Marinho | <strong>CPF:</strong> 338.610.054-68<br>
                    <strong>Cliente:</strong> {nome_c}<br>
                    <strong>CNPJ:</strong> {cnpj_c} | <strong>Endereço:</strong> {end_c}
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px;">
                    <tr style="background: #eee;">
                        <th style="border:1px solid #000;">COD</th><th style="border:1px solid #000;">PRODUTO</th>
                        <th style="border:1px solid #000;">PESO</th><th style="border:1px solid #000;">CX</th>
                        <th style="border:1px solid #000;">QTDE</th><th style="border:1px solid #000;">VALOR</th>
                        <th style="border:1px solid #000;">TOTAL</th>
                    </tr>
                    {"".join([f"<tr><td style='border:1px solid #000; padding:4px;'>{it['COD']}</td><td style='border:1px solid #000;'>{it['PRODUTO']}</td><td style='border:1px solid #000;'>{it['PESO']}</td><td style='border:1px solid #000;'>{it['CX']}</td><td style='border:1px solid #000;'>{it['QTDE']}</td><td style='border:1px solid #000;'>{it['VALOR']:.2f}</td><td style='border:1px solid #000;'>{it['TOTAL']:.2f}</td></tr>" for it in itens_para_pdf])}
                </table>
                <h3 style="text-align: right;">TOTAL: R$ {total_proposta:,.2f}</h3>
            </div>
            """
            
            with c1:
                if st.button("🖨️ Imprimir Proposta"):
                    components.html(f"{html_proposta}<script>window.print();</script>", height=600)
            with c2:
                st.link_button("📱 Enviar WhatsApp", f"https://wa.me/{fone_c.replace(' ','')}?text=Proposta%20MedTextil")

    # ---------------------------
    # MÓDULO 3: Inatividade (MANTIDO)
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
    # MÓDULO 4: Expansão (MANTIDO)
    # ---------------------------
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Plano de Expansão 2026")
        if expansao:
            for sheet, df in expansao.items():
                st.subheader(f"Planilha: {sheet}")
                st.dataframe(df, use_container_width=True)
