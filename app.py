import os
from pathlib import Path
import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    # Define o caminho para a pasta 'dados' relativa ao arquivo app.py
    # Path(__file__).parent garante que ele comece onde o script está
    caminho_dados = Path(__file__).parent / "dados"

    # Lista dos nomes exatos dos arquivos
    # ATENÇÃO: Verifique se as extensões (.xlsx ou .xls) e maiúsculas estão idênticas
    try:
        df_vendas = pd.read_excel(caminho_dados / "CONSULTA_VENDEDORES.xlsx")
        df_produtos = pd.read_excel(caminho_dados / "Produtos_Agrupados_Completos_conciliados.xlsx")
        df_tabela = pd.read_excel(caminho_dados / "TABELAS_NE.xlsx")
        # Para o arquivo .xls, usamos o motor 'xlrd'
        df_inad = pd.read_excel(caminho_dados / "XLS_Grid_LANCAMENTO A RECEBER.xls", engine='xlrd')
    except FileNotFoundError as e:
        st.error(f"Erro: O sistema não encontrou o arquivo dentro da pasta 'dados'. Detalhes: {e}")
        st.stop()

    # --- Processamento e Conciliação (Mantendo suas regras) ---
    df_vendas['CodigoProduto'] = df_vendas['CodigoProduto'].astype(str)
    df_produtos['ID_COD'] = df_produtos['ID_COD'].astype(str)
    df_tabela['ID_COD'] = df_tabela['ID_COD'].astype(str)

    # Join das tabelas
    df_master = pd.merge(df_vendas, df_produtos, left_on='CodigoProduto', right_on='ID_COD', how='left')
    df_master = pd.merge(df_master, df_tabela[['ID_COD', 'PRECO']], on='ID_COD', how='left')
    
    return df_master, df_inad, df_produtos, df_tabela

# Execução
df_master, df_inad, df_produtos, df_tabela = load_data()
