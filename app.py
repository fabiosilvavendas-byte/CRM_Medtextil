import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA (Mantendo o ícone para o app no iPhone)
st.set_page_config(
    page_title="CRM MedTextil - Pro", 
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
        Dashboard = pd.read_excel("dados/CONSULTA_VENDEDORES.xlsx")
        
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

# ===============================
# 3. INTERFACE E NAVEGAÇÃO
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🧾 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"])

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
    # MÓDULO 2: PEDIDOS (SISTEMA INTEGRAL)
    # ---------------------------
    if menu == "🛒 Pedidos":  # Verifique se o seu IF inicial é este
    df_comb = (
        produtos
            .merge(precos[['ID_COD', 'PRECO']], on='ID_COD', how='left')
            .merge(tabelas_ne[['ID_COD', 'LINHA', 'GRAMAT']], on='ID_COD', how='left')
        )

        df_comb['PRECO'] = df_comb['PRECO'].fillna(0.0)
        df_comb['LINHA'] = df_comb['LINHA'].fillna('')
        df_comb['GRAMAT'] = df_comb['GRAMAT'].fillna('')

        df_comb['DISPLAY'] = (
            df_comb['ID_COD'].astype(str)
            + " | "
            + df_comb['DESCRICAONF'].astype(str)
        )

        total_proposta = 0.0
        itens_final = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container():
                c_busca, c_cx, c_pr, c_qtd = st.columns([4, 1, 1, 1])

                escolha = c_busca.selectbox(
                    f"Item {i+1}",
                    options=sorted(df_comb['DISPLAY'].unique()),
                    key=f"sel_{i}"
                )

                if escolha:
                    dados_item = df_comb[df_comb['DISPLAY'] == escolha].iloc[0]

                    st.caption(
                        f"**Marca:** {dados_item['LINHA']} | "
                        f"**Gramatura:** {dados_item['GRAMAT']}"
                    )

                    cx_e = c_cx.text_input("Cx", value=dados_item['CX_EMB'], key=f"x_{i}")
                    pr_u = c_pr.number_input("Unit.", value=float(dados_item['PRECO']), key=f"p_{i}")
                    qtd = c_qtd.number_input("Qtd", min_value=1, value=1, key=f"q_{i}")

                    sub = pr_u * qtd
                    total_proposta += sub

                    itens_final.append({
                        "COD": dados_item['ID_COD'],
                        "PRODUTO": dados_item['DESCRICAONF'],
                        "MARCA": dados_item['LINHA'],
                        "GRAMATURA": dados_item['GRAMAT'],
                        "CX": cx_e,
                        "QTDE": qtd,
                        "VALOR": pr_u,
                        "TOTAL": sub
                    })

                if st.button(f"🗑️ Remover {i+1}", key=f"btn_rem_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()

        st.divider()

    # ---------------------------
    # MÓDULO 3: INATIVIDADE
    # ---------------------------
    elif menu == "🚨 Inatividade":
        st.title("🚨 Inatividade")
        with st.sidebar:
            vendedores_inat = sorted(
                [str(x) for x in vendas['Vendedor'].unique() if pd.notna(x)]
            )
            v_inat = st.multiselect(
                "Vendedores", vendedores_inat, default=vendedores_inat
            )
            d_limite = st.number_input(
                "Dias Limite", min_value=1, value=60
            )

        df_i = vendas[vendas['Vendedor'].isin(v_inat)].copy()
        if not df_i.empty:
            res = (
                df_i
                .groupby(['RazaoSocial', 'Vendedor', 'Estado'])
                .agg({'DataEmissao': 'max', 'TotalProduto2': 'sum'})
                .reset_index()
            )
            res['Dias_Inativo'] = (
                datetime.now() - res['DataEmissao']
            ).dt.days
            final = res[
                res['Dias_Inativo'] >= d_limite
            ].sort_values('Dias_Inativo', ascending=False)

            st.dataframe(final, use_container_width=True)

    # ---------------------------
    # MÓDULO 4: NOVO - EXPANSÃO PR (BASEADO NO RELATÓRIO)
    # ---------------------------
    # ---------------------------
    # MÓDULO 4: EXPANSÃO PR (INTERATIVO - COM PREENCHIMENTO)
    # ---------------------------
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Plano de Expansão PR 2026")
        
        # Inicializa a base de leads no estado da sessão se ainda não existir
        if "df_leads_ativa" not in st.session_state:
            if expansao and 'Gestão de Leads' in expansao:
                st.session_state.df_leads_ativa = expansao['Gestão de Leads'].copy()
            else:
                st.session_state.df_leads_ativa = pd.DataFrame(columns=["Data de Entrada", "Empresa", "Cidade", "Segmento", "Contato", "Status do Lead", "Dor Principal"])

        # Abas para organizar o trabalho no iPhone
        tab_view, tab_add, tab_edit = st.tabs(["📋 Visualizar Leads", "➕ Novo Lead", "📈 Atualizar Funil"])

        with tab_view:
            st.subheader("Base de Leads Atual")
            st.dataframe(st.session_state.df_leads_ativa, use_container_width=True, hide_index=True)
            
            # Botão para baixar o que foi preenchido (como CSV) para você não perder o trabalho
            if not st.session_state.df_leads_ativa.empty:
                csv = st.session_state.df_leads_ativa.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Baixar Leads Atualizados", csv, "leads_expansao_atualizado.csv", "text/csv")

        with tab_add:
            st.subheader("Cadastrar Nova Oportunidade")
            with st.form("novo_lead_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                empresa_n = col1.text_input("Nome da Empresa")
                cidade_n = col2.text_input("Cidade")
                segmento_n = col1.selectbox("Segmento", ["Hospitalar", "Distribuidora", "Clínica", "Público"])
                contato_n = col2.text_input("Contato Principal")
                dor_n = st.text_area("Necessidade/Dor do Cliente")
                
                submit = st.form_submit_button("✅ Salvar Lead no Aplicativo")
                
                if submit:
                    if empresa_n:
                        novo_registro = {
                            "Data de Entrada": datetime.now().strftime("%d/%m/%Y"),
                            "Empresa": empresa_n,
                            "Cidade": cidade_n,
                            "Segmento": segmento_n,
                            "Contato": contato_n,
                            "Status do Lead": "Prospecção",
                            "Dor Principal": dor_n
                        }
                        # Adiciona ao DataFrame em memória
                        st.session_state.df_leads_ativa = pd.concat([st.session_state.df_leads_ativa, pd.DataFrame([novo_registro])], ignore_index=True)
                        st.success(f"Lead {empresa_n} adicionado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Por favor, preencha pelo menos o nome da Empresa.")

        with tab_edit:
            st.subheader("Gestão de Funil e KPIs")
            if not st.session_state.df_leads_ativa.empty:
                # Mini Dashboard com os dados que você acabou de preencher
                c1, c2 = st.columns(2)
                c1.metric("Total de Leads", len(st.session_state.df_leads_ativa))
                
                # Interface simples de atualização
                st.divider()
                empresa_edit = st.selectbox("Selecionar Lead para Follow-up", st.session_state.df_leads_ativa['Empresa'].unique())
                status_edit = st.select_slider("Alterar Status", options=["Prospecção", "Qualificação", "Proposta", "Negociação", "Fechamento"])
                obs_edit = st.text_input("Última Interação")
                
                if st.button("Atualizar Histórico"):
                    st.toast(f"Status de {empresa_edit} atualizado!", icon="🚀")
            else:
                st.info("Cadastre leads na aba ao lado para gerenciar o funil.")










