import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. CONFIGURAÇÃO DA PÁGINA (Mantendo padrões Web que funcionam)
st.set_page_config(
    page_title="CRM MedTextil - Pro", 
    layout="wide", 
    page_icon="🛡️"
)

# ===============================
# 2. CARREGAMENTO DOS DADOS (CONSOLIDADO)
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
    # MÓDULO 1: Dashboard GERAL (CONSOLIDADO)
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
    # MÓDULO 2: PEDIDOS (ALTERAÇÃO SOLICITADA)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Emissão de Proposta Comercial")

        # SEÇÃO CLIENTE
        st.subheader("👤 Dados do Cliente")
        modo_c = st.radio("Origem", ["Base de Dados", "Cadastro Manual"], horizontal=True)
        dados_c = {"nome": "", "cnpj": "", "end": "", "fone": "", "email": "", "fantasia": ""}

        if modo_c == "Base de Dados":
            lista_clientes = sorted(Dashboard['RazaoSocial'].unique())
            sel_cli = st.selectbox("Selecione o Cliente", [""] + lista_clientes)
            if sel_cli:
                inf = Dashboard[Dashboard['RazaoSocial'] == sel_cli].iloc[0]
                dados_c = {
                    "nome": sel_cli, "cnpj": str(inf.get('CNPJ', 'S/I')),
                    "end": f"{inf.get('Endereço', 'S/I')}, {inf.get('Cidade', '')}",
                    "fone": str(inf.get('Telefone', 'S/I')), "email": str(inf.get('Email', 'S/I')),
                    "fantasia": str(inf.get('Nome Fantasia', 'S/I'))
                }
        else:
            c1, c2 = st.columns(2)
            dados_c['nome'] = c1.text_input("Razão Social")
            dados_c['cnpj'] = c2.text_input("CNPJ")
            dados_c['end'] = c1.text_input("Endereço Completo")
            dados_c['fone'] = c2.text_input("Telefone")

        st.divider()

        # LOGICA DE SINCRONIZAÇÃO DE PRODUTOS
        df_base = produtos.merge(precos[['ID_COD', 'PRECO', 'LINHA', 'GRAMAT']], on='ID_COD', how='left')
        df_base['PRECO'] = df_base['PRECO'].fillna(0.0)

        st.subheader("📦 Itens")
        if st.button("➕ Adicionar Item"):
            st.session_state.carrinho.append({"id": datetime.now().timestamp()})
            st.rerun()

        total_final = 0.0
        itens_pdf = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container(border=True):
                col_cod, col_prod, col_cx, col_pr, col_qtd, col_tot = st.columns([1.5, 3.5, 1, 1.5, 1, 1.5])
                
                # CÓDIGO É O FILTRO MESTRE
                cod_sel = col_cod.selectbox("Cód.", sorted(df_base['ID_COD'].unique()), key=f"c_{i}")
                
                # Busca automática baseada no código
                row = df_base[df_base['ID_COD'] == cod_sel].iloc[0]
                
                # Preenchimento automático sincronizado
                desc_p = col_prod.text_input("Produto", value=row['DESCRICAONF'], key=f"d_{i}")
                cx_p = col_cx.text_input("Cx", value=str(row.get('CX_EMB', 1)), key=f"x_{i}")
                pr_p = col_pr.number_input("Preço", value=float(row['PRECO']), format="%.2f", key=f"p_{i}")
                qtd_p = col_qtd.number_input("Qtd", min_value=1, value=1, key=f"q_{i}")
                
                sub = pr_p * qtd_p
                total_final += sub
                col_tot.metric("Subtotal", f"R$ {sub:,.2f}")

                itens_pdf.append({
                    "COD": cod_sel, "PROD": desc_p, "GRAM": row['GRAMAT'], 
                    "CX": cx_p, "QTDE": qtd_p, "VALOR": pr_p, "TOTAL": sub
                })

                if st.button("🗑️", key=f"rem_{i}"):
                    st.session_state.carrinho.pop(i)
                    st.rerun()

        # LAYOUT DE IMPRESSÃO (BASEADO NO MODELO PDF)
        if total_final > 0:
            st.subheader(f"Total: R$ {total_final:,.2f}")
            c1, c2 = st.columns(2)
            
            html_print = f"""
            <div id="proposta" style="font-family: Arial; padding: 20px; border: 1px solid #000;">
                <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px;">
                    <h2 style="margin:0; color: #d32f2f;">MEDTEXTIL</h2>
                    <p style="margin:0; font-size: 12px;">ULTRA TEXTIL IND E COM DE PROD HOSP LTDA | 40.357.820/0001-50</p>
                    <p style="margin:0; font-size: 11px;">comercial.ultratextilpb@gmail.com | (83) 3233-9798</p>
                    <h3 style="background: #eee; border: 1px solid #000; margin-top: 10px;">PROPOSTA COMERCIAL</h3>
                </div>
                <div style="margin: 15px 0; font-size: 12px;">
                    <strong>Representante:</strong> Rosselic Marinho | <strong>CPF:</strong> 338.610.054-68<br><br>
                    <strong>CLIENTE:</strong> {dados_c['nome']}<br>
                    <strong>CNPJ:</strong> {dados_c['cnpj']} | <strong>FONE:</strong> {dados_c['fone']}<br>
                    <strong>ENDEREÇO:</strong> {dados_c['end']}
                </div>
                <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                    <thead>
                        <tr style="background: #eee; border: 1px solid #000;">
                            <th>COD</th><th>PRODUTO</th><th>GRAMAT.</th><th>CX</th><th>QTDE</th><th>VALOR</th><th>TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f"<tr><td style='border:1px solid #000; padding:4px;'>{it['COD']}</td><td style='border:1px solid #000; padding:4px;'>{it['PROD']}</td><td style='border:1px solid #000; padding:4px;'>{it['GRAM']}</td><td style='border:1px solid #000; padding:4px; text-align:center;'>{it['CX']}</td><td style='border:1px solid #000; padding:4px; text-align:center;'>{it['QTDE']}</td><td style='border:1px solid #000; padding:4px; text-align:right;'>R$ {it['VALOR']:.2f}</td><td style='border:1px solid #000; padding:4px; text-align:right;'>R$ {it['TOTAL']:.2f}</td></tr>" for it in itens_pdf])}
                    </tbody>
                </table>
                <h3 style="text-align: right;">TOTAL FINAL: R$ {total_final:,.2f}</h3>
                <div style="font-size: 10px; margin-top: 20px; border-top: 1px solid #000;">
                    <strong>DECLARAÇÕES:</strong> Prazo: 30 dias | Validade: 60 dias | Garantia: 05 dias.
                </div>
            </div>
            """

            with c1:
                if st.button("🖨️ IMPRIMIR / PDF"):
                    components.html(f"{html_print}<script>window.onload = function() {{ window.print(); }}</script>", height=600, scrolling=True)
            with c2:
                link_wa = f"https://wa.me/{dados_c['fone'].replace('(','').replace(')','').replace('-','').replace(' ','')}?text=Proposta MedTextil: R$ {total_final:.2f}"
                st.link_button("📱 ENVIAR WHATSAPP", link_wa)

    # ---------------------------
    # MÓDULO 3: INATIVIDADE (CONSOLIDADO)
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
    # MÓDULO 4: EXPANSÃO PR (CONSOLIDADO)
    # ---------------------------
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Plano de Expansão PR 2026")
        if "df_leads_ativa" not in st.session_state:
            if expansao and 'Gestão de Leads' in expansao:
                st.session_state.df_leads_ativa = expansao['Gestão de Leads'].copy()
            else:
                st.session_state.df_leads_ativa = pd.DataFrame(columns=["Data", "Empresa", "Status"])
        
        st.dataframe(st.session_state.df_leads_ativa, use_container_width=True)
