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
    # MÓDULO 1: Dashboard GERAL
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
    # MÓDULO 2: PEDIDOS (NOVO MÓDULO REESTRUTURADO)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Emissão de Proposta Comercial")

        # SEÇÃO 1: CADASTRO/BUSCA DE CLIENTE
        st.subheader("👤 Informações do Cliente")
        modo_c = st.radio("Origem do Cliente", ["Buscar na Base", "Novo Cadastro"], horizontal=True)
        dados_c = {"nome": "", "cnpj": "", "endereco": "", "telefone": "", "email": ""}

        if modo_c == "Buscar na Base":
            lista_clientes = sorted(Dashboard['RazaoSocial'].unique())
            sel_c = st.selectbox("Selecione o Cliente", [""] + lista_clientes)
            if sel_c:
                # Busca automática nas colunas da planilha Consulta Vendedores
                inf = Dashboard[Dashboard['RazaoSocial'] == sel_c].iloc[0]
                dados_c = {
                    "nome": sel_c,
                    "cnpj": str(inf.get('CNPJ', 'Não informado')),
                    "endereco": f"{inf.get('Endereço', 'Não informado')}, {inf.get('Cidade', '')}",
                    "telefone": str(inf.get('Telefone', 'Não informado')),
                    "email": str(inf.get('Email', 'Não informado'))
                }
        else:
            c1, c2 = st.columns(2)
            dados_c['nome'] = c1.text_input("Razão Social")
            dados_c['cnpj'] = c2.text_input("CNPJ")
            dados_c['endereco'] = c1.text_input("Endereço Completo")
            dados_c['telefone'] = c2.text_input("Telefone")

        st.divider()

        # SEÇÃO 2: ITENS DO PEDIDO
        st.subheader("📦 Itens do Pedido")
        # Prepara base cruzada (Sincroniza precos com LINHA e GRAMAT) [cite: 1, 2, 3]
        df_comb = produtos.merge(precos[['ID_COD', 'PRECO', 'LINHA', 'GRAMAT']], on='ID_COD', how='left')
        df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)

        if st.button("➕ Adicionar Novo Item"):
            st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})
            st.rerun()

        total_pedido = 0.0
        itens_print = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container(border=True):
                # Layout solicitado: Cód, Produto, Cx, Preço, Qtd, Total
                c_cod, c_prod, c_cx, c_pr, c_qtd, c_tot = st.columns([1.5, 3.5, 1, 1.2, 1, 1.2])

                # Seleção por Código
                cod_sel = c_cod.selectbox("Cód.", sorted(df_comb['ID_COD'].unique()), key=f"c_{i}")
                
                # Sincronização automática
                dados_p = df_comb[df_comb['ID_COD'] == cod_sel].iloc[0]
                
                prod_txt = c_prod.text_input("Produto", value=dados_p['DESCRICAONF'], key=f"p_{i}")
                cx_val = c_cx.text_input("Cx", value=str(dados_p.get('CX_EMB', 1)), key=f"x_{i}")
                pr_unit = c_pr.number_input("Unit.", value=float(dados_p['PRECO']), format="%.2f", key=f"v_{i}")
                qtd_val = c_qtd.number_input("Qtd", min_value=1, value=1, key=f"q_{i}")
                
                subtotal = pr_unit * qtd_val
                total_pedido += subtotal
                c_tot.metric("Valor", f"R$ {subtotal:,.2f}")

                itens_print.append({
                    "COD": cod_sel, "PRODUTO": prod_txt, "CX": cx_val, 
                    "QTDE": qtd_val, "VALOR": pr_unit, "TOTAL": subtotal
                })

                if st.button(f"🗑️ Remover Item {i+1}", key=f"r_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()

        st.divider()
        st.subheader(f"💰 Total da Proposta: R$ {total_pedido:,.2f}")

        # SEÇÃO 3: PDF E WHATSAPP (CONFORME MODELO PDF)
        if total_pedido > 0:
            c1, c2 = st.columns(2)
            
            # Estrutura HTML baseada no modelo "ULTRA TEXTIL" enviado [cite: 3, 4, 6]
            html_proposta = f"""
            <div style="border:1px solid #000; padding:20px; font-family: Arial, sans-serif;">
                <div style="text-align:center;">
                    <h2 style="margin:0; color:#d32f2f;">MEDTEXTIL</h2>
                    <p style="margin:0; font-size:12px;">ULTRA TEXTIL IND E COM DE PROD HOSP LTDA</p>
                    <p style="margin:0; font-size:11px;">CNPJ: 40.357.820/0001-50 | (83) 3233-9798</p>
                    <h3 style="background:#eee; padding:5px; border:1px solid #000;">PROPOSTA COMERCIAL</h3>
                </div>
                <div style="margin: 20px 0; border:1px solid #ccc; padding:10px;">
                    <strong>DADOS DO CLIENTE:</strong><br>
                    <strong>Cliente:</strong> {dados_c['nome']}<br>
                    <strong>CNPJ/CPF:</strong> {dados_c['cnpj']} | <strong>Fone:</strong> {dados_c['telefone']}<br>
                    <strong>Endereço:</strong> {dados_c['endereco']}
                </div>
                <table style="width:100%; border-collapse: collapse; font-size:12px;">
                    <thead>
                        <tr style="background:#f2f2f2; border-bottom: 2px solid #000;">
                            <th style="padding:5px; text-align:left;">COD</th>
                            <th style="padding:5px; text-align:left;">PRODUTO</th>
                            <th style="padding:5px; text-align:center;">CX</th>
                            <th style="padding:5px; text-align:center;">QTDE</th>
                            <th style="padding:5px; text-align:right;">VALOR</th>
                            <th style="padding:5px; text-align:right;">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f"<tr style='border-bottom: 1px solid #ddd;'><td style='padding:5px;'>{it['COD']}</td><td style='padding:5px;'>{it['PRODUTO']}</td><td style='padding:5px; text-align:center;'>{it['CX']}</td><td style='padding:5px; text-align:center;'>{it['QTDE']}</td><td style='padding:5px; text-align:right;'>R$ {it['VALOR']:.2f}</td><td style='padding:5px; text-align:right;'>R$ {it['TOTAL']:.2f}</td></tr>" for it in itens_print])}
                    </tbody>
                </table>
                <h3 style="text-align:right; margin-top:20px;">TOTAL FINAL: R$ {total_pedido:,.2f}</h3>
                <div style="margin-top:30px; font-size:10px; color:#555;">
                    <strong>DECLARAÇÕES:</strong><br>
                    - Prazo de entrega: até 30 dias corridos.<br>
                    - Validade da proposta: 60 dias.<br>
                    - Garantia: substituição em até 5 dias úteis.<br>
                    - Preços incluem todos os impostos.
                </div>
            </div>
            """

            with c1:
                if st.button("📄 Visualizar Proposta (PDF)"):
                    st.components.v1.html(html_proposta, height=800, scrolling=True)
            
            with c2:
                msg_wa = f"Olá, segue proposta MedTextil para {dados_c['nome']} no valor total de R$ {total_pedido:,.2f}"
                link_wa = f"https://wa.me/{dados_c['telefone'].replace('(','').replace(')','').replace('-','').replace(' ','')}?text={msg_wa}"
                st.link_button("📱 Enviar via WhatsApp", link_wa)

    # ---------------------------
    # MÓDULO 3: INATIVIDADE
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
    # MÓDULO 4: EXPANSÃO PR
    # ---------------------------
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Plano de Expansão PR 2026")
        
        if "df_leads_ativa" not in st.session_state:
            if expansao and 'Gestão de Leads' in expansao:
                st.session_state.df_leads_ativa = expansao['Gestão de Leads'].copy()
            else:
                st.session_state.df_leads_ativa = pd.DataFrame(columns=["Data de Entrada", "Empresa", "Cidade", "Segmento", "Contato", "Status do Lead", "Dor Principal"])

        tab_view, tab_add, tab_edit = st.tabs(["📋 Visualizar Leads", "➕ Novo Lead", "📈 Atualizar Funil"])

        with tab_view:
            st.dataframe(st.session_state.df_leads_ativa, use_container_width=True, hide_index=True)
            if not st.session_state.df_leads_ativa.empty:
                csv = st.session_state.df_leads_ativa.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Baixar Leads", csv, "leads.csv", "text/csv")

        with tab_add:
            with st.form("novo_lead_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                emp_n = c1.text_input("Empresa")
                cid_n = c2.text_input("Cidade")
                seg_n = c1.selectbox("Segmento", ["Hospitalar", "Distribuidora", "Clínica", "Público"])
                con_n = c2.text_input("Contato")
                dor_n = st.text_area("Necessidade")
                if st.form_submit_button("✅ Salvar Lead"):
                    if emp_n:
                        novo = {"Data de Entrada": datetime.now().strftime("%d/%m/%Y"), "Empresa": emp_n, "Cidade": cid_n, "Segmento": seg_n, "Contato": con_n, "Status do Lead": "Prospecção", "Dor Principal": dor_n}
                        st.session_state.df_leads_ativa = pd.concat([st.session_state.df_leads_ativa, pd.DataFrame([novo])], ignore_index=True)
                        st.success("Lead salvo!")
                        st.rerun()

        with tab_edit:
            if not st.session_state.df_leads_ativa.empty:
                emp_edit = st.selectbox("Selecionar Lead", st.session_state.df_leads_ativa['Empresa'].unique())
                status_edit = st.select_slider("Alterar Status", options=["Prospecção", "Qualificação", "Proposta", "Negociação", "Fechamento"])
                if st.button("Atualizar Histórico"):
                    st.toast(f"Status de {emp_edit} atualizado!", icon="🚀")
