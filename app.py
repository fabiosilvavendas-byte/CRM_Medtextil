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
                else: df.rename(columns={df.columns[0]: 'ID_COD'}, inplace=True)

        produtos['ID_COD'] = produtos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        precos['ID_COD'] = precos['ID_COD'].astype(str).str.replace('.0', '', regex=False).str.strip()
        Dashboard['DataEmissao'] = pd.to_datetime(Dashboard['DataEmissao'], errors='coerce')
        
        return Dashboard, produtos, precos, expansao
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}")
        return None, None, None, None

Dashboard, produtos, precos, expansao = carregar_dados()
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# ===============================
# 3. INTERFACE E NAVEGAÇÃO
# ===============================
st.sidebar.title("🛡️ MEDTEXTIL CRM")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🛒 Pedidos", "🚨 Inatividade", "🚀 Expansão PR"])

if Dashboard is not None:
    # MÓDULO 1: Dashboard (Mantido conforme consolidado)
    if menu == "📊 Dashboard":
        st.title("📊 Dashboard de Performance")
        st.info("Filtros ativos na barra lateral.")

    # ---------------------------
    # MÓDULO 2: PEDIDOS (Sincronização e Layout PDF)
    # ---------------------------
    elif menu == "🛒 Pedidos":
        st.title("🛒 Emissão de Proposta Comercial")

        # 1. DADOS DO CLIENTE (Baseado no Modelo PDF)
        with st.container(border=True):
            st.subheader("📋 Informações da Proposta")
            c1, c2, c3 = st.columns(3)
            ped_num = c1.text_input("Pedido Nº", value="001")
            cond_pagto = c2.text_input("Condições de Pagto", value="A combinar")
            frete_tipo = c3.selectbox("Tipo de Frete", ["CIF", "FOB"])
            
            sel_cli = st.selectbox("Buscar Cliente na Base", [""] + sorted(Dashboard['RazaoSocial'].unique()))
            
            dados_c = {"nome": "", "cnpj": "", "fone": "", "email": "", "end": "", "fantasia": ""}
            if sel_cli:
                inf = Dashboard[Dashboard['RazaoSocial'] == sel_cli].iloc[0]
                dados_c = {
                    "nome": sel_cli, "cnpj": str(inf.get('CNPJ', '')),
                    "fone": str(inf.get('Telefone', '')), "email": str(inf.get('Email', '')),
                    "end": f"{inf.get('Endereço', '')}, {inf.get('Cidade', '')}",
                    "fantasia": str(inf.get('Nome Fantasia', ''))
                }
            else:
                c1, c2 = st.columns(2)
                dados_c['nome'] = c1.text_input("Razão Social")
                dados_c['cnpj'] = c2.text_input("CNPJ")

        st.divider()

        # 2. ITENS COM CÓDIGO MESTRE
        df_base = produtos.merge(precos[['ID_COD', 'PRECO', 'LINHA', 'GRAMAT']], on='ID_COD', how='left')
        df_base['PRECO'] = df_base['PRECO'].fillna(0.0)

        if st.button("➕ Adicionar Produto"):
            st.session_state.carrinho.append({"id": datetime.now().timestamp()})
            st.rerun()

        total_final = 0.0
        itens_pdf = []

        for i, item in enumerate(st.session_state.carrinho):
            with st.container(border=True):
                col_cod, col_prod, col_cx, col_pr, col_qtd, col_tot = st.columns([1.5, 3.5, 1, 1.2, 1, 1.2])
                
                # Seleção do Código (O MESTRE)
                cod_sel = col_cod.selectbox("Cód.", sorted(df_base['ID_COD'].unique()), key=f"c_{i}")
                
                # Filtro dinâmico: ao alterar o código, pegamos os dados da linha
                row = df_base[df_base['ID_COD'] == cod_sel].iloc[0]
                
                # Campos sincronizados
                desc_p = col_prod.text_input("Produto", value=row['DESCRICAONF'], key=f"d_{i}")
                cx_p = col_cx.text_input("Caixa", value=str(row.get('CX_EMB', 1)), key=f"x_{i}")
                pr_p = col_pr.number_input("Valor", value=float(row['PRECO']), format="%.2f", key=f"v_{i}")
                qtd_p = col_qtd.number_input("Qtd", min_value=1, value=1, key=f"q_{i}")
                
                sub = pr_p * qtd_p
                total_final += sub
                col_tot.metric("Total", f"R$ {sub:,.2f}")

                itens_pdf.append({
                    "COD": cod_sel, "PROD": desc_p, "PESO": row['GRAMAT'], 
                    "CX": cx_p, "QTDE": qtd_p, "VAL": pr_p, "TOT": sub
                })
                if st.button("🗑️", key=f"r_{i}"):
                    st.session_state.carrinho.pop(i); st.rerun()

        # 3. LAYOUT FIEL AO MODELO PROPOSTA.PDF
        if total_final > 0:
            st.subheader(f"Total: R$ {total_final:,.2f}")
            
            html_proposta = f"""
            <div id="proposta-fiel" style="font-family: 'Helvetica', sans-serif; padding: 30px; border: 1px solid #ccc; max-width: 900px; margin: auto;">
                <div style="text-align: center; border-bottom: 3px solid #d32f2f; padding-bottom: 10px;">
                    <h1 style="margin:0; color: #d32f2f; letter-spacing: 2px;">MEDTEXTIL</h1>
                    <p style="margin:0; font-size: 13px; font-weight: bold;">produto têxtil hospitalar</p>
                    <p style="margin:5px 0; font-size: 11px;">ULTRA TEXTIL INDUSTRIA E COMERCIO DE PRODUTOS HOSPITALARES LTDA</p>
                    <p style="margin:0; font-size: 10px;">40.357.820/0001-50 | comercial.ultratextilpb@gmail.com | (83) 3233-9798</p>
                    <p style="margin:0; font-size: 10px;">RY DOIS, 355-GALPÃO 3 - Distrito Industrial - João Pessoa - PB</p>
                </div>

                <div style="margin-top: 20px; font-size: 11px; line-height: 1.5;">
                    <table style="width: 100%;">
                        <tr>
                            <td style="width: 50%; vertical-align: top;">
                                <strong>Representante legal:</strong> Rosselic Marinho<br>
                                <strong>CPF:</strong> 338.610.054-68 | <strong>RG:</strong> 745858-SSP-PB
                            </td>
                            <td style="width: 50%; border-left: 1px solid #eee; padding-left: 15px;">
                                <strong>INFORMAÇÕES DO CLIENTE</strong><br>
                                <strong>Cliente:</strong> {dados_c['nome']}<br>
                                <strong>CNPJ:</strong> {dados_c['cnpj']} | <strong>Fone:</strong> {dados_c['fone']}<br>
                                <strong>Endereço:</strong> {dados_c['end']}
                            </td>
                        </tr>
                    </table>
                </div>

                <div style="margin-top: 15px; background: #f9f9f9; padding: 8px; border: 1px solid #ddd; font-size: 11px;">
                    <strong>Pedido Nº:</strong> {ped_num} | <strong>Pagamento:</strong> {cond_pagto} | <strong>Frete:</strong> {frete_tipo} | <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y')}
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px;">
                    <thead>
                        <tr style="background: #d32f2f; color: white;">
                            <th style="padding: 6px; border: 1px solid #000;">COD.</th>
                            <th style="padding: 6px; border: 1px solid #000; text-align: left;">PRODUTO</th>
                            <th style="padding: 6px; border: 1px solid #000;">PESO</th>
                            <th style="padding: 6px; border: 1px solid #000;">CX EMB.</th>
                            <th style="padding: 6px; border: 1px solid #000;">QTDE</th>
                            <th style="padding: 6px; border: 1px solid #000; text-align: right;">VALOR</th>
                            <th style="padding: 6px; border: 1px solid #000; text-align: right;">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f"<tr><td style='border:1px solid #000; padding:5px; text-align:center;'>{it['COD']}</td><td style='border:1px solid #000; padding:5px;'>{it['PROD']}</td><td style='border:1px solid #000; padding:5px; text-align:center;'>{it['PESO']}</td><td style='border:1px solid #000; padding:5px; text-align:center;'>{it['CX']}</td><td style='border:1px solid #000; padding:5px; text-align:center;'>{it['QTDE']}</td><td style='border:1px solid #000; padding:5px; text-align:right;'>R$ {it['VAL']:.2f}</td><td style='border:1px solid #000; padding:5px; text-align:right;'>R$ {it['TOT']:.2f}</td></tr>" for it in itens_pdf])}
                    </tbody>
                </table>

                <div style="text-align: right; margin-top: 15px;">
                    <h2 style="margin:0; color: #d32f2f;">TOTAL DA PROPOSTA: R$ {total_final:,.2f}</h2>
                </div>

                <div style="margin-top: 30px; font-size: 9px; border-top: 1px solid #000; padding-top: 10px; color: #666;">
                    <strong>CONDIÇÕES GERAIS:</strong> Prazo de entrega: 30 dias | Validade da Proposta: 60 dias | Garantia: 5 dias úteis.
                </div>
            </div>
            """

            c_print, c_wa = st.columns(2)
            with c_print:
                if st.button("🖨️ GERAR PDF / IMPRIMIR"):
                    components.html(f"{html_proposta}<script>window.onload = function() {{ window.print(); }}</script>", height=800, scrolling=True)
            with c_wa:
                msg = f"Olá, segue proposta MedTextil no valor de R$ {total_final:,.2f}"
                st.link_button("📱 ENVIAR WHATSAPP", f"https://wa.me/{dados_c['fone']}?text={msg}")

    # MÓDULOS 3 E 4 (Mantidos consolidados)
    elif menu == "🚨 Inatividade":
        st.title("🚨 Inatividade")
        # ... lógica consolidada ...
    elif menu == "🚀 Expansão PR":
        st.title("🚀 Expansão PR")
        # ... lógica consolidada ...
