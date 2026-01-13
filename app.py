import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA (Mantendo o ícone para o app no iPhone)
st.set_page_config(
    page_title="CRM MedTextil - Pro", 
    layout="wide", 
    page_icon="🛡️"
)

# ===============================
# 2. CARREGAMENTO DOS DADOS (SISTEMA ROBUSTO)
# ===============================
@st.cache_data
def carregar_dados():
    try:
        # Arquivos Originais
        Dashboard = pd.read_excel("dados/CONSULTA_VENDEDORES.xlsx")
        
        try:
            produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx", sheet_name='CONCILIADA')
        except:
            produtos = pd.read_excel("dados/Produtos_Agrupados_Completos_conciliados.xlsx")
            
        try:
            precos = pd.read_excel("dados/TABELAS_NE.xlsx", sheet_name='TAB 5%')
        except:
            precos = pd.read_excel("dados/TABELAS_NE.xlsx")
            
        # NOVO ARQUIVO DE EXPANSÃO
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
if "clientes_novos" not in st.session_state: st.session_state.clientes_novos = []
if "dados_cliente" not in st.session_state: st.session_state.dados_cliente = {}

# ===============================
# FUNÇÃO PARA GERAR PDF
# ===============================
def gerar_pdf_proposta(dados_cliente, itens_pedido, total):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elementos = []
    styles = getSampleStyleSheet()
    
    # Estilo customizado
    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=1
    )
    
    estilo_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )
    
    # Cabeçalho
    elementos.append(Paragraph("PROPOSTA COMERCIAL", estilo_titulo))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Dados do Cliente
    elementos.append(Paragraph("<b>DADOS DO CLIENTE</b>", styles['Heading2']))
    elementos.append(Spacer(1, 0.3*cm))
    
    info_cliente = f"""
    <b>Cliente:</b> {dados_cliente.get('nome', 'N/A')}<br/>
    <b>CNPJ:</b> {dados_cliente.get('cnpj', 'N/A')}<br/>
    <b>Endereço:</b> {dados_cliente.get('endereco', 'N/A')}<br/>
    <b>Cidade:</b> {dados_cliente.get('cidade', 'N/A')} - <b>Estado:</b> {dados_cliente.get('estado', 'N/A')}
    """
    elementos.append(Paragraph(info_cliente, estilo_normal))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Tabela de Produtos
    elementos.append(Paragraph("<b>ITENS DO PEDIDO</b>", styles['Heading2']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Cabeçalho da tabela
    dados_tabela = [['Cód.', 'Produto', 'Cx Embarque', 'Preço Unit.', 'Qtd', 'Total']]
    
    # Linhas de produtos
    for item in itens_pedido:
        dados_tabela.append([
            str(item['COD']),
            str(item['PRODUTO'])[:40],  # Limita tamanho do nome
            str(item['CX']),
            f"R$ {item['VALOR']:.2f}",
            str(item['QTDE']),
            f"R$ {item['TOTAL']:.2f}"
        ])
    
    # Linha de total
    dados_tabela.append(['', '', '', '', 'TOTAL:', f"R$ {total:.2f}"])
    
    # Criar tabela
    tabela = Table(dados_tabela, colWidths=[3*cm, 7*cm, 2.5*cm, 2.5*cm, 2*cm, 2.5*cm])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elementos.append(tabela)
    elementos.append(Spacer(1, 1*cm))
    
    # Rodapé
    elementos.append(Paragraph(f"<i>Proposta gerada em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</i>", estilo_normal))
    
    # Construir PDF
    doc.build(elementos)
    buffer.seek(0)
    return buffer

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
    # MÓDULO 2: PEDIDOS (ATUALIZADO COM PDF)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Sistema de Pedidos")
        
        # Preparar dados combinados
        cols_precos = ['ID_COD', 'PRECO']
        if 'LINHA' in precos.columns: cols_precos.append('LINHA')
        if 'GRAMAT' in precos.columns: cols_precos.append('GRAMAT')

        df_comb = produtos.merge(precos[cols_precos], on='ID_COD', how='left')
        df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)
        df_comb['LINHA'] = df_comb['LINHA'].fillna('')
        df_comb['GRAMAT'] = df_comb['GRAMAT'].fillna('')
        
        # Seção 1: DADOS DO CLIENTE
        st.subheader("📋 Dados do Cliente")
        col1, col2 = st.columns(2)
        
        with col1:
            # Buscar cliente existente ou criar novo
            clientes_existentes = sorted(Dashboard['RazaoSocial'].unique())
            tipo_cliente = st.radio("Tipo de Cliente", ["Existente", "Novo"], horizontal=True)
            
            if tipo_cliente == "Existente":
                cliente_selecionado = st.selectbox("Selecionar Cliente", clientes_existentes)
                # Buscar dados do cliente
                dados_cli = Dashboard[Dashboard['RazaoSocial'] == cliente_selecionado].iloc[0]
                st.session_state.dados_cliente = {
                    'nome': cliente_selecionado,
                    'cnpj': dados_cli.get('CNPJ', 'N/A'),
                    'endereco': dados_cli.get('Endereco', 'N/A'),
                    'cidade': dados_cli.get('Cidade', 'N/A'),
                    'estado': dados_cli.get('Estado', 'N/A')
                }
            else:
                st.session_state.dados_cliente = {
                    'nome': st.text_input("Nome/Razão Social", value=st.session_state.dados_cliente.get('nome', '')),
                    'cnpj': st.text_input("CNPJ", value=st.session_state.dados_cliente.get('cnpj', '')),
                    'endereco': st.text_input("Endereço", value=st.session_state.dados_cliente.get('endereco', '')),
                    'cidade': st.text_input("Cidade", value=st.session_state.dados_cliente.get('cidade', '')),
                    'estado': st.text_input("Estado", value=st.session_state.dados_cliente.get('estado', ''))
                }
        
        with col2:
            st.info(f"""
            **Cliente:** {st.session_state.dados_cliente.get('nome', 'N/A')}  
            **CNPJ:** {st.session_state.dados_cliente.get('cnpj', 'N/A')}  
            **Endereço:** {st.session_state.dados_cliente.get('endereco', 'N/A')}  
            **Cidade:** {st.session_state.dados_cliente.get('cidade', 'N/A')}  
            **Estado:** {st.session_state.dados_cliente.get('estado', 'N/A')}
            """)
        
        st.divider()
        
        # Seção 2: ITENS DO PEDIDO
        st.subheader("🛍️ Itens do Pedido")
        
        total_proposta = 0.0
        itens_final = []

        if st.button("➕ Adicionar Novo Item"):
            st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})
            st.rerun()

        # Exibir itens do carrinho
        for i, item in enumerate(st.session_state.carrinho):
            with st.container():
                st.markdown(f"**Item {i+1}**")
                col_cod, col_prod, col_cx, col_preco, col_qtd, col_rem = st.columns([2, 4, 2, 2, 2, 1])
                
                # Buscar por código
                cod_digitado = col_cod.text_input("Código", key=f"cod_{i}", label_visibility="collapsed", placeholder="Cód.")
                
                if cod_digitado:
                    # Buscar produto pelo código
                    produto_encontrado = df_comb[df_comb['ID_COD'] == cod_digitado]
                    
                    if not produto_encontrado.empty:
                        dados_item = produto_encontrado.iloc[0]
                        
                        col_prod.text_input("Produto", value=str(dados_item['DESCRICAONF']), key=f"prod_{i}", disabled=True, label_visibility="collapsed")
                        cx_e = col_cx.text_input("Cx", value=str(dados_item.get('CX_EMB', '')), key=f"cx_{i}", label_visibility="collapsed")
                        pr_u = col_preco.number_input("Preço", value=float(dados_item['PRECO']), key=f"preco_{i}", format="%.2f", label_visibility="collapsed")
                        qtd = col_qtd.number_input("Qtd", min_value=1, value=1, key=f"qtd_{i}", label_visibility="collapsed")
                        
                        sub = pr_u * qtd
                        total_proposta += sub
                        
                        itens_final.append({
                            "COD": dados_item['ID_COD'], 
                            "PRODUTO": dados_item['DESCRICAONF'],
                            "CX": cx_e, 
                            "VALOR": pr_u, 
                            "QTDE": qtd, 
                            "TOTAL": sub
                        })
                        
                        st.caption(f"Marca: {dados_item['LINHA']} | Gramatura: {dados_item['GRAMAT']} | Subtotal: R$ {sub:,.2f}")
                    else:
                        col_prod.warning("Código não encontrado")
                
                if col_rem.button("🗑️", key=f"rem_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()
                
                st.divider()

        # Resumo e Ações
        st.markdown(f"### 💰 Total da Proposta: R$ {total_proposta:,.2f}")

        if itens_final and st.session_state.dados_cliente.get('nome'):
            col_pdf, col_wa, col_limpar = st.columns(3)
            
            # Gerar PDF
            if col_pdf.button("📄 Gerar PDF da Proposta", use_container_width=True):
                pdf_buffer = gerar_pdf_proposta(st.session_state.dados_cliente, itens_final, total_proposta)
                st.download_button(
                    label="⬇️ Baixar Proposta em PDF",
                    data=pdf_buffer,
                    file_name=f"Proposta_{st.session_state.dados_cliente['nome']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # WhatsApp
            if col_wa.button("📱 Enviar via WhatsApp", use_container_width=True):
                texto_wa = f"Olá! Segue proposta comercial MedTextil para {st.session_state.dados_cliente['nome']} no valor de R$ {total_proposta:,.2f}"
                st.markdown(f"[🔗 Clique aqui para enviar no WhatsApp](https://wa.me/?text={texto_wa})")
            
            # Limpar pedido
            if col_limpar.button("🗑️ Limpar Pedido", use_container_width=True):
                st.session_state.carrinho = []
                st.session_state.dados_cliente = {}
                st.rerun()
        else:
            if not st.session_state.dados_cliente.get('nome'):
                st.warning("⚠️ Preencha os dados do cliente para gerar a proposta")
            if not itens_final:
                st.warning("⚠️ Adicione itens ao pedido para gerar a proposta")

    # ---------------------------
    # MÓDULO 3: INATIVIDADE
    # ---------------------------
    elif menu == "🚨 Inatividade":
        st.title("🚨 Inatividade")
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
