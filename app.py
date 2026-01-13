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

# =================================================================
# FUNÇÃO DE CALLBACK PARA O FILTRO MESTRE (SOLUÇÃO DEFINITIVA)
# =================================================================
def atualizar_item_carrinho(indice):
    chave_sel = f"sel_{indice}"
    if chave_sel in st.session_state:
        escolha = st.session_state[chave_sel]
        # Busca os dados no dataframe global que preparamos abaixo
        dados = df_comb_global[df_comb_global['DISPLAY'] == escolha].iloc[0]
        st.session_state.carrinho[indice].update({
            "display": escolha,
            "cod": dados['ID_COD'],
            "desc": dados['DESCRICAONF'],
            "peso": str(dados.get('GRAMAT', '')),
            "cx": str(dados.get('CX_EMB', 1)),
            "pr": float(dados['PRECO'])
        })

# ===============================
# 2. CARREGAMENTO DOS DADOS (SISTEMA ROBUSTO)
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
if "clientes_novos" not in st.session_state: st.session_state.clientes_novos = []

# Preparação de dados para o Módulo de Pedidos (Global)
cols_p = ['ID_COD', 'PRECO']
if 'GRAMAT' in precos.columns: cols_p.append('GRAMAT')
df_comb_global = produtos.merge(precos[cols_p], on='ID_COD', how='left').fillna({'PRECO':0, 'GRAMAT':''})
df_comb_global['DISPLAY'] = df_comb_global['ID_COD'].astype(str) + " | " + df_comb_global['DESCRICAONF'].astype(str)

# ===============================
# 3. INTERFACE E NAVEGAÇÃO
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🛒 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"])

if Dashboard is not None:
    # ---------------------------
    # MÓDULO 1: Dashboard GERAL (MANTIDO)
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
    # MÓDULO 2: PEDIDOS (COM TÉCNICA DE CALLBACK)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Pedidos")
        opcoes = sorted(df_comb_global['DISPLAY'].unique())

        with st.container(border=True):
            st.subheader("👤 Cliente")
            sel_cli = st.selectbox("Buscar Cliente", [""] + sorted(Dashboard['RazaoSocial'].unique()))
            d_cli = {"n": "", "c": "", "f": "", "e": ""}
            if sel_cli:
                inf = Dashboard[Dashboard['RazaoSocial'] == sel_cli].iloc[0]
                d_cli = {"n": sel_cli, "c": str(inf.get('CNPJ', '')), "f": str(inf.get('Telefone', '')), "e": str(inf.get('Endereço', ''))}
            c1, c2 = st.columns(2)
            cli_n = c1.text_input("Razão Social", value=d_cli['n'])
            cli_c = c2.text_input("CNPJ", value=d_cli['c'])

        if st.button("➕ Adicionar Item"):
            prim = df_comb_global[df_comb_global['DISPLAY'] == opcoes[0]].iloc[0]
            st.session_state.carrinho.append({
                "display": opcoes[0], "cod": prim['ID_COD'], "desc": prim['DESCRICAONF'],
                "peso": str(prim.get('GRAMAT', '')), "cx": "1", "pr": float(prim['PRECO']), "qtd": 1
            })
            st.rerun()

        total_p = 0.0
        itens_pdf = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container(border=True):
                c_sel, c_peso, c_cx, c_pr, c_qtd, c_sub = st.columns([2.5, 0.8, 0.8, 1, 0.8, 1])
                
                # CALLBACK APLICADO AQUI
                idx = opcoes.index(item['display']) if item['display'] in opcoes else 0
                c_sel.selectbox(f"Produto {i+1}", opcoes, index=idx, key=f"sel_{i}", on_change=atualizar_item_carrinho, args=(i,))

                v_peso = c_peso.text_input("Peso", value=item['peso'], key=f"w_{i}")
                v_cx = c_cx.text_input("Cx", value=item['cx'], key=f"x_{i}")
                v_pr = c_pr.number_input("Unit.", value=item['pr'], format="%.2f", key=f"p_{i}")
                v_qtd = c_qtd.number_input("Qtd", min_value=1, value=item['qtd'], key=f"q_{i}")
                
                st.session_state.carrinho[i].update({"peso": v_peso, "cx": v_cx, "pr": v_pr, "qtd": v_qtd})
                sub = v_pr * v_qtd
                total_p += sub
                c_sub.metric("Subtotal", f"R$ {sub:,.2f}")
                
                itens_pdf.append({"COD": item['cod'], "PROD": item['desc'], "PESO": v_peso, "CX": v_cx, "QTD": v_qtd, "VAL": v_pr, "TOT": sub})

                if st.button(f"🗑️ Remover {i+1}", key=f"rem_{i}"):
                    st.session_state.carrinho.pop(i); st.rerun()

        if total_p > 0:
            st.divider()
            if st.button("📄 Gerar Proposta Comercial"):
                html = f"""<div style='font-family: Arial; padding: 20px; border: 1px solid #000; width: 750px; margin: auto;'>
                <h2 style='color: red; text-align: center;'>MEDTEXTIL</h2>
                <p><strong>Representante:</strong> Rosselic Marinho | <strong>Cliente:</strong> {cli_n}</p>
                <table style='width: 100%; border-collapse: collapse; font-size: 11px;'>
                <tr style='background: #eee;'><th>COD</th><th>PRODUTO</th><th>PESO</th><th>CX</th><th>QTDE</th><th>VALOR</th><th>TOTAL</th></tr>
                {"".join([f"<tr><td style='border:1px solid #000;'>{it['COD']}</td><td style='border:1px solid #000;'>{it['PROD']}</td><td style='border:1px solid #000; text-align:center;'>{it['PESO']}</td><td style='border:1px solid #000; text-align:center;'>{it['CX']}</td><td style='border:1px solid #000; text-align:center;'>{it['QTD']}</td><td style='border:1px solid #000;'>R$ {it['VAL']:.2f}</td><td style='border:1px solid #000;'>R$ {it['TOT']:.2f}</td></tr>" for it in itens_pdf])}
                </table><h3 style='text-align: right;'>TOTAL: R$ {total_p:,.2f}</h3></div>"""
                components.html(f"{html}<script>window.print();</script>", height=600)

    # ---------------------------
    # MÓDULO 3: INATIVIDADE (MANTIDO)
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
    # MÓDULO 4: EXPANSÃO PR (MANTIDO)
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
                emp_n = c1.text_input("Empresa"); cid_n = c2.text_input("Cidade")
                seg_n = c1.selectbox("Segmento", ["Hospitalar", "Distribuidora", "Clínica", "Público"])
                con_n = c2.text_input("Contato"); dor_n = st.text_area("Necessidade")
                if st.form_submit_button("✅ Salvar Lead"):
                    if emp_n:
                        novo = {"Data de Entrada": datetime.now().strftime("%d/%m/%Y"), "Empresa": emp_n, "Cidade": cid_n, "Segmento": seg_n, "Contato": con_n, "Status do Lead": "Prospecção", "Dor Principal": dor_n}
                        st.session_state.df_leads_ativa = pd.concat([st.session_state.df_leads_ativa, pd.DataFrame([novo])], ignore_index=True)
                        st.rerun()
        with tab_edit:
            if not st.session_state.df_leads_ativa.empty:
                emp_edit = st.selectbox("Selecionar Lead", st.session_state.df_leads_ativa['Empresa'].unique())
                status_edit = st.select_slider("Alterar Status", options=["Prospecção", "Qualificação", "Proposta", "Negociação", "Fechamento"])
                if st.button("Atualizar Histórico"): st.toast(f"Status de {emp_edit} atualizado!", icon="🚀")
