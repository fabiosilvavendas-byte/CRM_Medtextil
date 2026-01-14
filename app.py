import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
if "dados_pedido" not in st.session_state: st.session_state.dados_pedido = {}

# ===============================
# FUNÇÃO PARA GERAR PDF (MODELO EXATO)
# ===============================
def gerar_pdf_proposta(dados_cliente, dados_pedido, itens_pedido, total):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Margens
    margin_left = 30
    margin_right = width - 30
    y = height - 40
    
    # ========== CABEÇALHO EMPRESA ==========
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_left, y, "MEDTEXTIL")
    y -= 20
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left, y, "ULTRA TEXTIL INDUSTRIA E COMERCIO DE PRODUTOS HOSPITALARES LTDA")
    y -= 15
    
    c.setFont("Helvetica", 9)
    c.drawString(margin_left, y, "40.357.820/0001-50 - (83) 3233-9798")
    y -= 12
    c.drawString(margin_left, y, "comercial.ultratextilpb@gmail.com")
    y -= 12
    c.drawString(margin_left, y, "R Y DOIS, 355 - GALPÃO 3 - Distrito Industrial - João Pessoa - PB - CEP: 58.082-025")
    y -= 12
    c.drawString(margin_left, y, "CNPJ: 40.357.820/0001-50   Inscrição Estadual: 16.390.286-0")
    y -= 25
    
    # ========== TÍTULO PROPOSTA ==========
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y, "PROPOSTA COMERCIAL")
    y -= 30
    
    # ========== INFORMAÇÕES DO CLIENTE ==========
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "INFORMAÇÕES DO CLIENTE")
    y -= 15
    
    c.setFont("Helvetica", 9)
    c.drawString(margin_left, y, f"Cliente: {dados_cliente.get('razao_social', 'N/A')}")
    y -= 12
    c.drawString(margin_left, y, f"Nome Fantasia: {dados_cliente.get('nome_fantasia', dados_cliente.get('razao_social', 'N/A'))}")
    y -= 12
    c.drawString(margin_left, y, f"CNPJ: {dados_cliente.get('cnpj', 'N/A')}")
    y -= 12
    c.drawString(margin_left, y, f"Endereço: {dados_cliente.get('endereco', 'N/A')}")
    y -= 12
    c.drawString(margin_left, y, f"Representante legal: {dados_cliente.get('representante', 'N/A')}")
    y -= 12
    c.drawString(margin_left, y, f"CPF: {dados_cliente.get('cpf_rep', 'N/A')}   RG: {dados_cliente.get('rg_rep', 'N/A')}")
    y -= 12
    c.drawString(margin_left, y, f"Telefone: {dados_cliente.get('telefone', 'N/A')}")
    y -= 12
    c.drawString(margin_left, y, f"Email NF-e: {dados_cliente.get('email', 'N/A')}")
    y -= 25
    
    # ========== INFORMAÇÕES DO PEDIDO ==========
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "INFORMAÇÕES DO PEDIDO")
    y -= 15
    
    c.setFont("Helvetica", 9)
    c.drawString(margin_left, y, f"Pedido N°: {dados_pedido.get('numero', 'N/A')}")
    c.drawString(margin_left + 200, y, f"Data da Venda: {dados_pedido.get('data', datetime.now().strftime('%d/%m/%Y'))}")
    y -= 12
    c.drawString(margin_left, y, f"Tipo de frete: {dados_pedido.get('frete', 'CIF')}")
    c.drawString(margin_left + 200, y, f"Condições de Pagto: {dados_pedido.get('pagamento', '30 dias')}")
    y -= 25
    
    # ========== TABELA DE PRODUTOS ==========
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_left, y, "Detalhes do Pedido")
    y -= 20
    
    # Cabeçalho da tabela
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin_left, y, "COD.")
    c.drawString(margin_left + 50, y, "PRODUTO")
    c.drawString(margin_left + 270, y, "PESO")
    c.drawString(margin_left + 310, y, "CX EMBARQUE")
    c.drawString(margin_left + 390, y, "QTDE")
    c.drawString(margin_left + 430, y, "VALOR")
    c.drawString(margin_left + 500, y, "TOTAL")
    y -= 3
    
    # Linha separadora
    c.line(margin_left, y, margin_right, y)
    y -= 12
    
    # Itens da tabela
    c.setFont("Helvetica", 8)
    for item in itens_pedido:
        if y < 100:  # Nova página se necessário
            c.showPage()
            y = height - 40
            c.setFont("Helvetica", 8)
        
        produto_nome = str(item['PRODUTO'])[:45]  # Limita tamanho
        
        c.drawString(margin_left, y, str(item['COD']))
        c.drawString(margin_left + 50, y, produto_nome)
        c.drawString(margin_left + 270, y, str(item.get('PESO', '-')))
        c.drawString(margin_left + 310, y, str(item['CX']))
        c.drawString(margin_left + 390, y, str(item['QTDE']))
        c.drawString(margin_left + 430, y, f"R$ {item['VALOR']:.2f}")
        c.drawString(margin_left + 500, y, f"R$ {item['TOTAL']:.2f}")
        y -= 12
    
    # Linha antes do total
    y -= 5
    c.line(margin_left, y, margin_right, y)
    y -= 15
    
    # TOTAIS
    c.setFont("Helvetica-Bold", 10)
    qtd_itens = sum([item['QTDE'] for item in itens_pedido])
    c.drawString(margin_left, y, f"Qtde Itens: {qtd_itens}")
    c.drawString(margin_left + 150, y, f"Frete: {dados_pedido.get('valor_frete', 'R$ 0,00')}")
    c.drawString(margin_left + 300, y, f"Total Final: R$ {total:,.2f}")
    y -= 30
    
    # ========== OBSERVAÇÕES ==========
    if dados_pedido.get('observacao'):
        c.setFont("Helvetica", 8)
        c.drawString(margin_left, y, f"Observação: {dados_pedido.get('observacao', '')}")
        y -= 20
    
    # ========== DECLARAÇÕES ==========
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_left, y, "DECLARAÇÕES:")
    y -= 15
    
    c.setFont("Helvetica", 8)
    declaracoes = [
        "- Prazo de entrega: até 30 dias corridos.",
        "- Validade da proposta: 60 dias.",
        "- Garantia: substituição em até 5 dias úteis.",
        "- Preços incluem todos os impostos.",
        "- Produtos novos com validade mínima de 5 anos.",
        "- Registro ANVISA anexado."
    ]
    
    for decl in declaracoes:
        c.drawString(margin_left, y, decl)
        y -= 12
    
    y -= 20
    
    # ========== ASSINATURA ==========
    cidade = dados_cliente.get('cidade', 'João Pessoa')
    data_atual = datetime.now()
    c.setFont("Helvetica", 9)
    c.drawString(margin_left, y, f"{cidade}, {data_atual.day} de {data_atual.strftime('%B')} de {data_atual.year}.")
    
    # Finalizar PDF
    c.save()
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
    # MÓDULO 2: PEDIDOS (MODELO FIEL)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Sistema de Pedidos - MedTextil")
        
        # Preparar dados combinados
        cols_precos = ['ID_COD', 'PRECO']
        if 'LINHA' in precos.columns: cols_precos.append('LINHA')
        if 'GRAMAT' in precos.columns: cols_precos.append('GRAMAT')

        df_comb = produtos.merge(precos[cols_precos], on='ID_COD', how='left')
        df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)
        df_comb['LINHA'] = df_comb['LINHA'].fillna('')
        df_comb['GRAMAT'] = df_comb['GRAMAT'].fillna('')
        
        # ========== SEÇÃO 1: DADOS DO CLIENTE ==========
        st.subheader("📋 Informações do Cliente")
        
        tab_cliente, tab_pedido = st.tabs(["👤 Cliente", "📝 Pedido"])
        
        with tab_cliente:
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_cliente = st.radio("Tipo de Cliente", ["Existente", "Novo"], horizontal=True)
                
                if tipo_cliente == "Existente":
                    clientes_existentes = sorted(Dashboard['RazaoSocial'].unique())
                    cliente_selecionado = st.selectbox("Selecionar Cliente", clientes_existentes)
                    
                    # Buscar dados do cliente no Dashboard
                    dados_cli = Dashboard[Dashboard['RazaoSocial'] == cliente_selecionado].iloc[0]
                    
                    st.session_state.dados_cliente = {
                        'razao_social': cliente_selecionado,
                        'nome_fantasia': dados_cli.get('NomeFantasia', cliente_selecionado),
                        'cnpj': dados_cli.get('CNPJ', 'N/A'),
                        'endereco': dados_cli.get('Endereco', 'N/A'),
                        'cidade': dados_cli.get('Cidade', 'N/A'),
                        'estado': dados_cli.get('Estado', 'N/A'),
                        'telefone': dados_cli.get('Telefone', 'N/A'),
                        'email': dados_cli.get('Email', 'N/A'),
                        'representante': st.text_input("Representante Legal", value=st.session_state.dados_cliente.get('representante', '')),
                        'cpf_rep': st.text_input("CPF Representante", value=st.session_state.dados_cliente.get('cpf_rep', '')),
                        'rg_rep': st.text_input("RG Representante", value=st.session_state.dados_cliente.get('rg_rep', ''))
                    }
                else:
                    st.session_state.dados_cliente = {
                        'razao_social': st.text_input("Razão Social", value=st.session_state.dados_cliente.get('razao_social', '')),
                        'nome_fantasia': st.text_input("Nome Fantasia", value=st.session_state.dados_cliente.get('nome_fantasia', '')),
                        'cnpj': st.text_input("CNPJ", value=st.session_state.dados_cliente.get('cnpj', '')),
                        'endereco': st.text_input("Endereço Completo", value=st.session_state.dados_cliente.get('endereco', '')),
                        'cidade': st.text_input("Cidade", value=st.session_state.dados_cliente.get('cidade', '')),
                        'estado': st.text_input("Estado", value=st.session_state.dados_cliente.get('estado', '')),
                        'telefone': st.text_input("Telefone", value=st.session_state.dados_cliente.get('telefone', '')),
                        'email': st.text_input("Email NF-e", value=st.session_state.dados_cliente.get('email', '')),
                        'representante': st.text_input("Representante Legal", value=st.session_state.dados_cliente.get('representante', '')),
                        'cpf_rep': st.text_input("CPF Representante", value=st.session_state.dados_cliente.get('cpf_rep', '')),
                        'rg_rep': st.text_input("RG Representante", value=st.session_state.dados_cliente.get('rg_rep', ''))
                    }
            
            with col2:
                st.info(f"""
                **Cliente:** {st.session_state.dados_cliente.get('razao_social', 'N/A')}  
                **Nome Fantasia:** {st.session_state.dados_cliente.get('nome_fantasia', 'N/A')}  
                **CNPJ:** {st.session_state.dados_cliente.get('cnpj', 'N/A')}  
                **Endereço:** {st.session_state.dados_cliente.get('endereco', 'N/A')}  
                **Cidade/UF:** {st.session_state.dados_cliente.get('cidade', 'N/A')}/{st.session_state.dados_cliente.get('estado', 'N/A')}  
                **Telefone:** {st.session_state.dados_cliente.get('telefone', 'N/A')}  
                **Email:** {st.session_state.dados_cliente.get('email', 'N/A')}
                """)
        
        with tab_pedido:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.session_state.dados_pedido['numero'] = st.text_input("Número do Pedido", value=st.session_state.dados_pedido.get('numero', ''))
                st.session_state.dados_pedido['data'] = st.date_input("Data da Venda", value=datetime.now()).strftime('%d/%m/%Y')
                st.session_state.dados_pedido['frete'] = st.selectbox("Tipo de Frete", ["CIF", "FOB"], index=0)
            
            with col_p2:
                st.session_state.dados_pedido['pagamento'] = st.text_input("Condições de Pagamento", value=st.session_state.dados_pedido.get('pagamento', '30 dias'))
                st.session_state.dados_pedido['valor_frete'] = st.text_input("Valor do Frete", value=st.session_state.dados_pedido.get('valor_frete', 'R$ 0,00'))
                st.session_state.dados_pedido['observacao'] = st.text_area("Observação", value=st.session_state.dados_pedido.get('observacao', ''))
        
        st.divider()
        
        # ========== SEÇÃO 2: ITENS DO PEDIDO ==========
        st.subheader("🛍️ Itens do Pedido")
        
        # Inicializar lista de produtos se não existir
        if "produtos_selecionados" not in st.session_state:
            st.session_state.produtos_selecionados = {}
        
        total_proposta = 0.0
        itens_final = []

        if st.button("➕ Adicionar Novo Item", type="primary"):
            st.session_state.carrinho.append({"id": len(st.session_state.carrinho)})
            st.rerun()

        # Exibir itens do carrinho
        for i, item in enumerate(st.session_state.carrinho):
            st.markdown(f"### Item {i+1}")
            
            # Linha 1: Busca por Código ou Nome
            col_tipo, col_busca = st.columns([1, 5])
            tipo_busca = col_tipo.radio("Buscar por:", ["Código", "Nome"], key=f"tipo_{i}", horizontal=True, label_visibility="collapsed")
            
            cod_produto_atual = None
            
            if tipo_busca == "Código":
                cod_digitado = col_busca.text_input("Digite o Código do Produto", key=f"cod_input_{i}", placeholder="Ex: 12345")
                
                if cod_digitado:
                    produto_encontrado = df_comb[df_comb['ID_COD'] == cod_digitado]
                    
                    if not produto_encontrado.empty:
                        cod_produto_atual = cod_digitado
                        # Salvar dados do produto no session state
                        if f"prod_{i}" not in st.session_state.produtos_selecionados or st.session_state.produtos_selecionados.get(f"prod_{i}", {}).get("cod") != cod_digitado:
                            dados_item = produto_encontrado.iloc[0]
                            st.session_state.produtos_selecionados[f"prod_{i}"] = {
                                "cod": str(dados_item['ID_COD']),
                                "nome": str(dados_item['DESCRICAONF']),
                                "peso": str(dados_item.get('GRAMAT', '-')) if pd.notna(dados_item.get('GRAMAT')) else '-',
                                "cx": str(dados_item.get('CX_EMB', '')) if pd.notna(dados_item.get('CX_EMB')) else '',
                                "preco": float(dados_item.get('PRECO', 0)) if pd.notna(dados_item.get('PRECO')) else 0.0,
                                "marca": str(dados_item.get('LINHA', 'N/A')),
                                "gramat": str(dados_item.get('GRAMAT', 'N/A'))
                            }
                            st.rerun()
                    else:
                        col_busca.warning("❌ Código não encontrado")
                        
            else:  # Buscar por Nome
                opcoes_busca = ["Selecione um produto..."] + [f"{row['ID_COD']} - {row['DESCRICAONF']}" for _, row in df_comb.iterrows()]
                
                busca = col_busca.selectbox(
                    "Selecione o Produto",
                    options=opcoes_busca,
                    key=f"busca_select_{i}",
                    label_visibility="collapsed"
                )
                
                if busca and busca != "Selecione um produto...":
                    cod_selecionado = busca.split(" - ")[0]
                    cod_produto_atual = cod_selecionado
                    
                    # Salvar dados do produto no session state
                    if f"prod_{i}" not in st.session_state.produtos_selecionados or st.session_state.produtos_selecionados.get(f"prod_{i}", {}).get("cod") != cod_selecionado:
                        produto_encontrado = df_comb[df_comb['ID_COD'] == cod_selecionado]
                        if not produto_encontrado.empty:
                            dados_item = produto_encontrado.iloc[0]
                            st.session_state.produtos_selecionados[f"prod_{i}"] = {
                                "cod": str(dados_item['ID_COD']),
                                "nome": str(dados_item['DESCRICAONF']),
                                "peso": str(dados_item.get('GRAMAT', '-')) if pd.notna(dados_item.get('GRAMAT')) else '-',
                                "cx": str(dados_item.get('CX_EMB', '')) if pd.notna(dados_item.get('CX_EMB')) else '',
                                "preco": float(dados_item.get('PRECO', 0)) if pd.notna(dados_item.get('PRECO')) else 0.0,
                                "marca": str(dados_item.get('LINHA', 'N/A')),
                                "gramat": str(dados_item.get('GRAMAT', 'N/A'))
                            }
                            st.rerun()
            
            # Verificar se tem produto selecionado
            if f"prod_{i}" in st.session_state.produtos_selecionados:
                produto = st.session_state.produtos_selecionados[f"prod_{i}"]
                
                st.success(f"✅ **Produto:** {produto['nome']}")
                st.caption(f"📦 **Código:** {produto['cod']} | **Marca:** {produto['marca']} | **Gramatura:** {produto['gramat']}")
                
                # Labels das colunas
                col_peso, col_cx, col_qtd, col_preco, col_total, col_rem = st.columns([1.5, 1.5, 1.2, 1.8, 1.8, 0.8])
                
                col_peso.markdown("**Peso**")
                col_cx.markdown("**Cx Embarque**")
                col_qtd.markdown("**Qtde**")
                col_preco.markdown("**Valor Unit.**")
                col_total.markdown("**Total**")
                
                # Inputs - usar valores do produto salvo
                col_peso2, col_cx2, col_qtd2, col_preco2, col_total2, col_rem2 = st.columns([1.5, 1.5, 1.2, 1.8, 1.8, 0.8])
                
                # Criar key única baseada no código do produto para forçar recriação dos widgets
                key_suffix = produto['cod']
                
                peso = col_peso2.text_input(
                    "Peso", 
                    value=produto['peso'], 
                    key=f"peso_{i}_{key_suffix}", 
                    label_visibility="collapsed"
                )
                
                cx_e = col_cx2.text_input(
                    "Cx", 
                    value=produto['cx'], 
                    key=f"cx_{i}_{key_suffix}", 
                    label_visibility="collapsed"
                )
                
                qtd = col_qtd2.number_input(
                    "Qtd", 
                    min_value=1, 
                    value=1, 
                    key=f"qtd_{i}_{key_suffix}", 
                    label_visibility="collapsed"
                )
                
                pr_u = col_preco2.number_input(
                    "Preço", 
                    value=produto['preco'], 
                    key=f"preco_{i}_{key_suffix}", 
                    format="%.2f", 
                    label_visibility="collapsed"
                )
                
                sub = pr_u * qtd
                total_proposta += sub
                
                col_total2.metric("", f"R$ {sub:,.2f}")
                
                itens_final.append({
                    "COD": produto['cod'], 
                    "PRODUTO": produto['nome'],
                    "PESO": peso,
                    "CX": cx_e, 
                    "QTDE": qtd,
                    "VALOR": pr_u, 
                    "TOTAL": sub
                })
                
                if col_rem2.button("🗑️", key=f"rem_{i}"):
                    st.session_state.carrinho.pop(i)
                    if f"prod_{i}" in st.session_state.produtos_selecionados:
                        del st.session_state.produtos_selecionados[f"prod_{i}"]
                    st.rerun()
            else:
                # Botão remover mesmo sem produto selecionado
                if st.button("🗑️ Remover Item", key=f"rem_empty_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()
            
            st.divider()

        # ========== RESUMO E AÇÕES ==========
        st.markdown(f"### 💰 Total da Proposta: R$ {total_proposta:,.2f}")
        st.caption(f"📦 Total de itens: {len(itens_final)}")

        if itens_final and st.session_state.dados_cliente.get('razao_social'):
            col_pdf, col_wa, col_limpar = st.columns(3)
            
            # Gerar PDF
            if col_pdf.button("📄 Gerar PDF da Proposta", use_container_width=True, type="primary"):
                pdf_buffer = gerar_pdf_proposta(
                    st.session_state.dados_cliente, 
                    st.session_state.dados_pedido,
                    itens_final, 
                    total_proposta
                )
                st.download_button(
                    label="⬇️ Baixar Proposta em PDF",
                    data=pdf_buffer,
                    file_name=f"Proposta_MedTextil_{st.session_state.dados_cliente['razao_social'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # WhatsApp
            if col_wa.button("📱 Enviar via WhatsApp", use_container_width=True):
                texto_wa = f"Olá! Segue proposta comercial MedTextil para {st.session_state.dados_cliente['razao_social']} no valor de R$ {total_proposta:,.2f}"
                st.markdown(f"[🔗 Clique para enviar no WhatsApp](https://wa.me/?text={texto_wa})")
            
            # Limpar pedido
            if col_limpar.button("🗑️ Limpar Pedido", use_container_width=True):
                st.session_state.carrinho = []
                st.session_state.dados_cliente = {}
                st.session_state.dados_pedido = {}
                st.rerun()
        else:
            if not st.session_state.dados_cliente.get('razao_social'):
                st.warning("⚠️ Preencha os dados do cliente para gerar a proposta")
            if not itens_final:
                st.info("ℹ️ Adicione itens ao pedido para gerar a proposta")

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
