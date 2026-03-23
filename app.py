import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import requests
from github import Github

# ====================== FUNÇÃO KPI CARD PROFISSIONAL ======================
def render_kpi_card(label, value, delta=None, icon="📊", color="#1F4788"):
    """Renderiza card KPI profissional com HTML/CSS - substitui st.metric()"""
    delta_html = ""
    if delta:
        delta_val = str(delta).replace("%","").replace(",","").replace("+","").strip()
        try:
            delta_color = "#10B981" if float(delta_val) >= 0 else "#EF4444"
        except:
            delta_color = "#10B981" if "+" in str(delta) else "#EF4444"
        delta_html = f'<div style="color:{delta_color};font-size:0.875rem;font-weight:600;margin-top:0.5rem;">{delta}</div>'
    
    st.markdown(f"""
    <div style="background:white;padding:1.5rem;border-radius:15px;
                box-shadow:0 4px 12px rgba(0,0,0,0.05);border-left:4px solid {color};
                height:140px;display:flex;flex-direction:column;justify-content:space-between;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div style="font-size:0.8rem;color:#6B7280;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
            <div style="font-size:1.75rem;">{icon}</div>
        </div>
        <div>
            <div style="font-size:1.75rem;font-weight:700;color:#1F2937;">{value}</div>
            {delta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Configuração da página
st.set_page_config(
    page_title="Dashboard BI Medtextil", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="https://i.imgur.com/gt3rgyL.png"  # Logo Medtextil
)

# ====================== CONFIGURAÇÃO DO ÍCONE ======================
# O Streamlit gerencia automaticamente o ícone via page_icon
# Nenhuma configuração adicional é necessária

# ====================== CSS CUSTOMIZADO - UX/UI PROFISSIONAL ======================
st.markdown("""
<style>
/* ── Importar fonte Inter ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset e fonte base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', Roboto, sans-serif !important;
}

/* ── Fundo cinza muito claro ── */
.stApp {
    background-color: var(--background-color) !important;
}

/* ── Sidebar limpa e profissional ── */
[data-testid="stSidebar"] {
    background: var(--secondary-background-color) !important;
    border-right: 1px solid rgba(128,128,128,0.2) !important;
    box-shadow: 2px 0 8px rgba(0,0,0,0.04) !important;
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #4A7BC8 !important;
}

/* ── Botões de navegação da sidebar estilizados ── */
[data-testid="stSidebar"] [data-testid="stRadio"] {
    gap: 6px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: #F8F9FA !important;
    border: 1px solid #E9ECEF !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    display: block !important;
    width: 100% !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #EEF2F7 !important;
    border-color: #4A7BC8 !important;
    transform: translateX(3px) !important;
}

/* Botão selecionado na sidebar */
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
    background: linear-gradient(135deg, #1F4788 0%, #2D5AA0 100%) !important;
    border-color: #4A7BC8 !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(31, 71, 136, 0.2) !important;
}

/* Esconder radio button padrão */
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}

/* ── Cards de métricas (st.metric) ── */
[data-testid="stMetric"] {
    background: var(--secondary-background-color) !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
    border-left: 4px solid #1F4788 !important;
    box-shadow: 0 2px 8px rgba(31, 71, 136, 0.08), 0 1px 3px rgba(0,0,0,0.04) !important;
    transition: box-shadow 0.2s ease, transform 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 20px rgba(31, 71, 136, 0.14) !important;
    transform: translateY(-2px) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    color: #6C757D !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #4A7BC8 !important;
}

/* ── Cor alternada para cards de destaque ── */
div[data-testid="column"]:nth-child(2) [data-testid="stMetric"] {
    border-left-color: #2E86AB !important;
}
div[data-testid="column"]:nth-child(3) [data-testid="stMetric"] {
    border-left-color: #28A745 !important;
}
div[data-testid="column"]:nth-child(4) [data-testid="stMetric"] {
    border-left-color: #F4A261 !important;
}

/* ── Botões modernos ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.25rem !important;
    border: 1.5px solid #1F4788 !important;
    color: #4A7BC8 !important;
    background: var(--secondary-background-color) !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 4px rgba(31, 71, 136, 0.10) !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: #1F4788 !important;
    color: #FFFFFF !important;
    border-color: #4A7BC8 !important;
    box-shadow: 0 4px 12px rgba(31, 71, 136, 0.25) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: #1F4788 !important;
    color: #FFFFFF !important;
    border-color: #4A7BC8 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #163561 !important;
    border-color: #163561 !important;
}

/* ── Botão de Download ── */
[data-testid="stDownloadButton"] > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    background: var(--secondary-background-color) !important;
    color: #4A7BC8 !important;
    border: 1.5px solid #1F4788 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #1F4788 !important;
    color: #FFFFFF !important;
}

/* ── Cards de navegação (Home) ── */
.stButton > button p {
    font-size: 0.9rem !important;
}

/* ── Títulos de página ── */
.stApp h1 {
    color: #2C5AA0 !important;
    font-weight: 700 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.02em !important;
}
.stApp h2 {
    color: #4A7BC8 !important;
    font-weight: 600 !important;
    font-size: 1.3rem !important;
}
.stApp h3 {
    color: #2E4A7A !important;
    font-weight: 600 !important;
}

/* ── Selectbox e inputs ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stDateInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: 8px !important;
    border-color: #DEE2E6 !important;
    font-size: 0.9rem !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div:focus-within {
    border-color: #4A7BC8 !important;
    box-shadow: 0 0 0 2px rgba(31, 71, 136, 0.15) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--secondary-background-color) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border-bottom: none !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    color: #6C757D !important;
    padding: 6px 16px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #1F4788 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ── Dataframes / tabelas ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}

/* ── Divisores ── */
hr {
    border-color: #E9ECEF !important;
    margin: 1rem 0 !important;
}

/* ── Alertas e info boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Sidebar logo area ── */
.sidebar-logo-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 8px 8px 8px;
    border-bottom: 1px solid #E9ECEF;
    margin-bottom: 12px;
}
.sidebar-user-badge {
    background: #F0F4FF;
    border: 1px solid #C5D5F0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.85rem;
    color: #4A7BC8;
    font-weight: 600;
    width: 100%;
    text-align: center;
    margin-top: 8px;
}

/* ── Barra de filtros no topo ── */
.filter-bar {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border: 1px solid #E9ECEF;
}

/* ── Cabeçalho da página ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.page-subtitle {
    color: #6C757D;
    font-size: 0.9rem;
    margin-bottom: 20px;
    margin-top: -4px;
}

/* ── Radio buttons estilo pill ── */
.stRadio > div {
    flex-direction: row !important;
    gap: 8px !important;
}
.stRadio > div label {
    border-radius: 20px !important;
    padding: 4px 14px !important;
    border: 1.5px solid #DEE2E6 !important;
    font-size: 0.875rem !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
}
.stRadio > div label:has(input:checked) {
    background: #1F4788 !important;
    color: #FFFFFF !important;
    border-color: #4A7BC8 !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #4A7BC8 !important;
}

/* ── Sidebar navigation radio ── */
[data-testid="stSidebar"] .stRadio > div {
    flex-direction: column !important;
    gap: 4px !important;
}
[data-testid="stSidebar"] .stRadio > div label {
    border-radius: 10px !important;
    padding: 11px 14px !important;
    border: none !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    color: #495057 !important;
    background: transparent !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stRadio > div label:has(input:checked) {
    background: linear-gradient(135deg, #F0F4FF, #E4EDFC) !important;
    color: #4A7BC8 !important;
    border-left: 4px solid #1F4788 !important;
    border-radius: 0 10px 10px 0 !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(31,71,136,0.10) !important;
}
[data-testid="stSidebar"] .stRadio > div label:hover {
    background: #F4F7FD !important;
    color: #4A7BC8 !important;
    transform: translateX(2px) !important;
}

/* ── Success/warning/error messages ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 8px !important;
    font-size: 0.875rem !important;
}

/* ── Métricas: rótulo uppercase corporativo ── */
[data-testid="stMetricLabel"] p {
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    color: #8A96A8 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: #2C5AA0 !important;
}

/* ── Subheaders sem emoji weight ── */
h2, h3 {
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}

/* ── Expander painel de controle ── */
[data-testid="stExpander"] summary {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #6C757D !important;
}

/* ── Captions dos filtros ── */
.stCaption p {
    font-size: 0.7rem !important;
    color: #8A96A8 !important;
    margin-top: -4px !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
}


/* ══════════════════════════════════════════════════════
   DARK MODE — sobrescreve cores fixas quando o tema
   escuro está ativo. Usa prefers-color-scheme E o
   atributo data-theme que o Streamlit injeta no <body>.
   ══════════════════════════════════════════════════════ */

/* Detectar dark mode via atributo do Streamlit */
@media (prefers-color-scheme: dark) {
    .stApp { background-color: #0E1117 !important; }
}

/* Streamlit injeta data-theme="dark" no root quando tema escuro ativo */
[data-theme="dark"] .stApp,
.stApp[data-theme="dark"] {
    background-color: #0E1117 !important;
}

/* Sidebar dark */
[data-theme="dark"] section[data-testid="stSidebar"],
[data-theme="dark"] [data-testid="stSidebar"] {
    background: #1A1D24 !important;
    border-right-color: #2D3139 !important;
}

/* Métricas dark */
[data-theme="dark"] [data-testid="stMetric"] {
    background: #1A1D24 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.3) !important;
}
[data-theme="dark"] [data-testid="stMetricLabel"] p {
    color: #8A96A8 !important;
}
[data-theme="dark"] [data-testid="stMetricValue"] {
    color: #E8EDF5 !important;
}

/* Filtros dark */
[data-theme="dark"] div[style*="background:#F2F5FA"],
[data-theme="dark"] div[style*="background: #F2F5FA"] {
    background: #1A1D24 !important;
    border-color: #2D3139 !important;
}

/* Botões gerais dark */
[data-theme="dark"] .stButton > button {
    background: #1A1D24 !important;
    color: #A8C4E8 !important;
    border-color: #2D5AA0 !important;
}
[data-theme="dark"] .stButton > button:hover {
    background: #1F4788 !important;
    color: #FFFFFF !important;
}

/* Expander dark */
[data-theme="dark"] [data-testid="stExpander"] {
    background: #1A1D24 !important;
    border-color: #2D3139 !important;
}

/* Dataframes dark */
[data-theme="dark"] [data-testid="stDataFrame"] {
    background: #1A1D24 !important;
}

/* Tabs dark */
[data-theme="dark"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #1A1D24 !important;
}
[data-theme="dark"] [data-testid="stTabs"] [data-baseweb="tab"] {
    color: #8A96A8 !important;
}

/* Radio sidebar dark */
[data-theme="dark"] section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
    color: #A8B4C4 !important;
}
[data-theme="dark"] section[data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
    background: linear-gradient(90deg,#1A2A45,#1F3560) !important;
    border-left-color: #4A7BC8 !important;
}
[data-theme="dark"] section[data-testid="stSidebar"] .stRadio label[aria-checked="true"] p {
    color: #7EB3F7 !important;
}

/* Breadcrumb e textos de apoio dark */
[data-theme="dark"] .stMarkdown p {
    color: #C4CDD9 !important;
}

/* Inputs dark */
[data-theme="dark"] .stSelectbox > div > div,
[data-theme="dark"] .stTextInput > div > div > input,
[data-theme="dark"] .stDateInput > div > div > input {
    background: #1A1D24 !important;
    border-color: #2D3139 !important;
    color: #E0E6EF !important;
}

/* Download button dark */
[data-theme="dark"] [data-testid="stDownloadButton"] > button {
    background: #1A2A45 !important;
    color: #7EB3F7 !important;
    border-color: #2D5AA0 !important;
}
[data-theme="dark"] [data-testid="stDownloadButton"] > button:hover {
    background: #1F4788 !important;
    color: #FFFFFF !important;
}

/* Cabeçalho títulos dark */
[data-theme="dark"] .stApp h1 { color: #E8EDF5 !important; }
[data-theme="dark"] .stApp h2 { color: #A8C4E8 !important; }
[data-theme="dark"] .stApp h3 { color: #8AADD4 !important; }


/* ── Mobile (≤768px): layout compacto ── */
@media (max-width: 768px) {

    /* Cards da home: 4 colunas proporcionais no mobile */
    div.home-grid > div[data-testid="stHorizontalBlock"] {
        gap: 4px !important;
        overflow-x: hidden !important;
    }
    div.home-grid > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 0 !important;
        flex: 1 1 0 !important;
        padding: 0 2px !important;
    }

    /* Filtros: esconder barra de labels (captions) no mobile */
    .filter-header-bar { display: none !important; }

    /* Colunas de filtros: empilhar verticalmente no mobile */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) {
        flex-wrap: wrap !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"])
        > div[data-testid="stVerticalBlock"] {
        width: calc(50% - 4px) !important;
        min-width: calc(50% - 4px) !important;
        flex: 0 0 calc(50% - 4px) !important;
    }

    /* Sidebar: fundo sólido no mobile — cores explícitas */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }
    /* Dark mode sidebar mobile */
    @media (prefers-color-scheme: dark) {
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] > div:first-child {
            background-color: #1A1D24 !important;
            background: #1A1D24 !important;
        }
    }

    /* Gráficos: garantir que caibam na tela */
    div[data-testid="stPlotlyChart"] {
        overflow-x: auto !important;
    }
}

/* ── Expander de filtros discreto ── */
div[data-testid="stExpander"] details {
    border: 1px solid rgba(128,128,128,0.15) !important;
    border-radius: 8px !important;
    background: transparent !important;
    margin-bottom: 8px !important;
}
div[data-testid="stExpander"] details summary {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #8A96A8 !important;
    padding: 6px 12px !important;
}
div[data-testid="stExpander"] details summary:hover {
    color: #4A7BC8 !important;
}


/* ── Dark mode via prefers-color-scheme (mais confiável no Streamlit) ── */
@media (prefers-color-scheme: dark) {
    .stApp h1, .stApp h2, .stApp h3 { color: #7EB3F7 !important; }
    [data-testid="stMetricValue"]    { color: #E8EDF5 !important; }
    [data-testid="stMetricLabel"] p  { color: #8A96A8 !important; }
    [data-testid="stSidebar"] .stRadio label[aria-checked="true"] p {
        color: #7EB3F7 !important;
    }
    /* Títulos dos módulos (h2 inline) */
    .stMarkdown h2 { color: #7EB3F7 !important; }
    /* Texto padrão */
    .stMarkdown p  { color: #C4CDD9 !important; }
    /* Cards */
    [data-testid="stMetric"] { background: var(--secondary-background-color) !important; }
    /* Breadcrumb */
    [data-testid="stSidebar"] { background: var(--secondary-background-color) !important; }
}

</style>
""", unsafe_allow_html=True)

# ====================== CONFIGURAÇÕES GITHUB ======================
GITHUB_REPO = "fabiosilvavendas-byte/CRM_Medtextil2.0"
GITHUB_FOLDER = "dados"  # ⭐ PASTA ONDE ESTÃO AS PLANILHAS
GITHUB_TOKEN = None  # Opcional: adicione token se repositório for privado

@st.cache_data(ttl=3600)
def listar_planilhas_github():
    """Lista todos os arquivos Excel da pasta 'dados' no repositório GitHub"""
    try:
        if GITHUB_TOKEN:
            g = Github(GITHUB_TOKEN, timeout=15)
        else:
            g = Github(timeout=15)
        
        repo = g.get_repo(GITHUB_REPO)
        # ⭐ BUSCAR NA PASTA 'dados'
        contents = repo.get_contents(GITHUB_FOLDER)
        
        planilhas = {
            'vendas': None,
            'inadimplencia': None,
            'vendas_produto': None,
            'produtos_agrupados': None,
            'pedidos_pendentes': None,
            'todas': []
        }
        
        for content in contents:
            if content.name.endswith(('.xlsx', '.xls')):
                info = {
                    'nome': content.name,
                    'url': content.download_url,
                    'path': content.path
                }
                planilhas['todas'].append(info)
                
                # Identificar planilha de vendas
                if 'CONSULTA_VENDEDORES' in content.name.upper():
                    planilhas['vendas'] = info
                
                # Identificar planilha de inadimplência
                if 'LANCAMENTO A RECEBER' in content.name.upper() or 'LANCAMENTO_A_RECEBER' in content.name.upper():
                    planilhas['inadimplencia'] = info
                
                # Identificar planilha de vendas por produto
                if 'VENDAS POR PRODUTO' in content.name.upper() and 'GERAL' in content.name.upper():
                    planilhas['vendas_produto'] = info
                
                # Identificar planilha de produtos agrupados
                if 'PRODUTOS_AGRUPADOS_COMPLETOS_CONCILIADOS' in content.name.upper():
                    planilhas['produtos_agrupados'] = info
                
                # Identificar planilha de pedidos pendentes
                if 'PEDIDOSPENDENTES' in content.name.upper().replace(' ', '').replace('_', ''):
                    planilhas['pedidos_pendentes'] = info
        
        if not planilhas['todas']:
            st.warning(f"⚠️ Nenhuma planilha Excel encontrada na pasta '{GITHUB_FOLDER}'")
        
        return planilhas
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao GitHub: {str(e)}")
        st.info(f"💡 Verificando: {GITHUB_REPO}/{GITHUB_FOLDER}")
        return {'vendas': None, 'inadimplencia': None, 'vendas_produto': None, 'produtos_agrupados': None, 'pedidos_pendentes': None, 'todas': []}

@st.cache_data(ttl=3600)
def carregar_planilha_github(url):
    """Carrega planilha diretamente do GitHub"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_excel(io.BytesIO(response.content))
        return df
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout ao carregar planilha. Tente novamente.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao carregar planilha: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao processar planilha: {str(e)}")
        return None

# ====================== AUTENTICAÇÃO ======================
def check_password():
    """Sistema de autenticação com níveis de acesso"""
    
    # 🔐 CONFIGURAÇÃO DE USUÁRIOS E SENHAS
    USUARIOS = {
        "admin123": {
            "tipo": "administrador",
            "nome": "Administrador",
            "modulos": ["Dashboard", "Positivação", "Inadimplência", "Clientes sem Compra", "Histórico", "Preço Médio", "Pedidos Pendentes", "Rankings"]
        },
        "colaborador123": {  # ⬅️ MUDE ESTA SENHA
            "tipo": "colaborador",
            "nome": "Colaborador",
            "modulos": ["Inadimplência", "Histórico", "Pedidos Pendentes"]
        }
    }
    
    def password_entered():
        senha = st.session_state.get("password_input", "")
        
        if senha in USUARIOS:
            st.session_state["password_correct"] = True
            st.session_state["usuario"] = USUARIOS[senha]
            st.session_state["senha_usada"] = senha
        else:
            st.session_state["password_correct"] = False
            st.session_state["show_error"] = True
            if "usuario" in st.session_state:
                del st.session_state["usuario"]

    # Tela de login estilizada
    def render_login(show_error=False):
        st.markdown("""
        <div style="max-width:420px;margin:60px auto 0 auto;background:#FFFFFF;border-radius:16px;
                    padding:40px 36px;box-shadow:0 8px 32px rgba(31,71,136,0.12);border-top:4px solid #1F4788;">
            <div style="text-align:center;margin-bottom:10px;">
                <img src="https://i.imgur.com/gt3rgyL.png" height="52"
                     style="border-radius:8px;" onerror="this.style.display='none'"/>
            </div>
            <div style="text-align:center;font-size:1.4rem;font-weight:700;color:#4A7BC8;margin-bottom:4px;">
                Medtextil BI
            </div>
            <div style="text-align:center;font-size:0.85rem;color:#6C757D;margin-bottom:8px;">
                Dashboard Comercial 2.0
            </div>
        </div>
        """, unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.markdown("<br>", unsafe_allow_html=True)
            st.text_input("🔑 Senha de acesso", type="password", key="password_input", placeholder="Digite sua senha...")
            if st.button("Entrar →", use_container_width=True, type="primary"):
                password_entered()
            if show_error:
                st.error("Senha incorreta. Verifique e tente novamente.")

    if "password_correct" not in st.session_state:
        render_login(show_error=False)
        return False
    elif not st.session_state["password_correct"]:
        render_login(show_error=st.session_state.get("show_error", False))
        return False
    else:
        return True

# ====================== PROCESSAMENTO DE DADOS ======================
def calcular_prazo_historico(data_emissao, data_vencimento_str):
    """
    Calcula o prazo histórico CUMULATIVO em dias.
    NÃO conta o dia da emissão (começa a contar do dia seguinte).
    
    Exemplo:
    - Data Emissão: 18/12/2025 (não conta este dia)
    - Vencimentos: "15/01/2026; 22/01/2026; 29/01/2026; 05/02/2026"
    - Cálculo:
      * De 19/12 até 15/01 = 28 dias
      * De 19/12 até 22/01 = 35 dias
      * De 19/12 até 29/01 = 42 dias
      * De 19/12 até 05/02 = 49 dias
    - Resultado: "28/35/42/49"
    """
    try:
        if pd.isna(data_vencimento_str) or data_vencimento_str == '':
            return ''
        
        if pd.isna(data_emissao):
            return ''
        
        # Converter string para garantir que é texto e limpar
        data_vencimento_str = str(data_vencimento_str).strip()
        
        # Separar as datas por ponto e vírgula
        datas_vencimento = data_vencimento_str.split(';')
        
        prazos = []
        for data_venc_str in datas_vencimento:
            data_venc_str = data_venc_str.strip()
            if not data_venc_str:
                continue
            
            try:
                # Tentar converter para datetime com dayfirst=True (padrão brasileiro)
                data_venc = pd.to_datetime(data_venc_str, errors='coerce', dayfirst=True)
                
                # Normalizar para meia-noite (remove qualquer componente de hora)
                if pd.notna(data_venc):
                    data_venc = data_venc.normalize() if hasattr(data_venc, 'normalize') else data_venc.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Validar se a data é válida e razoável
                if pd.notna(data_venc):
                    # Verificar se a data está dentro de um intervalo razoável (ano entre 2020 e 2030)
                    if 2020 <= data_venc.year <= 2030:
                        # Calcular dias a partir do DIA SEGUINTE à emissão
                        # O Python já calcula correto: não conta o dia da emissão
                        diferenca = (data_venc - data_emissao).days
                        
                        # Validar prazo razoável (entre 1 e 365 dias)
                        if 1 <= diferenca <= 365:
                            prazos.append(str(diferenca))
            except:
                # Ignorar datas inválidas silenciosamente
                continue
        
        # Retornar prazos separados por "/"
        if prazos:
            return '/'.join(prazos)
        else:
            return ''
    except:
        return ''

def gerar_pdf_pedido(dados_cliente, dados_pedido, itens_pedido, observacao=''):
    """Gera PDF do pedido no formato da Medtextil"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo customizado
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica'
    )
    
    style_small = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica'
    )
    
    # CABEÇALHO - SOLUÇÃO COM CONTROLE TOTAL DE TAMANHO
    logo_adicionado = False
    try:
        # Buscar logo do GitHub
        logo_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FOLDER}/logo.png"
        response = requests.get(logo_url)
        if response.status_code == 200:
            from PIL import Image as PILImage
            
            # Carregar imagem com PIL para ter controle total
            logo_buffer = io.BytesIO(response.content)
            pil_img = PILImage.open(logo_buffer)
            
            # Obter dimensões originais
            largura_original, altura_original = pil_img.size
            proporcao = largura_original / altura_original
            
            # DIMENSÕES FIXAS DO LOGO NO PDF
            altura_desejada_mm = 15  # Altura em milímetros
            largura_desejada_mm = altura_desejada_mm * proporcao
            
            # Criar Image do ReportLab com dimensões exatas
            logo_buffer.seek(0)  # Voltar ao início do buffer
            logo_img = Image(logo_buffer, width=largura_desejada_mm*mm, height=altura_desejada_mm*mm)
            
            # Texto ao lado - com width definido para não vazar
            texto_empresa = Paragraph(
                "<b>MEDTEXTIL PRODUTOS TEXTIL HOSPITALARES</b><br/>"
                "<font size=8>CNPJ: 40.357.820/0001-50  Inscrição Estadual: 16.390.286-0</font>",
                style_small
            )
            
            # Calcular colWidths baseado no logo real
            espaco_logo = largura_desejada_mm + 5  # Logo + margem de 5mm
            espaco_texto = 190 - espaco_logo  # Resto da página
            
            # Criar tabela com dimensões calculadas
            cabecalho_data = [[logo_img, texto_empresa]]
            cabecalho_table = Table(cabecalho_data, colWidths=[espaco_logo*mm, espaco_texto*mm])
            cabecalho_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (0, 0), 'TOP'),
                ('VALIGN', (1, 0), (1, 0), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(cabecalho_table)
            elements.append(Spacer(1, 5*mm))
            logo_adicionado = True
            
    except Exception as e:
        # Se PIL não disponível ou erro, fallback simples
        try:
            logo_buffer = io.BytesIO(response.content)
            # Fallback: tamanho fixo conservador
            logo_img = Image(logo_buffer, width=30*mm, height=15*mm)
            
            texto_empresa = Paragraph(
                "<b>MEDTEXTIL PRODUTOS TEXTIL HOSPITALARES</b><br/>"
                "<font size=8>CNPJ: 40.357.820/0001-50  Inscrição Estadual: 16.390.286-0</font>",
                style_small
            )
            
            cabecalho_data = [[logo_img, texto_empresa]]
            cabecalho_table = Table(cabecalho_data, colWidths=[35*mm, 155*mm])
            cabecalho_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(cabecalho_table)
            elements.append(Spacer(1, 5*mm))
            logo_adicionado = True
        except:
            pass
    
    if not logo_adicionado:
        # Fallback final para texto
        elements.append(Paragraph("<b>MEDTEXTIL PRODUTOS TEXTIL HOSPITALARES</b><br/>"
                                 "CNPJ: 40.357.820/0001-50 | Inscrição Estadual: 16.390.286-0", style_title))
        elements.append(Spacer(1, 5*mm))
    
    # REPRESENTANTE (tabela simples como no modelo)
    data_repr = [
        ['Representante', dados_cliente.get('representante', '')],
        ['CNPJ', dados_cliente.get('cnpj', '')]
    ]
    table_repr = Table(data_repr, colWidths=[40*mm, 150*mm])
    table_repr.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(table_repr)
    elements.append(Spacer(1, 2*mm))
    
    # INFORMAÇÕES DO CLIENTE (layout simplificado)
    data_cliente = [
        [Paragraph("<b>Informações sobre o Cliente</b>", style_normal), '', '', ''],
        ['Cliente', dados_cliente.get('razao_social', ''), '', Paragraph("<b>Nome</b><br/>Fantasia:<br/>Inscr.<br/>Estadual:", style_small)],
        ['CNPJ:', dados_cliente.get('cnpj', ''), '', dados_cliente.get('nome_fantasia', '')],
        ['Telefone:', dados_cliente.get('telefone', ''), 'Email NF-e:', dados_cliente.get('email', '')],
        ['Endereço:', dados_cliente.get('endereco', ''), '', dados_cliente.get('ie', '')],
        ['Observação:', dados_cliente.get('obs_cliente', ''), '', '']
    ]
    
    table_cliente = Table(data_cliente, colWidths=[25*mm, 85*mm, 25*mm, 55*mm])
    table_cliente.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('SPAN', (0, 0), (-1, 0)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (1, 5), (-1, 5)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table_cliente)
    elements.append(Spacer(1, 2*mm))
    
    # INFORMAÇÕES DO PEDIDO (layout compacto)
    data_pedido_info = [
        ['Informações sobre Pedido Nº', dados_pedido.get('numero', ''), '', Paragraph("<b>Tabela de<br/>Preço:</b>", style_small)],
        ['Condições de Pagto:', dados_pedido.get('condicoes_pagto', ''), '', dados_pedido.get('tabela_preco', '')],
        ['Data da Venda:', dados_pedido.get('data_venda', ''), 'Tipo de<br/>Frete:', dados_pedido.get('tipo_frete', 'CIF')]
    ]
    
    table_pedido = Table(data_pedido_info, colWidths=[45*mm, 90*mm, 20*mm, 35*mm])
    table_pedido.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table_pedido)
    elements.append(Spacer(1, 3*mm))
    
    # DETALHE DO PEDIDO
    elements.append(Paragraph("<b>Detalhe do Pedido</b>", style_normal))
    elements.append(Spacer(1, 1*mm))
    
    # Cabeçalho da tabela de itens (cor azul igual ao modelo)
    header_itens = ['COD.', 'PRODUTO', 'PESO', 'CAIXA DE\nEMBARQUE', 'QTDE', 'VALOR', 'TOTAL', 'COMISSÃO%']
    data_itens = [header_itens]
    
    # Adicionar itens
    for item in itens_pedido:
        descricao = str(item.get('descricao', ''))
        # Quebrar descrição se muito longa
        if len(descricao) > 45:
            descricao = descricao[:45] + '...'
        
        data_itens.append([
            str(item.get('codigo', '')),
            descricao,
            str(item.get('peso', '')),
            str(item.get('cx_embarque', '')),
            f"{item.get('quantidade', 0):.0f}",
            f"R$ {item.get('valor_unit', 0):.2f}",
            f"R$ {item.get('total', 0):.2f}",
            str(item.get('comissao', ''))
        ])
    
    # Calcular totais
    total_qtde = sum([item.get('quantidade', 0) for item in itens_pedido])
    total_valor = sum([item.get('total', 0) for item in itens_pedido])
    
    # Linha de total (sem bordas superiores, fundo cinza)
    data_itens.append(['', '', '', '', f"{total_qtde:.0f}", '', f"R$ {total_valor:,.2f}", ''])
    
    col_widths = [12*mm, 70*mm, 15*mm, 18*mm, 12*mm, 20*mm, 25*mm, 18*mm]
    table_itens = Table(data_itens, colWidths=col_widths)
    
    # Estilo da tabela de itens (azul igual ao modelo)
    num_rows = len(data_itens)
    style_itens = [
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),  # Azul escuro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Centralizar QTDE
        ('ALIGN', (5, 1), (7, -1), 'RIGHT'),   # Alinhar valores à direita
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
    ]
    
    table_itens.setStyle(TableStyle(style_itens))
    elements.append(table_itens)
    elements.append(Spacer(1, 3*mm))
    
    # RESUMO FINAL
    data_resumo = [
        ['Qtde Itens', 'Frete', 'Total Final'],
        [f"{total_qtde:.0f}", dados_pedido.get('tipo_frete', 'CIF'), f"R$ {total_valor:,.2f}"]
    ]
    
    table_resumo = Table(data_resumo, colWidths=[60*mm, 60*mm, 70*mm])
    table_resumo.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table_resumo)
    elements.append(Spacer(1, 3*mm))
    
    # OBSERVAÇÃO
    if observacao:
        elements.append(Paragraph("<b>Observação</b>", style_normal))
        elements.append(Paragraph(observacao, style_small))
    
    # Construir PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def calcular_comissao(preco_unit, preco_ref):
    """
    Calcula o percentual de comissão com base no desvio do PrecoUnit em relação ao preço de referência.
    
    Regras:
    - PrecoUnit >= 6% ACIMA  do preço ref → 4%
    - PrecoUnit igual ao preço ref (0% desconto) → 3%
    - PrecoUnit até 3% ABAIXO do preço ref → 2,5%
    - PrecoUnit 3% ou mais ABAIXO do preço ref → 2%
    """
    try:
        if pd.isna(preco_unit) or pd.isna(preco_ref) or preco_ref == 0:
            return ''
        
        preco_unit = float(preco_unit)
        preco_ref  = float(preco_ref)
        
        # Arredondar para 2 casas decimais (centavos) antes de comparar
        # Elimina ruído de ponto flutuante sem distorcer valores reais
        preco_unit = round(preco_unit, 2)
        preco_ref  = round(preco_ref,  2)
        
        variacao = round(((preco_unit - preco_ref) / preco_ref) * 100, 4)
        
        if variacao >= 6:     # >= 6% acima → 4%
            return '4%'
        elif variacao >= 0:   # >= 0% (igual ou acima) → 3%
            return '3%'
        elif variacao > -3:   # Entre 0% e -3% → 2,5%
            return '2,5%'
        else:                 # -3% ou mais abaixo → 2%
            return '2%'
    except:
        return ''


# ── Paleta institucional e helper de layout de gráficos ──────────────────
CORES_INST = ['#1F4788', '#2E86AB', '#28A745', '#F4A261', '#6C757D',
              '#163561', '#1B5E8A', '#1E7B34', '#C97A3A', '#495057']

def aplicar_layout_grafico(fig, height=None):
    """Aplica o estilo institucional Medtextil a qualquer figura Plotly."""
    layout_kwargs = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, Segoe UI, Roboto, sans-serif', color='#495057', size=12),
        margin=dict(l=10, r=10, t=36, b=10),
        xaxis=dict(showgrid=False, showline=True, linecolor='#E9ECEF', tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0', showline=False, tickfont=dict(size=11)),
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor='#1F4788', font_color='white', font_size=12,
                        bordercolor='#1F4788'),
    )
    if height:
        layout_kwargs['height'] = height
    fig.update_layout(**layout_kwargs)
    return fig

@st.cache_data
def processar_dados(df):
    """Aplica as regras de negócio nos dados"""
    df['Valor_Real'] = df.apply(
        lambda row: row['TotalProduto'] if row['TipoMov'] == 'NF Venda' else -row['TotalProduto'],
        axis=1
    )
    # Converter DataEmissao com formato brasileiro e normalizar para meia-noite
    df['DataEmissao'] = pd.to_datetime(df['DataEmissao'], errors='coerce', dayfirst=True)
    # Normalizar para meia-noite (remove hora) para cálculos corretos de dias
    df['DataEmissao'] = df['DataEmissao'].dt.normalize()
    
    df['Mes'] = df['DataEmissao'].dt.month
    df['Ano'] = df['DataEmissao'].dt.year
    df['MesAno'] = df['DataEmissao'].dt.to_period('M').astype(str)
    
    # Calcular prazo histórico se a coluna DataVencimento existir
    if 'DataVencimento' in df.columns:
        df['PrazoHistorico'] = df.apply(
            lambda row: calcular_prazo_historico(row['DataEmissao'], row['DataVencimento']),
            axis=1
        )
    else:
        df['PrazoHistorico'] = ''
    
    return df

def obter_notas_unicas(df):
    """
    Agrupa produtos da mesma nota e soma os valores.
    CORREÇÃO CRÍTICA: Cada linha = 1 produto. Mesma nota tem vários produtos.
    ANTES: drop_duplicates mantinha só o primeiro produto (PERDIA VALORES!)
    AGORA: groupby soma todos os produtos da mesma nota
    """
    if len(df) == 0:
        return df
    
    # Colunas numéricas para somar
    colunas_soma = ['TotalProduto', 'Quantidade']
    if 'Valor_Real' in df.columns:
        colunas_soma.append('Valor_Real')
    
    # Agrupar por Numero_NF e somar valores dos produtos
    agg_dict = {col: 'sum' for col in colunas_soma if col in df.columns}
    
    # Manter outras colunas importantes (pegar primeiro valor da nota)
    for col in df.columns:
        if col not in agg_dict and col != 'Numero_NF':
            agg_dict[col] = 'first'
    
    notas_agrupadas = df.groupby('Numero_NF', as_index=False).agg(agg_dict)
    
    return notas_agrupadas

def to_excel(df):
    """Converte DataFrame para Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

def to_excel_pedidos_pendentes(df):
    """Converte DataFrame de pedidos pendentes para Excel com abas por tipo de produto"""
    output = io.BytesIO()
    
    # Função para identificar tipo de produto pela descrição
    def identificar_tipo(descricao):
        if pd.isna(descricao):
            return 'OUTROS'
        
        descricao_upper = str(descricao).upper()
        
        if 'ATADURA' in descricao_upper:
            return 'ATADURAS'
        elif 'CAMPO' in descricao_upper:
            return 'CAMPO'
        elif ('GAZE' in descricao_upper and 'ROLO' in descricao_upper) or ('GAZE' in descricao_upper and 'CIRCULAR' in descricao_upper):
            return 'GAZE EM ROLO'
        elif 'NAO ESTERIL' in descricao_upper or 'NÃO ESTERIL' in descricao_upper or 'NÃO ESTÉRIL' in descricao_upper or 'NAO ESTÉRIL' in descricao_upper:
            return 'NÃO ESTERIL'
        elif 'ESTERIL' in descricao_upper or 'ESTÉRIL' in descricao_upper:
            return 'ESTERIL'
        else:
            return 'OUTROS'
    
    # Função para identificar se é HOSPITALAR ou FARMA (apenas para ATADURAS)
    def identificar_categoria(descricao, tipo):
        if tipo == 'ATADURAS':
            if pd.notna(descricao) and 'HOSP' in str(descricao).upper():
                return 'HOSPITALAR'
            else:
                return 'FARMA'
        return ''
    
    # Adicionar coluna de tipo
    df_export = df.copy()
    df_export['TipoProduto'] = df_export['Descricao'].apply(identificar_tipo)
    df_export['Categoria'] = df_export.apply(lambda row: identificar_categoria(row['Descricao'], row['TipoProduto']), axis=1)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Definir ordem das abas
        tipos_ordem = ['ATADURAS', 'CAMPO', 'ESTERIL', 'NÃO ESTERIL', 'GAZE EM ROLO', 'OUTROS']
        
        for tipo in tipos_ordem:
            df_tipo = df_export[df_export['TipoProduto'] == tipo].copy()
            
            if len(df_tipo) > 0:
                # Para ATADURAS, ordenar por Categoria (HOSPITALAR primeiro)
                if tipo == 'ATADURAS':
                    df_tipo = df_tipo.sort_values('Categoria')
                
                # Remover colunas auxiliares antes de exportar
                colunas_para_remover = ['TipoProduto']
                # Manter coluna Categoria apenas para ATADURAS
                if tipo != 'ATADURAS':
                    colunas_para_remover.append('Categoria')
                
                df_tipo = df_tipo.drop(columns=[col for col in colunas_para_remover if col in df_tipo.columns])
                
                df_tipo.to_excel(writer, index=False, sheet_name=tipo)
    
    return output.getvalue()

def formatar_moeda(valor):
    """Formata valor para moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_dataframe_moeda(df, colunas_moeda):
    """Formata colunas de moeda em um dataframe para exibição"""
    df_formatado = df.copy()
    for col in colunas_moeda:
        if col in df_formatado.columns:
            df_formatado[col] = df_formatado[col].apply(lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00")
    return df_formatado

@st.cache_data
def processar_inadimplencia(df):
    """Processa dados de inadimplência"""
    # Padronizar nomes das colunas
    # Tentar várias variações de nomes de colunas
    rename_map = {
        'Funcionário': 'Vendedor',
        'Razão Social': 'Cliente',
        'N_Doc': 'NumeroDoc',
        'N Doc': 'NumeroDoc',
        'NDoc': 'NumeroDoc',
        'Numero Doc': 'NumeroDoc',
        'Dt.Vencimento': 'DataVencimento',
        'Dt Vencimento': 'DataVencimento',
        'Data Vencimento': 'DataVencimento',
        'Vr.Líquido': 'ValorLiquido',
        'Vr Líquido': 'ValorLiquido',
        'Valor Líquido': 'ValorLiquido',
        'Valor Liquido': 'ValorLiquido',
        'Conta/Caixa': 'Banco',
        'Conta Caixa': 'Banco',
        'UF': 'Estado'
    }
    
    df = df.rename(columns=rename_map)
    
    # Converter data de vencimento
    df['DataVencimento'] = pd.to_datetime(df['DataVencimento'], errors='coerce')
    
    # Calcular dias de atraso
    hoje = pd.Timestamp.now()
    df['DiasAtraso'] = (hoje - df['DataVencimento']).dt.days
    df['DiasAtraso'] = df['DiasAtraso'].apply(lambda x: max(0, x))  # Não mostrar valores negativos
    
    # Classificar inadimplência
    def classificar_inadimplencia(dias):
        if dias == 0:
            return 'A Vencer'
        elif dias <= 30:
            return '1-30 dias'
        elif dias <= 60:
            return '31-60 dias'
        elif dias <= 90:
            return '61-90 dias'
        else:
            return 'Acima de 90 dias'
    
    df['FaixaAtraso'] = df['DiasAtraso'].apply(classificar_inadimplencia)
    
    return df


# ====================== PROPOSTA PDF (HISTÓRICO DE CLIENTE) ======================
def gerar_proposta_pdf_historico(cliente_info_dict, historico_df, vendas_resumo):
    """
    Gera PDF de Proposta Comercial baseada no histórico de compras do cliente.
    Usa apenas a biblioteca fpdf2 (pip install fpdf2).
    Fallback: se fpdf2 não estiver disponível, usa ReportLab.
    """
    import io, requests
    from datetime import date

    razao    = str(cliente_info_dict.get('RazaoSocial', ''))
    cpf_cnpj = str(cliente_info_dict.get('CPF_CNPJ', ''))
    cidade   = str(cliente_info_dict.get('Cidade', ''))
    estado   = str(cliente_info_dict.get('Estado', ''))
    vendedor = str(cliente_info_dict.get('Vendedor', ''))
    hoje     = date.today().strftime('%d/%m/%Y')

    # ── Tentar fpdf2 primeiro ─────────────────────────────────────────────
    try:
        from fpdf import FPDF

        class PropostaPDF(FPDF):
            def header(self):
                # Logo
                try:
                    resp = requests.get("https://i.imgur.com/gt3rgyL.png", timeout=8)
                    if resp.status_code == 200:
                        tmp = io.BytesIO(resp.content)
                        tmp.seek(0)
                        import tempfile, os
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f_tmp:
                            f_tmp.write(resp.content)
                            tmp_path = f_tmp.name
                        self.image(tmp_path, x=10, y=8, w=32)
                        os.unlink(tmp_path)
                except Exception:
                    pass
                self.set_xy(46, 10)
                self.set_font('Helvetica', 'B', 13)
                self.set_text_color(31, 71, 136)
                self.cell(0, 6, 'MEDTEXTIL PRODUTOS TEXTIL HOSPITALARES', ln=True)
                self.set_xy(46, 16)
                self.set_font('Helvetica', '', 8)
                self.set_text_color(100, 100, 100)
                self.cell(0, 5, 'CNPJ: 40.357.820/0001-50  |  IE: 16.390.286-0', ln=True)
                self.set_draw_color(31, 71, 136)
                self.set_line_width(0.6)
                self.line(10, 26, 200, 26)
                self.ln(4)

            def footer(self):
                self.set_y(-14)
                self.set_font('Helvetica', 'I', 7)
                self.set_text_color(160, 160, 160)
                self.cell(0, 6,
                    f'Medtextil — Proposta gerada em {hoje}  |  Pág. {self.page_no()}',
                    align='C')

        pdf = PropostaPDF()
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()
        pdf.set_margins(10, 10, 10)

        # ── Título ────────────────────────────────────────────────────────
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(31, 71, 136)
        pdf.cell(0, 8, 'PROPOSTA COMERCIAL', align='C', ln=True)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 5, f'Emitida em {hoje}', align='C', ln=True)
        pdf.ln(4)

        # ── Dados do Cliente ──────────────────────────────────────────────
        pdf.set_fill_color(240, 244, 255)
        pdf.set_draw_color(200, 210, 230)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(31, 71, 136)
        pdf.cell(0, 7, ' DADOS DO CLIENTE', fill=True, border=1, ln=True)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        w1, w2 = 38, 152
        for label, valor in [
            ('Razão Social', razao),
            ('CPF / CNPJ',   cpf_cnpj),
            ('Cidade / UF',  f'{cidade} / {estado}'),
            ('Vendedor',     vendedor),
        ]:
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(w1, 6, f'  {label}:', border='LB', fill=False)
            pdf.set_font('Helvetica', '', 8)
            pdf.cell(w2, 6, f'  {valor}', border='RB', ln=True)
        pdf.ln(5)

        # ── Resumo Financeiro ─────────────────────────────────────────────
        pdf.set_fill_color(240, 244, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(31, 71, 136)
        pdf.cell(0, 7, ' RESUMO FINANCEIRO (PERÍODO SELECIONADO)', fill=True, border=1, ln=True)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        w3 = 95
        itens_resumo = list(vendas_resumo.items())
        for i in range(0, len(itens_resumo), 2):
            k1, v1 = itens_resumo[i]
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(w3, 6, f'  {k1}:', border='LB')
            pdf.set_font('Helvetica', '', 8)
            if i + 1 < len(itens_resumo):
                k2, v2 = itens_resumo[i+1]
                pdf.cell(w3, 6, f'  {v1}', border='B')
                pdf.set_font('Helvetica', 'B', 8)
                pdf.cell(0, 6, f'  {k2}:', border='B')
            else:
                pdf.cell(0, 6, f'  {v1}', border='RB')
            pdf.ln()
        pdf.ln(5)

        # ── Tabela de Produtos ────────────────────────────────────────────
        pdf.set_fill_color(31, 71, 136)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        cols_w = [18, 72, 18, 22, 26, 26]
        cols_h = ['Código', 'Produto', 'Qtd', 'Prazo', 'Preço Unit.', 'Total']
        for cw, ch in zip(cols_w, cols_h):
            pdf.cell(cw, 7, ch, border=1, fill=True, align='C')
        pdf.ln()

        pdf.set_text_color(50, 50, 50)
        fill_row = False
        vendas_only = historico_df[historico_df['TipoMov'] == 'NF Venda'].copy()
        # Agrupar por produto para resumo
        grp_cols = ['CodigoProduto', 'NomeProduto']
        if 'PrazoHistorico' in vendas_only.columns:
            grp_cols_agg = {
                'Quantidade': 'sum',
                'PrecoUnit': 'mean',
                'TotalProduto': 'sum',
                'PrazoHistorico': 'first'
            }
        else:
            grp_cols_agg = {
                'Quantidade': 'sum',
                'PrecoUnit': 'mean',
                'TotalProduto': 'sum'
            }
        try:
            resumo_prod = vendas_only.groupby(
                ['CodigoProduto', 'NomeProduto'], as_index=False
            ).agg({k: v for k, v in grp_cols_agg.items() if k in vendas_only.columns})
            resumo_prod = resumo_prod.sort_values('TotalProduto', ascending=False)
        except Exception:
            resumo_prod = vendas_only[['CodigoProduto','NomeProduto','Quantidade','PrecoUnit','TotalProduto']].head(30)

        for _, row in resumo_prod.iterrows():
            pdf.set_fill_color(247, 249, 255) if fill_row else pdf.set_fill_color(255, 255, 255)
            pdf.set_font('Helvetica', '', 7)
            cod  = str(row.get('CodigoProduto', ''))[:8]
            nome = str(row.get('NomeProduto', ''))[:38]
            qtd  = f"{row.get('Quantidade', 0):,.0f}"
            prazo = str(row.get('PrazoHistorico', '-'))[:10] if 'PrazoHistorico' in row.index else '-'
            preco = f"R$ {row.get('PrecoUnit', 0):,.2f}"
            total = f"R$ {row.get('TotalProduto', 0):,.2f}"
            row_vals = [cod, nome, qtd, prazo, preco, total]
            aligns   = ['C', 'L', 'C', 'C', 'R', 'R']
            for cw, rv, al in zip(cols_w, row_vals, aligns):
                pdf.cell(cw, 6, rv, border=1, fill=True, align=al)
            pdf.ln()
            fill_row = not fill_row

        # Total geral
        total_geral = vendas_only['TotalProduto'].sum() if len(vendas_only) > 0 else 0
        pdf.set_fill_color(31, 71, 136)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(sum(cols_w[:5]), 7, 'TOTAL GERAL', border=1, fill=True, align='R')
        pdf.cell(cols_w[5], 7, f'R$ {total_geral:,.2f}', border=1, fill=True, align='R')
        pdf.ln(8)

        # ── Rodapé da proposta ────────────────────────────────────────────
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(130, 130, 130)
        pdf.multi_cell(0, 5,
            'Esta proposta é baseada no histórico de compras do cliente e não representa um pedido confirmado. '
            'Valores sujeitos a alteração. Validade: 15 dias.')

        return pdf.output()

    # ── Fallback: ReportLab ───────────────────────────────────────────────
    except ImportError:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=15*mm, leftMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        azul = colors.HexColor('#1F4788')
        elements = []

        # Título
        p_title = ParagraphStyle('T', parent=styles['Heading1'],
                                 fontSize=16, textColor=azul, alignment=1)
        elements.append(Paragraph('PROPOSTA COMERCIAL', p_title))
        elements.append(Paragraph(f'<font size=9 color="grey">Medtextil — {hoje}</font>', styles['Normal']))
        elements.append(Spacer(1, 6*mm))

        # Dados do cliente
        dados = [['Razão Social', razao], ['CPF/CNPJ', cpf_cnpj],
                 ['Cidade/UF', f'{cidade}/{estado}'], ['Vendedor', vendedor]]
        t_dados = Table(dados, colWidths=[40*mm, 150*mm])
        t_dados.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(0,-1), colors.HexColor('#F0F4FF')),
            ('TEXTCOLOR', (0,0),(0,-1), azul),
            ('FONTNAME', (0,0),(0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0),(-1,-1), 8),
            ('BOX', (0,0),(-1,-1), 0.5, colors.grey),
            ('INNERGRID', (0,0),(-1,-1), 0.3, colors.lightgrey),
            ('LEFTPADDING', (0,0),(-1,-1), 5),
        ]))
        elements.append(t_dados)
        elements.append(Spacer(1, 6*mm))

        # Resumo
        for k, v in vendas_resumo.items():
            elements.append(Paragraph(f'<b>{k}:</b> {v}', styles['Normal']))
        elements.append(Spacer(1, 4*mm))

        # Tabela de produtos
        vendas_only = historico_df[historico_df['TipoMov'] == 'NF Venda']
        header = ['Código', 'Produto', 'Qtd', 'Preço Unit.', 'Total']
        rows = [header]
        try:
            grp = vendas_only.groupby(['CodigoProduto','NomeProduto'], as_index=False).agg(
                {'Quantidade':'sum','PrecoUnit':'mean','TotalProduto':'sum'})
            grp = grp.sort_values('TotalProduto', ascending=False)
            for _, r in grp.iterrows():
                rows.append([str(r['CodigoProduto'])[:8], str(r['NomeProduto'])[:40],
                             f"{r['Quantidade']:,.0f}", f"R$ {r['PrecoUnit']:,.2f}",
                             f"R$ {r['TotalProduto']:,.2f}"])
        except Exception:
            pass
        total_g = vendas_only['TotalProduto'].sum() if len(vendas_only) > 0 else 0
        rows.append(['','','','Total Geral', f'R$ {total_g:,.2f}'])

        t_prod = Table(rows, colWidths=[20*mm, 80*mm, 18*mm, 28*mm, 28*mm])
        t_prod.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), azul),
            ('TEXTCOLOR', (0,0),(-1,0), colors.white),
            ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0),(-1,-1), 7),
            ('ROWBACKGROUNDS', (0,1),(-1,-2), [colors.white, colors.HexColor('#F7F9FF')]),
            ('BACKGROUND', (0,-1),(-1,-1), colors.HexColor('#F0F4FF')),
            ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'),
            ('BOX', (0,0),(-1,-1), 0.5, colors.grey),
            ('INNERGRID', (0,0),(-1,-1), 0.3, colors.lightgrey),
            ('LEFTPADDING', (0,0),(-1,-1), 3),
            ('ALIGN', (2,0),(-1,-1), 'RIGHT'),
        ]))
        elements.append(t_prod)
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# ====================== FILTROS DE DATA LOCAIS ======================
def renderizar_filtros_locais(key_prefix, label="📅 Ajustar Período"):
    """
    Expander compacto com date_inputs lado a lado.
    Retorna (data_inicial, data_final) — None se não preenchido.
    Usa key_prefix para evitar conflito de keys entre módulos.
    """
    data_ini = None
    data_fim = None
    with st.expander(label, expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            data_ini = st.date_input(
                "De", value=None,
                key=f"local_ini_{key_prefix}",
                format="DD/MM/YYYY",
                label_visibility="visible"
            )
        with c2:
            data_fim = st.date_input(
                "Até", value=None,
                key=f"local_fim_{key_prefix}",
                format="DD/MM/YYYY",
                label_visibility="visible"
            )
    return data_ini, data_fim

# ====================== INÍCIO DO APP ======================
if not check_password():
    st.stop()

# Obter informações do usuário logado
usuario = st.session_state.get("usuario", {})
tipo_usuario = usuario.get("tipo", "")
nome_usuario = usuario.get("nome", "Usuário")
modulos_permitidos = usuario.get("modulos", [])

# ── Sidebar: Logo + Usuário + Navegação (clean) ──────────────────────────
with st.sidebar:
    # ── Logo centralizado ──
    st.markdown("""
    <div style="text-align:center;padding:20px 0 14px 0;border-bottom:1px solid #E9ECEF;margin-bottom:14px;">
        <img src="https://i.imgur.com/gt3rgyL.png" height="56"
             style="border-radius:10px;box-shadow:0 2px 8px rgba(31,71,136,0.18);"
             onerror="this.style.display='none'"/>
        <div style="font-size:0.8rem;font-weight:800;color:#4A7BC8;letter-spacing:0.1em;
                    text-transform:uppercase;margin-top:10px;">Medtextil</div>
        <div style="font-size:0.65rem;color:#ADB5BD;letter-spacing:0.06em;margin-top:1px;">
            BI Dashboard 2.0
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ── Badge do usuário ──
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#F0F4FF,#E8EFFD);border:1px solid #C5D5F0;
                border-radius:10px;padding:10px 14px;font-size:0.83rem;color:#4A7BC8;
                font-weight:600;text-align:center;margin-bottom:6px;">
        👤 &nbsp;{nome_usuario}
    </div>
    """, unsafe_allow_html=True)
    # ── Botão sair compacto ──
    if st.button("🚪 Sair", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

# ── Cabeçalho principal ───────────────────────────────────────────────────
col_titulo, col_actions = st.columns([4, 1])
with col_titulo:
    st.markdown("# 📊 Dashboard Comercial")
    st.markdown('<p class="page-subtitle">Medtextil Produtos Textil Hospitalares — Análise de Vendas & BI</p>',
                unsafe_allow_html=True)

# ── Carregamento silencioso + Status no sidebar expander ─────────────────
with st.sidebar:
    with st.expander("🛠️ Status das Planilhas", expanded=False):
        with st.spinner("Conectando ao GitHub..."):
            planilhas_disponiveis = listar_planilhas_github()

        if planilhas_disponiveis['vendas']:
            st.success(f"✅ Vendas: {planilhas_disponiveis['vendas']['nome']}")
            url_planilha_vendas = planilhas_disponiveis['vendas']['url']
        else:
            st.error("❌ Planilha de vendas não encontrada")
            st.info("Procurando por arquivo com 'CONSULTA_VENDEDORES' no nome")

        if planilhas_disponiveis['inadimplencia']:
            st.success(f"✅ Inadimplência: {planilhas_disponiveis['inadimplencia']['nome']}")
        else:
            st.warning("⚠️ Inadimplência não encontrada (módulo desabilitado)")

        if planilhas_disponiveis.get('produtos_agrupados'):
            st.success(f"✅ Produtos: {planilhas_disponiveis['produtos_agrupados']['nome']}")

        if st.button("🔄 Recarregar Dados", use_container_width=True, key="btn_reload"):
            st.cache_data.clear()
            st.rerun()

# Validação crítica fora do expander (sem mensagem visual)
if not planilhas_disponiveis.get('vendas'):
    st.error("❌ Planilha de vendas não encontrada no GitHub. Verifique o repositório.")
    st.stop()

with st.spinner(""):
    df = carregar_planilha_github(url_planilha_vendas)

if df is None:
    st.error("❌ Não foi possível carregar os dados de vendas.")
    st.stop()

df = processar_dados(df)

# Carregar planilha de produtos para cálculo de comissão
if planilhas_disponiveis.get('produtos_agrupados'):
    df_ref_preco = carregar_planilha_github(planilhas_disponiveis['produtos_agrupados']['url'])
    if df_ref_preco is not None:
        df_ref_preco.columns = df_ref_preco.columns.str.upper()
        if 'ID_COD' in df_ref_preco.columns and 'PRECO' in df_ref_preco.columns:
            df_ref_preco = df_ref_preco[['ID_COD', 'PRECO']].rename(
                columns={'ID_COD': 'CodigoProduto', 'PRECO': 'PrecoRef'}
            )
            def normalizar_codigo(val):
                try:
                    return str(int(float(str(val).strip())))
                except:
                    return str(val).strip()
            df['CodigoProduto'] = df['CodigoProduto'].apply(normalizar_codigo)
            df_ref_preco['CodigoProduto'] = df_ref_preco['CodigoProduto'].apply(normalizar_codigo)
            df_ref_preco = df_ref_preco.drop_duplicates(subset=['CodigoProduto'], keep='first')
            df = df.merge(df_ref_preco, on='CodigoProduto', how='left')
            df['Comissao'] = df.apply(
                lambda row: calcular_comissao(row['PrecoUnit'], row['PrecoRef']),
                axis=1
            )
        else:
            df['PrecoRef'] = None
            df['Comissao'] = ''
else:
    df['PrecoRef'] = None
    df['Comissao'] = ''
''

# ── Filtros Globais — dentro de expander único ───────────────────────────
with st.expander("⚙️ Filtros", expanded=False):
    # Linha 1: Datas lado a lado
    fc1, fc2 = st.columns(2)
    with fc1:
        data_inicial = st.date_input("📅 Data Inicial", value=None,
                                     key="data_ini", format="DD/MM/YYYY")
    with fc2:
        data_final = st.date_input("📅 Data Final", value=None,
                                   key="data_fim", format="DD/MM/YYYY")
    # Linha 2: Vendedor e Estado lado a lado
    fc3, fc4 = st.columns(2)
    with fc3:
        vendedores = ['Todos'] + sorted(df['Vendedor'].dropna().unique().tolist())
        vendedor_filtro = st.selectbox("👤 Vendedor", vendedores, key="vend_global")
    with fc4:
        estados = ['Todos'] + sorted(df['Estado'].dropna().unique().tolist())
        estado_filtro = st.selectbox("🗺️ Estado", estados, key="est_global")
    # Linha 3: Mês e Ano lado a lado
    fc5, fc6 = st.columns(2)
    with fc5:
        meses_opcoes = ['Todos'] + list(range(1, 13))
        mes_filtro = st.selectbox("📆 Mês", meses_opcoes, key="mes_global")
    with fc6:
        anos_opcoes = ['Todos'] + sorted(df['Ano'].dropna().unique().tolist(), reverse=True)
        ano_filtro = st.selectbox("🗓️ Ano", anos_opcoes, key="ano_global")
df_filtrado = df.copy()

if data_inicial:
    df_filtrado = df_filtrado[df_filtrado['DataEmissao'] >= pd.to_datetime(data_inicial)]
if data_final:
    df_filtrado = df_filtrado[df_filtrado['DataEmissao'] <= pd.to_datetime(data_final)]
if vendedor_filtro != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor_filtro]
if estado_filtro != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_filtro]
if mes_filtro != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Mes'] == mes_filtro]
if ano_filtro != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_filtro]

notas_unicas = obter_notas_unicas(df_filtrado)

st.sidebar.markdown("---")

# ====================== NAVEGAÇÃO ======================

_DESC = {
    "Dashboard":          "Visão geral de faturamento",
    "Positivação":        "Clientes atendidos no período",
    "Inadimplência":      "Títulos em aberto e atrasos",
    "Clientes sem Compra":"Clientes inativos para reativar",
    "Histórico":          "Consulta por cliente ou vendedor",
    "Preço Médio":        "Análise de preços por produto",
    "Pedidos Pendentes":  "Itens aguardando faturamento",
    "Rankings":           "Top vendedores e clientes",
}
_INFO_CARD = {}  # preenchido depois dos dados

if 'menu_option' not in st.session_state:
    st.session_state.menu_option = '__home__'

modulos_visiveis = modulos_permitidos if modulos_permitidos else [
    "Dashboard","Positivação","Inadimplência","Clientes sem Compra",
    "Histórico","Preço Médio","Pedidos Pendentes","Rankings"
]

# ══════════════════════════════════════════════════════════════════
# CSS GLOBAL — injetado uma única vez no topo do fluxo de página
# Cobre: sidebar radio, cards home (overlay + visual), métricas,
# gráficos, botões, filtros — tudo em um único bloco.
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family: 'Inter','Segoe UI',sans-serif !important; }
.stApp { background-color: var(--background-color) !important; }

/* ── Remove padding padrão das colunas (alinha cards) ── */
div[data-testid="stHorizontalBlock"] { gap: 10px !important; }
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}
div[data-testid="column"] { padding: 0 !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--secondary-background-color) !important;
    border-right: 1px solid rgba(128,128,128,0.2) !important;
}
section[data-testid="stSidebar"] .stRadio > label { display:none !important; }
section[data-testid="stSidebar"] .stRadio > div {
    display: flex !important; flex-direction: column !important; gap: 1px !important;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
    padding: 9px 12px 9px 10px !important;
    border-radius: 0 10px 10px 0 !important;
    border-left: 3px solid transparent !important;
    margin: 0 !important; cursor: pointer !important;
    transition: all 0.15s !important; align-items: center !important;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
    background: rgba(31,71,136,0.08) !important; border-left-color: #8EB3E8 !important;
}
section[data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
    background: linear-gradient(90deg,#EEF3FC,#F4F7FD) !important;
    border-left-color: #4A7BC8 !important;
}
section[data-testid="stSidebar"] .stRadio label[aria-checked="true"] p {
    color: #4A7BC8 !important; font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stRadio div[class*="RadioMark"],
section[data-testid="stSidebar"] .stRadio div[class*="RadioMarkFill"],
section[data-testid="stSidebar"] .stRadio svg { display:none !important; }
section[data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] p {
    font-size: 0.88rem !important; color: #495057 !important;
    padding: 0 !important; margin: 0 !important;
}

/* ── HOME: card visual (div.med-card) ── */
div.med-card {
    background: #FFFFFF;
    border: 1px solid #E4E9F0;
    border-radius: 14px;
    padding: 20px 18px 16px;
    min-height: 138px;
    box-shadow: 0 1px 5px rgba(31,71,136,0.06);
    transition: box-shadow 0.18s, transform 0.18s, border-color 0.18s;
    cursor: pointer;
    position: relative;
    box-sizing: border-box;
}
div.med-card:hover {
    border-color: #B8CDF0 !important;
    box-shadow: 0 7px 22px rgba(31,71,136,0.14) !important;
    transform: translateY(-3px);
}

/* ── HOME: botão overlay invisível sobre o card ── */
div.med-card-col div[data-testid="stButton"] > button {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    height: 138px !important;
    margin-top: -148px !important;
    opacity: 0 !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
    z-index: 99 !important;
    padding: 0 !important;
}

div.med-card .mc-icon {
    width: 38px; height: 38px;
    background: #EEF3FC; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 11px; color: #4A7BC8; font-size: 16px;
}
div.med-card .mc-title {
    font-size: 0.94rem; font-weight: 700;
    color: #2C5AA0; margin-bottom: 4px; letter-spacing: -0.01em;
}
div.med-card .mc-desc {
    font-size: 0.75rem; color: #6C757D; line-height: 1.4; margin-bottom: 9px;
}
div.med-card .mc-info {
    font-size: 0.70rem; color: #ADB5BD;
    border-top: 1px solid #F0F2F5; padding-top: 7px;
}

/* ── HOME: botão overlay invisível sobre o card ──
   O Streamlit renderiza o st.button logo após o st.markdown na mesma coluna.
   Usamos margin-top negativo para "subir" o botão sobre o card,
   e deixamos opacity:0 para ser invisível mas clicável. ── */
div.med-card-col div[data-testid="stButton"] > button {
    position: relative !important;
    display: block !important;
    width: 100% !important;
    height: 138px !important;
    margin-top: -148px !important;
    opacity: 0 !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
    z-index: 99 !important;
    padding: 0 !important;
}

/* ── Métricas ── */
[data-testid="stMetric"] {
    background: var(--secondary-background-color) !important; border-radius: 12px !important;
    padding: 16px 18px !important; border-left: 4px solid #1F4788 !important;
    box-shadow: 0 1px 6px rgba(31,71,136,0.07) !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.71rem !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.06em !important;
    color: #8A96A8 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important; font-weight: 700 !important; color: #2C5AA0 !important;
}

/* ── Botões gerais ── */
.stButton > button {
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 0.875rem !important;
}

/* ── Filtros ── */
div[data-testid="stHorizontalBlock"].filter-bar { background: #F2F5FA !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [aria-selected="true"] {
    background: #1F4788 !important; color: #FFFFFF !important; font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar: st.radio com labels com ícone Unicode ────────────────────────
_ICONES_NAV = {
    "Dashboard":"▦","Positivação":"✓","Inadimplência":"⚠",
    "Clientes sem Compra":"＋","Histórico":"◷","Preço Médio":"＄",
    "Pedidos Pendentes":"▣","Rankings":"▲",
}
_ICONES_CARD = {
    "Dashboard":"▦","Positivação":"✓","Inadimplência":"⚠",
    "Clientes sem Compra":"＋","Histórico":"◷","Preço Médio":"＄",
    "Pedidos Pendentes":"▣","Rankings":"▲",
}

with st.sidebar:
    st.markdown("""<div style="font-size:0.62rem;font-weight:700;color:#ADB5BD;
        letter-spacing:0.1em;text-transform:uppercase;
        margin-bottom:5px;padding-left:4px;">Navegação</div>""",
        unsafe_allow_html=True)

    # Botão Início
    if st.button("🏠  Início", key="nav_home", use_container_width=True, 
                 type="primary" if st.session_state.menu_option == '__home__' else "secondary"):
        st.session_state.menu_option = '__home__'
        st.rerun()
    
    # Botões dos módulos
    for modulo in modulos_visiveis:
        icone = _ICONES_NAV.get(modulo, '•')
        is_selected = (st.session_state.menu_option == modulo)
        
        if st.button(f"{icone}  {modulo}", 
                    key=f"nav_{modulo}", 
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"):
            st.session_state.menu_option = modulo
            st.rerun()

# ── Tela Home ─────────────────────────────────────────────────────────────
if st.session_state.menu_option == '__home__':
    usuario_info = st.session_state.get("usuario", {})

    try:
        vendas_mes = notas_unicas[
            (notas_unicas['DataEmissao'].dt.month == pd.Timestamp.now().month) &
            (notas_unicas['DataEmissao'].dt.year == pd.Timestamp.now().year)
        ]['Valor_Real'].sum()
    except:
        vendas_mes = 0
    try:
        total_clientes = len(df['RazaoSocial'].unique())
    except:
        total_clientes = 0

    cards_data = [
        {'nome':'Dashboard',          'info':f'R$ {vendas_mes:,.0f} no mês atual'},
        {'nome':'Positivação',         'info':f'{total_clientes} clientes na base'},
        {'nome':'Inadimplência',       'info':'Títulos em aberto e atrasos'},
        {'nome':'Clientes sem Compra', 'info':'Identificar inativos'},
        {'nome':'Histórico',           'info':'Por cliente ou vendedor'},
        {'nome':'Preço Médio',         'info':'Análise por produto'},
        {'nome':'Pedidos Pendentes',   'info':'Aguardando faturamento'},
        {'nome':'Rankings',            'info':'Top vendedores e clientes'},
    ]
    cards_visiveis = [c for c in cards_data if c['nome'] in modulos_visiveis]

    st.markdown(f"""
    <div style="margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #E9ECEF;">
        <div style="font-size:1.45rem;font-weight:600;color:#2C5AA0;margin-bottom:3px;">
            Olá, {usuario_info.get('nome','Usuário')}
        </div>
        <div style="color:#8A96A8;font-size:0.87rem;">
            Selecione um módulo abaixo para iniciar a análise.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Grid 4 colunas — técnica de botão overlay que FUNCIONA
    _USE_CARD_LIB = False  # streamlit-card substituído por st.button nativo

    # ── CSS dos cards home (st.button nativo — sem iframe) ─────────────
    st.markdown("""
    <style>
    /* Grade responsiva: 4 colunas desktop, 2 no mobile */
    div.home-nav div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    @media (max-width: 768px) {
        div.home-nav div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        div.home-nav div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: calc(50% - 5px) !important;
            flex: 1 1 calc(50% - 5px) !important;
            min-width: calc(50% - 5px) !important;
            max-width: calc(50% - 5px) !important;
            box-sizing: border-box !important;
        }
    }
    /* Botão estilizado como card azul institucional */
    div.home-nav div[data-testid="stButton"] > button {
        background: #1F4788 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 18px 14px !important;
        min-height: 130px !important;
        height: auto !important;
        width: 100% !important;
        text-align: left !important;
        white-space: pre-wrap !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        line-height: 1.5 !important;
        box-shadow: 0 2px 8px rgba(31,71,136,0.20) !important;
        transition: all 0.18s ease !important;
        cursor: pointer !important;
        box-sizing: border-box !important;
    }
    div.home-nav div[data-testid="stButton"] > button:hover {
        background: #163561 !important;
        box-shadow: 0 6px 20px rgba(31,71,136,0.35) !important;
        transform: translateY(-2px) !important;
    }
    div.home-nav div[data-testid="stButton"] > button p {
        color: #FFFFFF !important;
        white-space: pre-wrap !important;
        text-align: left !important;
        margin: 0 !important;
        font-size: 0.88rem !important;
        line-height: 1.5 !important;
    }
    @media (max-width: 768px) {
        div.home-nav div[data-testid="stButton"] > button {
            padding: 14px 10px !important;
            min-height: 110px !important;
            font-size: 0.78rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Grid 4 colunas (CSS faz wrap para 2 no mobile) ────────────────────
    st.markdown('<div class="home-nav">', unsafe_allow_html=True)
    for row_start in range(0, len(cards_visiveis), 4):
        row = cards_visiveis[row_start:row_start+4]
        cols = st.columns(4, gap="small")
        for j, c in enumerate(row):
            with cols[j]:
                nome = c['nome']
                desc = _DESC.get(nome, '')
                info = c['info']
                ic   = _ICONES_CARD.get(nome, '•')
                lbl  = f"{ic}  {nome}\n{desc}\n\n{info}"
                if st.button(lbl, key=f"hc_{nome}", use_container_width=True):
                    st.session_state.menu_option = nome
                    st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── Módulo ativo ──────────────────────────────────────────────────────────
menu = st.session_state.menu_option

st.markdown(f"""
<div style="font-size:0.74rem;color:#ADB5BD;margin-bottom:14px;
            padding-bottom:10px;border-bottom:1px solid #F0F2F5;">
    <span style="color:#6C757D;">Início</span>
    <span style="margin:0 6px;color:#D0D5DE;">›</span>
    <span style="color:#4A7BC8;font-weight:600;">{menu}</span>
</div>
""", unsafe_allow_html=True)

if menu not in modulos_permitidos:
    st.markdown("""
    <div style="background:#FFF3F3;border:1px solid #F5C6CB;border-radius:10px;
                padding:16px 20px;color:#721C24;font-size:0.9rem;">
        Acesso negado. Você não tem permissão para acessar este módulo.
    </div>""", unsafe_allow_html=True)
    st.stop()
# ====================== DASHBOARD ======================
if menu == "Dashboard":
    # KPIs principais com cards customizados
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        vendas_brutas = notas_unicas[notas_unicas['TipoMov'] == 'NF Venda']['TotalProduto'].sum()
        render_kpi_card("Faturamento Bruto", f"R$ {vendas_brutas:,.0f}", icon="💰", color="#1F4788")
    
    with col2:
        faturamento_liquido = notas_unicas['Valor_Real'].sum()
        render_kpi_card("Faturamento Líquido", f"R$ {faturamento_liquido:,.0f}", icon="💵", color="#10B981")
    
    with col3:
        clientes_unicos = df_filtrado['CPF_CNPJ'].nunique()
        render_kpi_card("Clientes Únicos", f"{clientes_unicos:,}", icon="👥", color="#F59E0B")
    
    with col4:
        total_notas = len(notas_unicas[notas_unicas['TipoMov'] == 'NF Venda'])
        render_kpi_card("Notas de Venda", f"{total_notas:,}", icon="📄", color="#EF4444")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Segunda linha de KPIs
    col1b, col2b, col3b, col4b = st.columns(4)
    
    with col1b:
        total_devolucoes = notas_unicas[notas_unicas['TipoMov'] == 'NF Dev.Venda']['TotalProduto'].sum()
        render_kpi_card("Devoluções", f"R$ {total_devolucoes:,.0f}", icon="↩️", color="#E5E7EB")
    
    with col2b:
        ticket_medio = vendas_brutas / clientes_unicos if clientes_unicos > 0 else 0
        render_kpi_card("Ticket Médio", f"R$ {ticket_medio:,.0f}", icon="🎯", color="#E5E7EB")
    
    with col3b:
        qtd_notas_dev = len(notas_unicas[notas_unicas['TipoMov'] == 'NF Dev.Venda'])
        render_kpi_card("Notas Devolução", f"{qtd_notas_dev:,}", icon="📋", color="#E5E7EB")
    
    with col4b:
        taxa_devolucao = (total_devolucoes / vendas_brutas * 100) if vendas_brutas > 0 else 0
        render_kpi_card("Taxa Devolução", f"{taxa_devolucao:.1f}%", icon="📊", color="#E5E7EB")
    
    st.markdown("---")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("📈 Evolução de Vendas Brutas")
        # Filtra apenas vendas (sem devoluções) para o gráfico
        vendas_apenas = notas_unicas[notas_unicas['TipoMov'] == 'NF Venda']
        vendas_tempo = vendas_apenas.groupby('MesAno')['TotalProduto'].sum().reset_index()
        vendas_tempo = vendas_tempo.sort_values('MesAno')
        
        if len(vendas_tempo) > 0:
            fig_linha = px.line(
                vendas_tempo, 
                x='MesAno', 
                y='TotalProduto',
                labels={'MesAno': 'Período', 'TotalProduto': 'Valor (R$)'}
            )
            fig_linha.update_traces(line_color='#1F4788', line_width=3, mode='lines+markers', marker=dict(size=6, color='#1F4788'))
            fig_linha.update_layout(
                xaxis_title="Período",
                yaxis_title="Valor (R$)",
                hovermode='x unified'
            )
            fig_linha = aplicar_layout_grafico(fig_linha)
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Sem dados para exibir no período selecionado")
    
    with col6:
        st.subheader("🗺️ Top 10 Estados")
        # Filtra apenas vendas (sem devoluções)
        vendas_estado_apenas = notas_unicas[notas_unicas['TipoMov'] == 'NF Venda']
        vendas_estado = vendas_estado_apenas.groupby('Estado')['TotalProduto'].sum().reset_index()
        vendas_estado = vendas_estado.sort_values('TotalProduto', ascending=False).head(10)
        
        fig_bar = px.bar(
            vendas_estado, 
            x='Estado', 
            y='TotalProduto',
            labels={'Estado': 'Estado', 'TotalProduto': 'Valor (R$)'},
            color='TotalProduto',
            color_discrete_sequence=['#2E86AB']
        )
        fig_bar = aplicar_layout_grafico(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    col7, col8 = st.columns(2)
    
    with col7:
        st.subheader("👥 Positivação por Vendedor")
        vendas_periodo = df_filtrado[df_filtrado['TipoMov'] == 'NF Venda']
        atendidos = vendas_periodo.groupby('Vendedor')['CPF_CNPJ'].nunique().reset_index()
        atendidos.columns = ['Vendedor', 'Clientes']
        atendidos = atendidos.sort_values('Clientes', ascending=False).head(10)
        
        fig_posit = px.bar(
            atendidos,
            x='Vendedor',
            y='Clientes',
            labels={'Vendedor': 'Vendedor', 'Clientes': 'Clientes Atendidos'},
            color='Clientes',
            color_discrete_sequence=['#1F4788']
        )
        fig_posit = aplicar_layout_grafico(fig_posit)
        st.plotly_chart(fig_posit, use_container_width=True)
    
    with col8:
        st.subheader("🏆 Top 10 Clientes")
        # Filtra apenas vendas
        vendas_clientes = notas_unicas[notas_unicas['TipoMov'] == 'NF Venda']
        ranking_clientes = vendas_clientes.groupby('RazaoSocial')['TotalProduto'].sum().reset_index()
        ranking_clientes = ranking_clientes.sort_values('TotalProduto', ascending=False).head(10)
        
        fig_clientes = px.bar(
            ranking_clientes,
            x='TotalProduto',
            y='RazaoSocial',
            orientation='h',
            labels={'RazaoSocial': 'Cliente', 'TotalProduto': 'Valor (R$)'},
            color='TotalProduto',
            color_discrete_sequence=['#4A7BC8']
        )
        fig_clientes = aplicar_layout_grafico(fig_clientes)
        st.plotly_chart(fig_clientes, use_container_width=True)
    
    st.markdown("---")
    
    col9, col10 = st.columns(2)
    
    with col9:
        st.subheader("⚠️ Clientes sem Compra (Top 10)")
        clientes_com_venda = set(df_filtrado[df_filtrado['TipoMov'] == 'NF Venda']['CPF_CNPJ'].unique())
        todos_clientes = df.sort_values('DataEmissao').groupby('CPF_CNPJ').last().reset_index()
        valor_historico = df[df['TipoMov'] == 'NF Venda'].groupby('CPF_CNPJ')['TotalProduto'].sum().reset_index()
        valor_historico.columns = ['CPF_CNPJ', 'ValorHistorico']
        
        todos_clientes = pd.merge(todos_clientes, valor_historico, on='CPF_CNPJ', how='left')
        todos_clientes['ValorHistorico'] = todos_clientes['ValorHistorico'].fillna(0)
        
        clientes_sem_compra = todos_clientes[~todos_clientes['CPF_CNPJ'].isin(clientes_com_venda)]
        clientes_sem_compra = clientes_sem_compra.sort_values('ValorHistorico', ascending=False).head(10)
        
        fig_churn = px.bar(
            clientes_sem_compra,
            x='ValorHistorico',
            y='RazaoSocial',
            orientation='h',
            labels={'RazaoSocial': 'Cliente', 'ValorHistorico': 'Valor Histórico (R$)'},
            color='ValorHistorico',
            color_discrete_sequence=['#1F4788']
        )
        fig_churn = aplicar_layout_grafico(fig_churn)
        st.plotly_chart(fig_churn, use_container_width=True)
    
    with col10:
        st.subheader("📊 Ranking de Vendedores")
        # Filtra apenas vendas
        vendas_vendedores = notas_unicas[notas_unicas['TipoMov'] == 'NF Venda']
        ranking_vendedores = vendas_vendedores.groupby('Vendedor')['TotalProduto'].sum().reset_index()
        ranking_vendedores = ranking_vendedores.sort_values('TotalProduto', ascending=False).head(10)
        
        fig_rank_vend = px.bar(
            ranking_vendedores,
            x='TotalProduto',
            y='Vendedor',
            orientation='h',
            labels={'Vendedor': 'Vendedor', 'TotalProduto': 'Valor Total (R$)'},
            color='TotalProduto',
            color_discrete_sequence=['#163561']
        )
        fig_rank_vend = aplicar_layout_grafico(fig_rank_vend)
        st.plotly_chart(fig_rank_vend, use_container_width=True)

# ====================== POSITIVAÇÃO ======================
elif menu == "Positivação":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">Relatório de Positivação</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 Por Vendedor", "🗺️ Por Estado"])
    
    with tab1:
        base_vendedor = df.groupby('Vendedor')['CPF_CNPJ'].nunique().reset_index()
        base_vendedor.columns = ['Vendedor', 'TotalBase']
        
        vendas_periodo = df_filtrado[df_filtrado['TipoMov'] == 'NF Venda']
        atendidos = vendas_periodo.groupby('Vendedor')['CPF_CNPJ'].nunique().reset_index()
        atendidos.columns = ['Vendedor', 'QtdAtendidos']
        
        valor_vendedor = obter_notas_unicas(vendas_periodo).groupby('Vendedor')['Valor_Real'].sum().reset_index()
        valor_vendedor.columns = ['Vendedor', 'ValorTotal']
        
        relatorio_positivacao = pd.merge(base_vendedor, atendidos, on='Vendedor', how='left')
        relatorio_positivacao = pd.merge(relatorio_positivacao, valor_vendedor, on='Vendedor', how='left')
        relatorio_positivacao['QtdAtendidos'] = relatorio_positivacao['QtdAtendidos'].fillna(0).astype(int)
        relatorio_positivacao['ValorTotal'] = relatorio_positivacao['ValorTotal'].fillna(0)
        relatorio_positivacao['Percentual'] = (relatorio_positivacao['QtdAtendidos'] / relatorio_positivacao['TotalBase'] * 100).round(1)
        relatorio_positivacao = relatorio_positivacao.sort_values('QtdAtendidos', ascending=False)
        
        fig_posit_vend = px.bar(
            relatorio_positivacao.head(15),
            x='Vendedor',
            y='Percentual',
            labels={'Vendedor': 'Vendedor', 'Percentual': 'Positivação (%)'},
            color='Percentual',
            color_discrete_sequence=['#1F4788'],
            title='Top 15 Vendedores - Taxa de Positivação'
        )
        fig_posit_vend = aplicar_layout_grafico(fig_posit_vend)
        st.plotly_chart(fig_posit_vend, use_container_width=True)
        
        # Formatar para exibição
        relatorio_positivacao_display = formatar_dataframe_moeda(relatorio_positivacao, ['ValorTotal'])
        st.dataframe(relatorio_positivacao_display, use_container_width=True)
        
        st.download_button(
            "📥 Exportar Positivação por Vendedor",
            to_excel(relatorio_positivacao),
            "positivacao_vendedor.xlsx",
            "application/vnd.ms-excel"
        )
        
        st.markdown("---")
        
        st.subheader("📋 Detalhamento de Clientes")
        vendedor_selecionado = st.selectbox(
            "Selecione o vendedor",
            relatorio_positivacao['Vendedor'].tolist()
        )
        
        if vendedor_selecionado:
            notas_vendedor = obter_notas_unicas(vendas_periodo[vendas_periodo['Vendedor'] == vendedor_selecionado])
            
            clientes_vendedor = notas_vendedor.groupby(['CPF_CNPJ', 'RazaoSocial', 'Cidade', 'Estado']).agg({
                'Valor_Real': 'sum'
            }).reset_index()
            clientes_vendedor.columns = ['CPF/CNPJ', 'Razão Social', 'Cidade', 'Estado', 'Valor Total']
            clientes_vendedor = clientes_vendedor.sort_values('Valor Total', ascending=False)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Clientes Atendidos", len(clientes_vendedor))
            with col2:
                st.metric("Valor Total", f"R$ {clientes_vendedor['Valor Total'].sum():,.2f}")
            
            # Formatar para exibição
            clientes_vendedor_display = formatar_dataframe_moeda(clientes_vendedor, ['Valor Total'])
            st.dataframe(clientes_vendedor_display, use_container_width=True)
            
            st.download_button(
                f"📥 Exportar Clientes - {vendedor_selecionado}",
                to_excel(clientes_vendedor),
                f"clientes_{vendedor_selecionado}.xlsx",
                "application/vnd.ms-excel"
            )
    
    with tab2:
        st.subheader("🗺️ Positivação por Estado")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            vendedor_estado_filtro = st.selectbox(
                "Filtrar por Vendedor",
                ['Todos'] + sorted(df['Vendedor'].dropna().unique().tolist()),
                key="vend_estado"
            )
        with col_f2:
            ano_estado_filtro = st.selectbox(
                "Filtrar por Ano",
                ['Todos'] + sorted(df['Ano'].dropna().unique().tolist(), reverse=True),
                key="ano_estado"
            )
        
        df_estado_filtrado = df_filtrado.copy()
        if vendedor_estado_filtro != 'Todos':
            df_estado_filtrado = df_estado_filtrado[df_estado_filtrado['Vendedor'] == vendedor_estado_filtro]
        if ano_estado_filtro != 'Todos':
            df_estado_filtrado = df_estado_filtrado[df_estado_filtrado['Ano'] == ano_estado_filtro]
        
        base_estado = df.groupby('Estado')['CPF_CNPJ'].nunique().reset_index()
        base_estado.columns = ['Estado', 'TotalBase']
        
        vendas_estado = df_estado_filtrado[df_estado_filtrado['TipoMov'] == 'NF Venda']
        atendidos_estado = vendas_estado.groupby('Estado')['CPF_CNPJ'].nunique().reset_index()
        atendidos_estado.columns = ['Estado', 'QtdAtendidos']
        
        valor_estado = obter_notas_unicas(vendas_estado).groupby('Estado')['Valor_Real'].sum().reset_index()
        valor_estado.columns = ['Estado', 'ValorTotal']
        
        relatorio_estado = pd.merge(base_estado, atendidos_estado, on='Estado', how='left')
        relatorio_estado = pd.merge(relatorio_estado, valor_estado, on='Estado', how='left')
        relatorio_estado['QtdAtendidos'] = relatorio_estado['QtdAtendidos'].fillna(0).astype(int)
        relatorio_estado['ValorTotal'] = relatorio_estado['ValorTotal'].fillna(0)
        relatorio_estado['Percentual'] = (relatorio_estado['QtdAtendidos'] / relatorio_estado['TotalBase'] * 100).round(1)
        relatorio_estado = relatorio_estado.sort_values('Percentual', ascending=False)
        
        fig_posit_estado = px.bar(
            relatorio_estado.head(15),
            x='Estado',
            y='Percentual',
            labels={'Estado': 'Estado', 'Percentual': 'Positivação (%)'},
            color='Percentual',
            color_discrete_sequence=['#2E86AB'],
            title='Top 15 Estados - Taxa de Positivação'
        )
        fig_posit_estado = aplicar_layout_grafico(fig_posit_estado)
        st.plotly_chart(fig_posit_estado, use_container_width=True)
        
        # Formatar para exibição
        relatorio_estado_display = formatar_dataframe_moeda(relatorio_estado, ['ValorTotal'])
        st.dataframe(relatorio_estado_display, use_container_width=True)
        
        st.download_button(
            "📥 Exportar Positivação por Estado",
            to_excel(relatorio_estado),
            "positivacao_estado.xlsx",
            "application/vnd.ms-excel"
        )

# ====================== INADIMPLÊNCIA ======================
elif menu == "Inadimplência":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">Relatório de Inadimplência</h2>', unsafe_allow_html=True)
    
    # Verificar se a planilha de inadimplência existe
    if not planilhas_disponiveis['inadimplencia']:
        st.error("❌ Planilha de inadimplência não encontrada")
        st.info("💡 Para usar este módulo, adicione no GitHub um arquivo com 'LANCAMENTO A RECEBER' no nome")
        st.info(f"📂 Local: {GITHUB_REPO}/{GITHUB_FOLDER}/")
        st.info("📋 Colunas necessárias: Funcionário, Razão Social, N_Doc, Dt.Vencimento, Vr.Líquido, Conta/Caixa, UF")
        st.stop()
    
    # Carregar dados de inadimplência
    with st.spinner("📥 Carregando dados de inadimplência..."):
        df_inadimplencia = carregar_planilha_github(planilhas_disponiveis['inadimplencia']['url'])
    
    if df_inadimplencia is not None and len(df_inadimplencia) > 0:
        df_inadimplencia = processar_inadimplencia(df_inadimplencia)
        
        
        # ========== FILTROS ==========
        st.subheader("🔍 Filtros")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            vendedores_inad = ['Todos'] + sorted(df_inadimplencia['Vendedor'].dropna().unique().tolist())
            vendedor_inad_filtro = st.selectbox("Vendedor", vendedores_inad, key="vend_inad")
        
        with col_f2:
            estados_inad = ['Todos'] + sorted(df_inadimplencia['Estado'].dropna().unique().tolist())
            estado_inad_filtro = st.selectbox("Estado", estados_inad, key="est_inad")
        
        data_inicial_inad, data_final_inad = renderizar_filtros_locais("inad", "📅 Ajustar Período de Vencimento")
        
        # Aplicar filtros
        df_inad_filtrado = df_inadimplencia.copy()
        
        if vendedor_inad_filtro != 'Todos':
            df_inad_filtrado = df_inad_filtrado[df_inad_filtrado['Vendedor'] == vendedor_inad_filtro]
        if estado_inad_filtro != 'Todos':
            df_inad_filtrado = df_inad_filtrado[df_inad_filtrado['Estado'] == estado_inad_filtro]
        if data_inicial_inad:
            df_inad_filtrado = df_inad_filtrado[df_inad_filtrado['DataVencimento'] >= pd.to_datetime(data_inicial_inad)]
        if data_final_inad:
            df_inad_filtrado = df_inad_filtrado[df_inad_filtrado['DataVencimento'] <= pd.to_datetime(data_final_inad)]
        
        st.markdown("---")
        
        # ========== CARDS DE RESUMO ==========
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_inadimplencia = df_inad_filtrado['ValorLiquido'].sum()
            st.metric("Total em Aberto", f"R$ {total_inadimplencia:,.2f}")
        
        with col2:
            qtd_titulos = len(df_inad_filtrado)
            st.metric("Qtd. Títulos", f"{qtd_titulos:,}")
        
        with col3:
            clientes_inadimplentes = df_inad_filtrado['Cliente'].nunique()
            st.metric("Clientes Inadimplentes", f"{clientes_inadimplentes:,}")
        
        with col4:
            atraso_medio = df_inad_filtrado['DiasAtraso'].mean()
            st.metric("Atraso Médio", f"{atraso_medio:.0f} dias")
        
        st.markdown("---")
        
        # ========== GRÁFICOS ==========
        col5, col6 = st.columns(2)
        
        with col5:
            st.subheader("📊 Inadimplência por Faixa de Atraso")
            
            # Ordenar faixas corretamente
            ordem_faixas = ['A Vencer', '1-30 dias', '31-60 dias', '61-90 dias', 'Acima de 90 dias']
            inad_por_faixa = df_inad_filtrado.groupby('FaixaAtraso')['ValorLiquido'].sum().reset_index()
            inad_por_faixa['FaixaAtraso'] = pd.Categorical(inad_por_faixa['FaixaAtraso'], categories=ordem_faixas, ordered=True)
            inad_por_faixa = inad_por_faixa.sort_values('FaixaAtraso')
            
            fig_faixa = px.bar(
                inad_por_faixa,
                x='FaixaAtraso',
                y='ValorLiquido',
                labels={'FaixaAtraso': 'Faixa de Atraso', 'ValorLiquido': 'Valor (R$)'},
                color='ValorLiquido',
                color_discrete_sequence=['#1F4788']
            )
            fig_faixa = aplicar_layout_grafico(fig_faixa)
        st.plotly_chart(fig_faixa, use_container_width=True)
        
        with col6:
            st.subheader("🏦 Inadimplência por Banco")
            inad_por_banco = df_inad_filtrado.groupby('Banco')['ValorLiquido'].sum().reset_index()
            inad_por_banco = inad_por_banco.sort_values('ValorLiquido', ascending=False).head(10)
            
            fig_banco = px.bar(
                inad_por_banco,
                x='ValorLiquido',
                y='Banco',
                orientation='h',
                labels={'Banco': 'Banco', 'ValorLiquido': 'Valor (R$)'},
                color='ValorLiquido',
                color_discrete_sequence=['#1F4788']
            )
            fig_banco = aplicar_layout_grafico(fig_banco)
        st.plotly_chart(fig_banco, use_container_width=True)
        
        st.markdown("---")
        
        col7, col8 = st.columns(2)
        
        with col7:
            st.subheader("👤 Top 10 Vendedores - Inadimplência")
            
            # Verificar se as colunas necessárias existem
            if 'NumeroDoc' not in df_inad_filtrado.columns:
                # Tentar encontrar coluna alternativa
                possiveis_nomes = [col for col in df_inad_filtrado.columns if 'DOC' in col.upper() or 'NUMERO' in col.upper()]
                if possiveis_nomes:
                    df_inad_filtrado['NumeroDoc'] = df_inad_filtrado[possiveis_nomes[0]]
                else:
                    # Criar coluna fake apenas para não quebrar
                    df_inad_filtrado['NumeroDoc'] = 1
            
            inad_por_vendedor = df_inad_filtrado.groupby('Vendedor').agg({
                'ValorLiquido': 'sum',
                'NumeroDoc': 'count'
            }).reset_index()
            inad_por_vendedor.columns = ['Vendedor', 'Valor', 'QtdTitulos']
            inad_por_vendedor = inad_por_vendedor.sort_values('Valor', ascending=False).head(10)
            
            fig_vend_inad = px.bar(
                inad_por_vendedor,
                x='Vendedor',
                y='Valor',
                labels={'Vendedor': 'Vendedor', 'Valor': 'Valor (R$)'},
                color='Valor',
                color_discrete_sequence=['#4A7BC8']
            )
            fig_vend_inad = aplicar_layout_grafico(fig_vend_inad)
        st.plotly_chart(fig_vend_inad, use_container_width=True)
        
        with col8:
            st.subheader("🗺️ Top 10 Estados - Inadimplência")
            inad_por_estado = df_inad_filtrado.groupby('Estado')['ValorLiquido'].sum().reset_index()
            inad_por_estado = inad_por_estado.sort_values('ValorLiquido', ascending=False).head(10)
            
            fig_est_inad = px.bar(
                inad_por_estado,
                x='Estado',
                y='ValorLiquido',
                labels={'Estado': 'Estado', 'ValorLiquido': 'Valor (R$)'},
                color='ValorLiquido',
                color_discrete_sequence=['#163561']
            )
            fig_est_inad = aplicar_layout_grafico(fig_est_inad)
        st.plotly_chart(fig_est_inad, use_container_width=True)
        
        st.markdown("---")
        
        # ========== TABELA DETALHADA ==========
        st.subheader("📋 Detalhamento dos Títulos")
        
        # Preparar dados para exibição
        df_detalhado = df_inad_filtrado[[
            'Vendedor', 'Cliente', 'NumeroDoc', 'DataVencimento', 
            'ValorLiquido', 'DiasAtraso', 'FaixaAtraso', 'Banco', 'Estado'
        ]].copy()
        
        # Formatar data
        df_detalhado['DataVencimento'] = df_detalhado['DataVencimento'].dt.strftime('%d/%m/%Y')
        
        # Formatar valores para exibição
        df_detalhado_display = df_detalhado.copy()
        df_detalhado_display['ValorLiquido'] = df_detalhado_display['ValorLiquido'].apply(
            lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00"
        )
        
        # Renomear colunas
        df_detalhado_display = df_detalhado_display.rename(columns={
            'Vendedor': 'Vendedor',
            'Cliente': 'Cliente',
            'NumeroDoc': 'Nº Documento',
            'DataVencimento': 'Vencimento',
            'ValorLiquido': 'Valor em Aberto',
            'DiasAtraso': 'Dias Atraso',
            'FaixaAtraso': 'Faixa',
            'Banco': 'Banco',
            'Estado': 'UF'
        })
        
        # Ordenar por dias de atraso (maior para menor)
        df_detalhado_display = df_detalhado_display.sort_values('Dias Atraso', ascending=False)
        
        st.dataframe(df_detalhado_display, use_container_width=True, height=400)
        
        # Botão de download
        st.download_button(
            "📥 Exportar Relatório Completo",
            to_excel(df_detalhado),
            "relatorio_inadimplencia.xlsx",
            "application/vnd.ms-excel"
        )

# ====================== CLIENTES SEM COMPRA ======================
elif menu == "Clientes sem Compra":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">️ Clientes sem Compra no Período</h2>', unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        vendedor_churn_filtro = st.selectbox(
            "Filtrar por Vendedor",
            ['Todos'] + sorted(df['Vendedor'].dropna().unique().tolist()),
            key="vend_churn"
        )
    with col_f2:
        estado_churn_filtro = st.selectbox(
            "Filtrar por Estado",
            ['Todos'] + sorted(df['Estado'].dropna().unique().tolist()),
            key="est_churn"
        )
    with col_f3:
        ordem = st.selectbox(
            "Ordenar por",
            ["Valor Histórico (Maior)", "Valor Histórico (Menor)", "Nome (A-Z)", "Última Compra (Mais Recente)"],
            key="ordem_churn"
        )
    with col_f4:
        busca_cliente_churn = st.text_input(
            "🔍 Buscar Cliente",
            placeholder="Digite o nome...",
            key="busca_churn"
        )
    
    clientes_com_venda = set(df_filtrado[df_filtrado['TipoMov'] == 'NF Venda']['CPF_CNPJ'].unique())
    todos_clientes = df.sort_values('DataEmissao').groupby('CPF_CNPJ').last().reset_index()
    valor_historico = df[df['TipoMov'] == 'NF Venda'].groupby('CPF_CNPJ')['TotalProduto'].sum().reset_index()
    valor_historico.columns = ['CPF_CNPJ', 'ValorHistorico']
    
    todos_clientes = pd.merge(todos_clientes, valor_historico, on='CPF_CNPJ', how='left')
    todos_clientes['ValorHistorico'] = todos_clientes['ValorHistorico'].fillna(0)
    
    clientes_sem_compra = todos_clientes[~todos_clientes['CPF_CNPJ'].isin(clientes_com_venda)]
    clientes_sem_compra = clientes_sem_compra[['RazaoSocial', 'CPF_CNPJ', 'Vendedor', 'Cidade', 'Estado', 'ValorHistorico']]
    
    if vendedor_churn_filtro != 'Todos':
        clientes_sem_compra = clientes_sem_compra[clientes_sem_compra['Vendedor'] == vendedor_churn_filtro]
    if estado_churn_filtro != 'Todos':
        clientes_sem_compra = clientes_sem_compra[clientes_sem_compra['Estado'] == estado_churn_filtro]
    
    # Filtro de busca por nome do cliente
    if busca_cliente_churn and len(busca_cliente_churn) >= 2:
        clientes_sem_compra = clientes_sem_compra[
            clientes_sem_compra['RazaoSocial'].str.contains(busca_cliente_churn, case=False, na=False)
        ]
    
    if ordem == "Valor Histórico (Maior)":
        clientes_sem_compra = clientes_sem_compra.sort_values('ValorHistorico', ascending=False)
    elif ordem == "Valor Histórico (Menor)":
        clientes_sem_compra = clientes_sem_compra.sort_values('ValorHistorico', ascending=True)
    elif ordem == "Nome (A-Z)":
        clientes_sem_compra = clientes_sem_compra.sort_values('RazaoSocial')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Clientes sem Compra", len(clientes_sem_compra))
    with col2:
        st.metric("Valor Potencial Perdido", f"R$ {clientes_sem_compra['ValorHistorico'].sum():,.2f}")
    with col3:
        ticket_medio_churn = clientes_sem_compra['ValorHistorico'].mean() if len(clientes_sem_compra) > 0 else 0
        st.metric("Ticket Médio Histórico", f"R$ {ticket_medio_churn:,.2f}")
    
    if len(clientes_sem_compra) > 0:
        top_churn = clientes_sem_compra.head(15)
        fig_churn = px.bar(
            top_churn,
            x='ValorHistorico',
            y='RazaoSocial',
            orientation='h',
            labels={'RazaoSocial': 'Cliente', 'ValorHistorico': 'Valor Histórico (R$)'},
            color='ValorHistorico',
            color_discrete_sequence=['#1F4788'],
            title='Top 15 Clientes sem Compra por Valor Histórico'
        )
        fig_churn = aplicar_layout_grafico(fig_churn)
        st.plotly_chart(fig_churn, use_container_width=True)
    
    # Formatar para exibição
    clientes_sem_compra_display = formatar_dataframe_moeda(clientes_sem_compra, ['ValorHistorico'])
    
    # Renomear colunas para exibição
    clientes_sem_compra_display = clientes_sem_compra_display.rename(columns={
        'RazaoSocial': 'Razão Social',
        'CPF_CNPJ': 'CPF/CNPJ',
        'Vendedor': 'Vendedor',
        'Cidade': 'Cidade',
        'Estado': 'Estado',
        'ValorHistorico': 'Valor Histórico'
    })
    
    st.dataframe(clientes_sem_compra_display, use_container_width=True, height=400)
    
    st.download_button(
        "📥 Exportar Clientes sem Compra",
        to_excel(clientes_sem_compra),
        "clientes_sem_compra.xlsx",
        "application/vnd.ms-excel"
    )

# ====================== HISTÓRICO ======================
elif menu == "Histórico":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">Histórico de Vendas</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👤 Por Cliente", "🧑‍💼 Por Vendedor", "📝 Pedidos"])
    
    # ========== ABA: POR CLIENTE ==========
    with tab1:
        st.subheader("Histórico de Vendas por Cliente")
        
        # Buscar cliente por CPF/CNPJ ou Nome
        col_busca1, col_busca2 = st.columns(2)
        
        with col_busca1:
            busca_tipo = st.radio("Buscar por:", ["Nome", "CPF/CNPJ"], horizontal=True, key="busca_tipo_cliente")
        
        with col_busca2:
            if busca_tipo == "Nome":
                busca_texto = st.text_input("Digite o nome do cliente", placeholder="Ex: Nome da Empresa", key="busca_nome_cliente")
            else:
                busca_texto = st.text_input("Digite o CPF/CNPJ", placeholder="Ex: 12345678901234", key="busca_cpf_cliente")
        
        cliente_selecionado = None
        cpf_cnpj = None
        
        if busca_texto and len(busca_texto) >= 3:
            if busca_tipo == "Nome":
                clientes_filtrados = df[df['RazaoSocial'].str.contains(busca_texto, case=False, na=False)][['CPF_CNPJ', 'RazaoSocial', 'Cidade', 'Estado']].drop_duplicates()
            else:
                clientes_filtrados = df[df['CPF_CNPJ'].str.contains(busca_texto, case=False, na=False)][['CPF_CNPJ', 'RazaoSocial', 'Cidade', 'Estado']].drop_duplicates()
            
            if len(clientes_filtrados) > 0:
                clientes_filtrados['Display'] = clientes_filtrados['RazaoSocial'] + " - " + clientes_filtrados['CPF_CNPJ'] + " (" + clientes_filtrados['Cidade'] + "/" + clientes_filtrados['Estado'] + ")"
                
                cliente_selecionado = st.selectbox(
                    f"📋 Clientes encontrados ({len(clientes_filtrados)}):",
                    options=clientes_filtrados['Display'].tolist(),
                    key="cliente_hist"
                )
                
                if cliente_selecionado:
                    cpf_cnpj = cliente_selecionado.split(' - ')[1].split(' (')[0]
            else:
                st.warning("❌ Nenhum cliente encontrado com esse critério")
        
        if cpf_cnpj:
            historico = df[df['CPF_CNPJ'] == cpf_cnpj].sort_values('DataEmissao', ascending=False)
            
            if len(historico) > 0:
                cliente_info = historico.iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Cliente", cliente_info['RazaoSocial'])
                with col2:
                    st.metric("CPF/CNPJ", cliente_info['CPF_CNPJ'])
                with col3:
                    st.metric("Cidade/Estado", f"{cliente_info['Cidade']}/{cliente_info['Estado']}")
                with col4:
                    st.metric("Total de Registros", len(historico))
                
                st.markdown("---")
                
                vendas_cliente = historico[historico['TipoMov'] == 'NF Venda']
                devolucoes_cliente = historico[historico['TipoMov'] == 'NF Dev.Venda']
                
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    st.metric("Total Vendas", f"R$ {vendas_cliente['TotalProduto'].sum():,.2f}")
                with col6:
                    st.metric("Total Devoluções", f"R$ {devolucoes_cliente['TotalProduto'].sum():,.2f}")
                with col7:
                    st.metric("Qtd Notas Vendas", len(vendas_cliente['Numero_NF'].unique()))
                with col8:
                    st.metric("Qtd Notas Devoluções", len(devolucoes_cliente['Numero_NF'].unique()))
                
                vendas_tempo_cliente = vendas_cliente.groupby('MesAno')['TotalProduto'].sum().reset_index()
                vendas_tempo_cliente = vendas_tempo_cliente.sort_values('MesAno')
                
                if len(vendas_tempo_cliente) > 0:
                    fig_hist = px.line(
                        vendas_tempo_cliente,
                        x='MesAno',
                        y='TotalProduto',
                        labels={'MesAno': 'Período', 'TotalProduto': 'Valor (R$)'},
                        title='Evolução de Compras'
                    )
                    fig_hist.update_traces(line_color='#28A745', line_width=3, mode='lines+markers', marker=dict(size=6, color='#28A745'))
                    fig_hist = aplicar_layout_grafico(fig_hist)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                st.markdown("---")
                
                st.subheader("📋 Detalhamento de Produtos")
                
                # Verificar se PrazoHistorico e Comissao existem no dataframe
                colunas_display = ['DataEmissao', 'TipoMov', 'Numero_NF', 'CodigoProduto', 'NomeProduto', 'Quantidade', 'PrecoUnit', 'TotalProduto']
                if 'PrazoHistorico' in historico.columns:
                    colunas_display.append('PrazoHistorico')
                if 'Comissao' in historico.columns:
                    colunas_display.append('Comissao')
                
                historico_display = historico[colunas_display].copy()
                historico_display['DataEmissao'] = historico_display['DataEmissao'].dt.strftime('%d/%m/%Y')
                
                # Formatar valores monetários
                historico_display['PrecoUnit'] = historico_display['PrecoUnit'].apply(lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00")
                historico_display['TotalProduto'] = historico_display['TotalProduto'].apply(lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00")
                
                # Renomear colunas
                colunas_rename = {
                    'DataEmissao': 'Data',
                    'TipoMov': 'Tipo',
                    'Numero_NF': 'Nota Fiscal',
                    'CodigoProduto': 'Código',
                    'NomeProduto': 'Produto',
                    'Quantidade': 'Qtd',
                    'PrecoUnit': 'Preço Unit.',
                    'TotalProduto': 'Total'
                }
                if 'PrazoHistorico' in historico_display.columns:
                    colunas_rename['PrazoHistorico'] = 'Prazo (dias)'
                if 'Comissao' in historico_display.columns:
                    colunas_rename['Comissao'] = 'Comissão%'
                
                historico_display = historico_display.rename(columns=colunas_rename)
                
                st.dataframe(historico_display, use_container_width=True, height=400)
                
                st.download_button(
                    "📥 Exportar Histórico Excel",
                    to_excel(historico),
                    f"historico_{cpf_cnpj}.xlsx",
                    "application/vnd.ms-excel",
                    key="dl_hist_excel"
                )

                st.markdown("---")
                st.markdown("""
                <div style="background:#F0F4FF;border:1px solid #C5D5F0;border-radius:10px;
                            padding:14px 18px;margin-bottom:8px;">
                    <div style="font-size:0.88rem;font-weight:700;color:#4A7BC8;margin-bottom:4px;">
                        Gerar Proposta Comercial PDF
                    </div>
                    <div style="font-size:0.78rem;color:#6C757D;">
                        Exporta os produtos do histórico do cliente em formato de proposta
                        comercial com cabeçalho Medtextil, dados do cliente e tabela de itens.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                _col_pdf1, _col_pdf2 = st.columns([2, 1])
                with _col_pdf1:
                    _vendas_resumo = {
                        'Total de Vendas':   f"R$ {vendas_cliente['TotalProduto'].sum():,.2f}",
                        'Total Devoluções':  f"R$ {devolucoes_cliente['TotalProduto'].sum():,.2f}",
                        'Notas de Venda':    str(len(vendas_cliente['Numero_NF'].unique())),
                        'Clientes (CNPJ)':   cpf_cnpj,
                    }
                    _cliente_info_dict = {
                        'RazaoSocial': cliente_info.get('RazaoSocial',''),
                        'CPF_CNPJ':    cpf_cnpj,
                        'Cidade':      cliente_info.get('Cidade',''),
                        'Estado':      cliente_info.get('Estado',''),
                        'Vendedor':    cliente_info.get('Vendedor',''),
                    }
                    if st.button("Gerar Proposta PDF", key="btn_gerar_proposta",
                                 use_container_width=True, type="primary"):
                        with st.spinner("Gerando proposta..."):
                            try:
                                _pdf_bytes = gerar_proposta_pdf_historico(
                                    _cliente_info_dict, historico, _vendas_resumo
                                )
                                st.session_state['proposta_pdf_bytes'] = _pdf_bytes
                                st.session_state['proposta_pdf_nome'] = (
                                    f"Proposta_{razao_curta}_{hoje_str}.pdf"
                                    if 'razao_curta' in dir() else
                                    f"Proposta_{cpf_cnpj}.pdf"
                                )
                                st.success("Proposta gerada! Clique em Download abaixo.")
                            except Exception as _e:
                                st.error(f"Erro ao gerar proposta: {_e}")

                with _col_pdf2:
                    if st.session_state.get('proposta_pdf_bytes'):
                        import datetime as _dt
                        _nome_pdf = (
                            f"Proposta_Medtextil_{cliente_info.get('RazaoSocial','cliente')[:20].replace(' ','_')}"
                            f"_{_dt.date.today().strftime('%Y%m%d')}.pdf"
                        )
                        st.download_button(
                            "Download PDF",
                            data=st.session_state['proposta_pdf_bytes'],
                            file_name=_nome_pdf,
                            mime="application/pdf",
                            key="dl_proposta_pdf",
                            use_container_width=True
                        )
            else:
                st.warning("Nenhum registro encontrado para este cliente")
        else:
            st.info("👆 Digite pelo menos 3 caracteres para buscar um cliente")
    
    # ========== ABA: POR VENDEDOR ==========
    with tab2:
        st.subheader("Histórico de Vendas por Vendedor")
        
        # Filtros
        col_f1, = st.columns(1)
        
        with col_f1:
            vendedores_hist = ['Todos'] + sorted(df['Vendedor'].dropna().unique().tolist())
            vendedor_hist_filtro = st.selectbox("Vendedor", vendedores_hist, key="vend_hist")
        
        data_inicial_hist, data_final_hist = renderizar_filtros_locais("hist_vend", "📅 Ajustar Período")
        
        # Aplicar filtros
        df_hist_vendedor = df[df['TipoMov'] == 'NF Venda'].copy()
        
        if vendedor_hist_filtro != 'Todos':
            df_hist_vendedor = df_hist_vendedor[df_hist_vendedor['Vendedor'] == vendedor_hist_filtro]
        if data_inicial_hist:
            df_hist_vendedor = df_hist_vendedor[df_hist_vendedor['DataEmissao'] >= pd.to_datetime(data_inicial_hist)]
        if data_final_hist:
            df_hist_vendedor = df_hist_vendedor[df_hist_vendedor['DataEmissao'] <= pd.to_datetime(data_final_hist)]
        
        if len(df_hist_vendedor) > 0:
            # Obter notas únicas e agrupar por NF para somar o valor total
            notas_vendedor = obter_notas_unicas(df_hist_vendedor)
            
            # Preparar dados para exibição
            colunas_vendedor = ['DataEmissao', 'RazaoSocial', 'Numero_NF', 'TotalProduto', 'Vendedor']
            if 'PrazoHistorico' in notas_vendedor.columns:
                colunas_vendedor.append('PrazoHistorico')
            
            historico_vendedor = notas_vendedor[colunas_vendedor].copy()
            historico_vendedor = historico_vendedor.sort_values('DataEmissao', ascending=False)
            
            # Métricas resumidas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Vendas", f"R$ {historico_vendedor['TotalProduto'].sum():,.2f}")
            with col2:
                st.metric("Quantidade de Notas", len(historico_vendedor))
            with col3:
                st.metric("Clientes Atendidos", historico_vendedor['RazaoSocial'].nunique())
            with col4:
                ticket_medio_vend = historico_vendedor['TotalProduto'].mean() if len(historico_vendedor) > 0 else 0
                st.metric("Ticket Médio", f"R$ {ticket_medio_vend:,.2f}")
            
            st.markdown("---")
            
            # Formatar para exibição
            historico_vendedor_display = historico_vendedor.copy()
            historico_vendedor_display['DataEmissao'] = historico_vendedor_display['DataEmissao'].dt.strftime('%d/%m/%Y')
            historico_vendedor_display['TotalProduto'] = historico_vendedor_display['TotalProduto'].apply(
                lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00"
            )
            
            # Renomear colunas
            colunas_rename_vendedor = {
                'DataEmissao': 'Data',
                'RazaoSocial': 'Cliente',
                'Numero_NF': 'Nota Fiscal',
                'TotalProduto': 'Valor Total',
                'Vendedor': 'Vendedor'
            }
            if 'PrazoHistorico' in historico_vendedor_display.columns:
                colunas_rename_vendedor['PrazoHistorico'] = 'Prazo (dias)'
            
            historico_vendedor_display = historico_vendedor_display.rename(columns=colunas_rename_vendedor)
            
            st.dataframe(historico_vendedor_display, use_container_width=True, height=400)
            
            # Botão de download
            st.download_button(
                "📥 Exportar Histórico de Vendas",
                to_excel(historico_vendedor),
                f"historico_vendedor_{vendedor_hist_filtro if vendedor_hist_filtro != 'Todos' else 'todos'}.xlsx",
                "application/vnd.ms-excel",
                key="download_hist_vend"
            )
        else:
            st.info("Nenhuma venda encontrada com os filtros selecionados")

    
    # ========== ABA: PEDIDOS ==========
    with tab3:
        st.subheader("📝 Gerar Pedido/Proposta")
        
        # Inicializar session_state para os itens do pedido
        if 'itens_pedido' not in st.session_state:
            st.session_state.itens_pedido = []
        
        # Carregar dados de produtos se disponível
        df_produtos_pedido = None
        if planilhas_disponiveis.get('produtos_agrupados'):
            with st.spinner("📥 Carregando catálogo de produtos..."):
                df_produtos_pedido = carregar_planilha_github(planilhas_disponiveis['produtos_agrupados']['url'])
                if df_produtos_pedido is not None:
                    df_produtos_pedido.columns = df_produtos_pedido.columns.str.upper()
        
        # SEÇÃO 1: DADOS DO CLIENTE
        st.markdown("### 👤 Informações do Cliente")
        
        col_cli1, col_cli2 = st.columns(2)
        
        with col_cli1:
            # Buscar cliente
            clientes_lista = sorted(df['RazaoSocial'].dropna().unique().tolist())
            cliente_selecionado = st.selectbox("Selecione o Cliente", [''] + clientes_lista, key="cliente_pedido")
        
        # Buscar dados do cliente
        dados_cliente = {}
        if cliente_selecionado:
            df_cliente = df[df['RazaoSocial'] == cliente_selecionado].iloc[0]
            dados_cliente = {
                'razao_social': df_cliente.get('RazaoSocial', ''),
                'cpf_cnpj': df_cliente.get('CPF_CNPJ', ''),
                'cidade': df_cliente.get('Cidade', ''),
                'estado': df_cliente.get('Estado', ''),
                'vendedor': df_cliente.get('Vendedor', '')
            }
        
        with col_cli2:
            representante = st.text_input("Representante", value=dados_cliente.get('vendedor', ''), key="representante_pedido")
        
        col_cli3, col_cli4, col_cli5 = st.columns(3)
        
        with col_cli3:
            nome_fantasia = st.text_input("Nome Fantasia", value=dados_cliente.get('razao_social', ''), key="fantasia_pedido")
        
        with col_cli4:
            cnpj_pedido = st.text_input("CNPJ", value=dados_cliente.get('cpf_cnpj', ''), key="cnpj_pedido")
        
        with col_cli5:
            insc_estadual = st.text_input("Inscrição Estadual", key="ie_pedido")
        
        col_cli6, col_cli7 = st.columns(2)
        
        with col_cli6:
            telefone_pedido = st.text_input("Telefone", key="tel_pedido")
        
        with col_cli7:
            email_pedido = st.text_input("Email NF-e", key="email_pedido")
        
        endereco_pedido = st.text_input("Endereço", value=f"{dados_cliente.get('cidade', '')}/{dados_cliente.get('estado', '')}" if dados_cliente else "", key="end_pedido")
        
        obs_cliente = st.text_area("Observação (Cliente)", key="obs_cli_pedido", height=80)
        
        st.markdown("---")
        
        # SEÇÃO 2: DADOS DO PEDIDO
        st.markdown("### 📋 Informações do Pedido")
        
        col_ped1, col_ped2, col_ped3, col_ped4 = st.columns(4)
        
        with col_ped1:
            num_pedido = st.text_input("Nº do Pedido", key="num_pedido")
        
        with col_ped2:
            tabela_preco = st.text_input("Tabela de Preço", key="tab_preco")
        
        with col_ped3:
            tipo_frete = st.selectbox("Tipo de Frete", ["CIF", "FOB"], key="tipo_frete")
        
        with col_ped4:
            data_venda = st.date_input("Data da Venda", value=pd.Timestamp.now(), key="data_venda")
        
        condicoes_pagto = st.text_input("Condições de Pagamento", key="cond_pagto")
        
        st.markdown("---")
        
        # SEÇÃO 3: ADICIONAR PRODUTOS
        st.markdown("### 🛒 Adicionar Produtos ao Pedido")
        
        col_prod1, col_prod2, col_prod3, col_prod4 = st.columns([2, 1, 1, 1])
        
        with col_prod1:
            # Buscar por código ou descrição
            tipo_busca_prod = st.radio("Buscar por:", ["Código", "Descrição"], horizontal=True, key="tipo_busca_prod")
            
            if tipo_busca_prod == "Código":
                if df_produtos_pedido is not None:
                    codigos = [''] + sorted(df_produtos_pedido['ID_COD'].dropna().astype(str).unique().tolist())
                    codigo_selecionado = st.selectbox("Código do Produto", codigos, key="cod_prod_pedido")
                else:
                    codigo_selecionado = st.text_input("Código do Produto", key="cod_prod_pedido")
            else:
                busca_desc = st.text_input("Descrição do Produto", key="desc_prod_pedido")
                codigo_selecionado = None
        
        # Buscar informações do produto
        produto_info = {}
        if df_produtos_pedido is not None and codigo_selecionado:
            prod = df_produtos_pedido[df_produtos_pedido['ID_COD'].astype(str) == str(codigo_selecionado)]
            if len(prod) > 0:
                prod = prod.iloc[0]
                # Montar descrição completa
                descricao_completa = f"{prod.get('GRUPO', '')} {prod.get('DESCRIÇÃO', '') or prod.get('DESCRICAO', '')} {prod.get('LINHA', '') or prod.get('LINHAS', '')}".strip()
                
                produto_info = {
                    'codigo': str(prod.get('ID_COD', '')),
                    'descricao': descricao_completa,
                    'peso': prod.get('GRAMATURA', ''),
                    'cx_embarque': prod.get('CX_EMB', ''),
                    'preco_ref': prod.get('PRECO', 0)
                }
                
                # Buscar último preço que o cliente comprou
                if cliente_selecionado:
                    hist_cliente = df[(df['RazaoSocial'] == cliente_selecionado) & 
                                     (df['CodigoProduto'].astype(str) == str(codigo_selecionado))]
                    if len(hist_cliente) > 0:
                        hist_cliente = hist_cliente.sort_values('DataEmissao', ascending=False)
                        produto_info['preco_sugerido'] = hist_cliente.iloc[0]['PrecoUnit']
                        produto_info['preco_historico'] = hist_cliente.iloc[0]['PrecoUnit']  # Para mostrar na tabela
                    else:
                        produto_info['preco_sugerido'] = prod.get('PRECO', 0)
                        produto_info['preco_historico'] = prod.get('PRECO', 0)
                else:
                    produto_info['preco_sugerido'] = prod.get('PRECO', 0)
                    produto_info['preco_historico'] = prod.get('PRECO', 0)
        
        with col_prod2:
            qtde_item = st.number_input("Quantidade", min_value=0, value=0, key="qtde_item_pedido")
        
        with col_prod3:
            valor_item = st.number_input("Valor Unit.", min_value=0.0, value=float(produto_info.get('preco_sugerido', 0)), format="%.2f", key="valor_item_pedido")
        
        with col_prod4:
            st.write("")
            st.write("")
            if st.button("➕ Adicionar Item", use_container_width=True, key="add_item_pedido"):
                if produto_info and qtde_item > 0:
                    # Calcular comissão
                    comissao = calcular_comissao(valor_item, produto_info.get('preco_ref', 0))
                    
                    item = {
                        'codigo': produto_info['codigo'],
                        'descricao': produto_info['descricao'],
                        'peso': produto_info.get('peso', ''),
                        'cx_embarque': produto_info.get('cx_embarque', ''),
                        'quantidade': qtde_item,
                        'valor_unit': valor_item,
                        'preco_historico': produto_info.get('preco_historico', 0),
                        'total': qtde_item * valor_item,
                        'comissao': comissao
                    }
                    st.session_state.itens_pedido.append(item)
                    st.success(f"✅ Item adicionado: {produto_info['descricao']}")
                    st.rerun()
        
        # PREVIEW EM TEMPO REAL - Mostrar antes de adicionar
        if produto_info and qtde_item > 0 and valor_item > 0:
            st.markdown("---")
            st.markdown("### 👁️ Preview do Item")
            
            # Calcular valores preview
            total_preview = qtde_item * valor_item
            comissao_preview = calcular_comissao(valor_item, produto_info.get('preco_ref', 0))
            preco_hist_preview = produto_info.get('preco_historico', 0)
            
            # Mostrar em tabela estilizada
            preview_data = {
                'Código': [produto_info['codigo']],
                'Produto': [produto_info['descricao'][:50]],
                'Peso': [produto_info.get('peso', '')],
                'Cx Embarque': [produto_info.get('cx_embarque', '')],
                'Qtde': [f"{qtde_item:,.0f}"],
                'Preço Histórico': [f"R$ {preco_hist_preview:,.2f}"],
                'Valor Unit.': [f"R$ {valor_item:,.2f}"],
                'Total': [f"R$ {total_preview:,.2f}"],
                'Comissão%': [comissao_preview]
            }
            
            df_preview = pd.DataFrame(preview_data)
            st.dataframe(df_preview, use_container_width=True, hide_index=True)
            
            # Comparação com preço histórico
            if preco_hist_preview > 0:
                variacao = ((valor_item - preco_hist_preview) / preco_hist_preview) * 100
                if variacao > 0:
                    st.info(f"📈 Valor {variacao:.1f}% **acima** do histórico (R$ {preco_hist_preview:,.2f})")
                elif variacao < 0:
                    st.warning(f"📉 Valor {abs(variacao):.1f}% **abaixo** do histórico (R$ {preco_hist_preview:,.2f})")
                else:
                    st.success(f"✅ Valor **igual** ao histórico (R$ {preco_hist_preview:,.2f})")
            
            st.markdown("---")
        
        # Mostrar produtos adicionados
        if st.session_state.itens_pedido:
            st.markdown("---")
            st.markdown("### 📦 Itens do Pedido")
            
            # Criar DataFrame dos itens
            df_itens = pd.DataFrame(st.session_state.itens_pedido)
            
            # Formatar para exibição
            df_itens_display = df_itens.copy()
            df_itens_display['preco_historico'] = df_itens_display['preco_historico'].apply(lambda x: f"R$ {x:,.2f}")
            df_itens_display['valor_unit'] = df_itens_display['valor_unit'].apply(lambda x: f"R$ {x:,.2f}")
            df_itens_display['total'] = df_itens_display['total'].apply(lambda x: f"R$ {x:,.2f}")
            
            df_itens_display = df_itens_display.rename(columns={
                'codigo': 'COD.',
                'descricao': 'PRODUTO',
                'peso': 'PESO',
                'cx_embarque': 'CAIXA EMBARQUE',
                'quantidade': 'QTDE',
                'preco_historico': 'PREÇO HISTÓRICO',
                'valor_unit': 'VALOR',
                'total': 'TOTAL',
                'comissao': 'COMISSÃO%'
            })
            
            st.dataframe(df_itens_display, use_container_width=True, height=300)
            
            # Métricas do pedido
            col_met1, col_met2, col_met3 = st.columns(3)
            
            with col_met1:
                total_itens = df_itens['quantidade'].sum()
                st.metric("Qtde Total de Itens", f"{total_itens:,.0f}")
            
            with col_met2:
                st.metric("Frete", tipo_frete)
            
            with col_met3:
                total_pedido = df_itens['total'].sum()
                st.metric("Total Final", f"R$ {total_pedido:,.2f}")
            
            # Observação final
            obs_pedido = st.text_area("Observação (Pedido)", key="obs_pedido", height=100)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🗑️ Limpar Pedido", use_container_width=True, key="limpar_pedido"):
                    st.session_state.itens_pedido = []
                    st.rerun()
            
            with col_btn2:
                if st.button("📄 Gerar PDF do Pedido", use_container_width=True, key="gerar_pdf_pedido", type="primary"):
                    try:
                        # Preparar dados para o PDF
                        dados_cliente_pdf = {
                            'representante': representante,
                            'razao_social': cliente_selecionado,
                            'nome_fantasia': nome_fantasia,
                            'cnpj': cnpj_pedido,
                            'ie': insc_estadual,
                            'telefone': telefone_pedido,
                            'email': email_pedido,
                            'endereco': endereco_pedido,
                            'obs_cliente': obs_cliente
                        }
                        
                        dados_pedido_pdf = {
                            'numero': num_pedido,
                            'tabela_preco': tabela_preco,
                            'tipo_frete': tipo_frete,
                            'data_venda': data_venda.strftime('%d/%m/%Y'),
                            'condicoes_pagto': condicoes_pagto
                        }
                        
                        # Gerar PDF
                        pdf_bytes = gerar_pdf_pedido(dados_cliente_pdf, dados_pedido_pdf, st.session_state.itens_pedido, obs_pedido)
                        
                        # Botão de download
                        st.download_button(
                            label="📥 Baixar PDF do Pedido",
                            data=pdf_bytes,
                            file_name=f"Pedido_{num_pedido or 'SN'}_{cliente_selecionado.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key="download_pdf_pedido"
                        )
                        
                        st.success("✅ PDF gerado com sucesso!")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar PDF: {str(e)}")
                        st.info("💡 Certifique-se de que a biblioteca ReportLab está instalada")
        else:
            st.info("ℹ️ Nenhum item adicionado ao pedido ainda. Use o formulário acima para adicionar produtos.")

# ====================== PREÇO MÉDIO ======================
elif menu == "Preço Médio":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">Análise de Preço Médio por Produto</h2>', unsafe_allow_html=True)
    
    # Verificar se as planilhas necessárias existem
    if not planilhas_disponiveis['vendas_produto']:
        st.error("❌ Planilha 'Vendas por produto - GERAL.xlsx' não encontrada")
        st.info("💡 Adicione no GitHub um arquivo com 'VENDAS POR PRODUTO' e 'GERAL' no nome")
        st.info(f"📂 Local: {GITHUB_REPO}/{GITHUB_FOLDER}/")
        st.info("📋 Colunas necessárias: CODPRODUTO, TOTQTD, PRECOUNITMEDIO, TOTLIQUIDO")
        st.stop()
    
    if not planilhas_disponiveis['produtos_agrupados']:
        st.error("❌ Planilha 'Produtos_Agrupados_Completos_conciliados.xlsx' não encontrada")
        st.info("💡 Adicione no GitHub um arquivo com 'PRODUTOS_AGRUPADOS_COMPLETOS_CONCILIADOS' no nome")
        st.info(f"📂 Local: {GITHUB_REPO}/{GITHUB_FOLDER}/")
        st.info("📋 Colunas necessárias: ID_COD, Grupo, Descrição, Linha, Gramatura")
        st.stop()
    
    # Carregar planilhas
    with st.spinner("📥 Carregando dados de vendas por produto..."):
        df_vendas_produto = carregar_planilha_github(planilhas_disponiveis['vendas_produto']['url'])
    
    with st.spinner("📥 Carregando dados de produtos..."):
        df_produtos = carregar_planilha_github(planilhas_disponiveis['produtos_agrupados']['url'])
    
    if df_vendas_produto is None or df_produtos is None:
        st.error("❌ Erro ao carregar uma ou mais planilhas")
        st.stop()
    
    # Padronizar nomes das colunas (case-insensitive)
    df_vendas_produto.columns = df_vendas_produto.columns.str.upper()
    df_produtos.columns = df_produtos.columns.str.upper()
    
    # IMPORTANTE: Se a planilha de vendas já tiver NOMEPRODUTO, remover para usar apenas o da planilha de produtos
    if 'NOMEPRODUTO' in df_vendas_produto.columns:
        df_vendas_produto = df_vendas_produto.drop(columns=['NOMEPRODUTO'])
    
    # Verificar se as colunas necessárias existem
    colunas_vendas_necessarias = ['CODPRODUTO', 'TOTQTD', 'PRECOUNITMEDIO', 'TOTLIQUIDO']
    colunas_produtos_necessarias = ['ID_COD', 'GRUPO', 'DESCRIÇÃO', 'LINHA', 'GRAMATURA']
    
    # Verificar colunas alternativas
    if 'DESCRIÇÃO' not in df_produtos.columns and 'DESCRICAO' in df_produtos.columns:
        df_produtos = df_produtos.rename(columns={'DESCRICAO': 'DESCRIÇÃO'})
    
    if 'LINHA' not in df_produtos.columns and 'LINHAS' in df_produtos.columns:
        df_produtos = df_produtos.rename(columns={'LINHAS': 'LINHA'})
    
    if 'GRUPO' not in df_produtos.columns and 'GRUPOS' in df_produtos.columns:
        df_produtos = df_produtos.rename(columns={'GRUPOS': 'GRUPO'})
    
    faltando_vendas = [col for col in colunas_vendas_necessarias if col not in df_vendas_produto.columns]
    faltando_produtos = [col for col in colunas_produtos_necessarias if col not in df_produtos.columns]
    
    if faltando_vendas:
        st.error(f"❌ Colunas faltando na planilha de vendas: {', '.join(faltando_vendas)}")
        st.info(f"📋 Colunas encontradas: {', '.join(df_vendas_produto.columns.tolist())}")
        st.stop()
    
    if faltando_produtos:
        st.error(f"❌ Colunas faltando na planilha de produtos: {', '.join(faltando_produtos)}")
        st.info(f"📋 Colunas encontradas: {', '.join(df_produtos.columns.tolist())}")
        st.stop()
    
    # Criar a descrição concatenada na planilha de produtos
    # Limpar espaços e garantir que não fique vazio
    df_produtos['GRUPO_LIMPO'] = df_produtos['GRUPO'].fillna('').astype(str).str.strip()
    df_produtos['DESCRIÇÃO_LIMPO'] = df_produtos['DESCRIÇÃO'].fillna('').astype(str).str.strip()
    df_produtos['LINHA_LIMPO'] = df_produtos['LINHA'].fillna('').astype(str).str.strip()
    
    df_produtos['NOMEPRODUTO'] = (
        df_produtos['GRUPO_LIMPO'] + ' ' +
        df_produtos['DESCRIÇÃO_LIMPO'] + ' ' +
        df_produtos['LINHA_LIMPO']
    ).str.strip()
    
    # Se NOMEPRODUTO ficar vazio, usar o ID_COD como descrição
    df_produtos.loc[df_produtos['NOMEPRODUTO'] == '', 'NOMEPRODUTO'] = 'Produto ' + df_produtos['ID_COD'].astype(str)
    
    # Remover colunas temporárias
    df_produtos = df_produtos.drop(columns=['GRUPO_LIMPO', 'DESCRIÇÃO_LIMPO', 'LINHA_LIMPO'])
    
    # Renomear ID_COD para CODPRODUTO para facilitar o merge
    df_produtos = df_produtos.rename(columns={'ID_COD': 'CODPRODUTO'})
    
    # Adicionar coluna DATA com o mês/ano atual (já que não existe na planilha)
    data_atual = pd.Timestamp.now()
    df_vendas_produto['DATA'] = data_atual
    df_vendas_produto['Mes'] = data_atual.month
    df_vendas_produto['Ano'] = data_atual.year
    df_vendas_produto['MesAno'] = data_atual.strftime('%Y-%m')
    
    # Fazer o merge (PROCV) entre as planilhas
    # Garantir que as colunas necessárias existam antes do merge
    colunas_merge = ['CODPRODUTO', 'NOMEPRODUTO', 'GRAMATURA']
    for col in colunas_merge:
        if col not in df_produtos.columns:
            if col == 'NOMEPRODUTO':
                df_produtos['NOMEPRODUTO'] = 'Produto não catalogado'
            elif col == 'GRAMATURA':
                df_produtos['GRAMATURA'] = 0
    
    df_preco_medio = pd.merge(
        df_vendas_produto,
        df_produtos[colunas_merge],
        on='CODPRODUTO',
        how='left'
    )
    
    # Preencher valores nulos após o merge
    produtos_nao_catalogados = 0
    if 'NOMEPRODUTO' in df_preco_medio.columns:
        produtos_nao_catalogados = df_preco_medio['NOMEPRODUTO'].isna().sum()
        df_preco_medio['NOMEPRODUTO'] = df_preco_medio['NOMEPRODUTO'].fillna('Produto não catalogado - Código: ' + df_preco_medio['CODPRODUTO'].astype(str))
    else:
        df_preco_medio['NOMEPRODUTO'] = 'Produto não catalogado - Código: ' + df_preco_medio['CODPRODUTO'].astype(str)
        produtos_nao_catalogados = len(df_preco_medio)
    
    if 'GRAMATURA' in df_preco_medio.columns:
        df_preco_medio['GRAMATURA'] = df_preco_medio['GRAMATURA'].fillna(0)
    else:
        df_preco_medio['GRAMATURA'] = 0
    
    
    
    st.markdown("---")
    
    # ========== FILTROS ==========
    st.subheader("🔍 Filtros")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        anos_preco = ['Todos'] + sorted(df_preco_medio['Ano'].dropna().unique().tolist(), reverse=True)
        ano_preco_filtro = st.selectbox("Ano", anos_preco, key="ano_preco")
    
    with col_f2:
        meses_preco = ['Todos'] + list(range(1, 13))
        mes_preco_filtro = st.selectbox("Mês", meses_preco, key="mes_preco")
    
    with col_f3:
        busca_cod = st.text_input("🔍 Buscar Código", placeholder="Digite o código...", key="busca_cod_preco")
    
    with col_f4:
        busca_nome = st.text_input("🔍 Buscar Produto", placeholder="Digite o nome...", key="busca_nome_preco")
    
    # Aplicar filtros
    df_preco_filtrado = df_preco_medio.copy()
    
    if ano_preco_filtro != 'Todos':
        df_preco_filtrado = df_preco_filtrado[df_preco_filtrado['Ano'] == ano_preco_filtro]
    if mes_preco_filtro != 'Todos':
        df_preco_filtrado = df_preco_filtrado[df_preco_filtrado['Mes'] == mes_preco_filtro]
    if busca_cod and len(busca_cod) >= 2:
        df_preco_filtrado = df_preco_filtrado[
            df_preco_filtrado['CODPRODUTO'].astype(str).str.contains(busca_cod, case=False, na=False)
        ]
    if busca_nome and len(busca_nome) >= 2:
        df_preco_filtrado = df_preco_filtrado[
            df_preco_filtrado['NOMEPRODUTO'].str.contains(busca_nome, case=False, na=False)
        ]
    
    st.markdown("---")
    
    # ========== MÉTRICAS GERAIS ==========
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_vendido = df_preco_filtrado['TOTLIQUIDO'].sum()
        st.metric("Total Vendido", f"R$ {total_vendido:,.2f}")
    
    with col2:
        qtd_total = df_preco_filtrado['TOTQTD'].sum()
        st.metric("Qtd. Total Vendida", f"{qtd_total:,.0f}")
    
    with col3:
        # CORREÇÃO: Média ponderada = Total Vendido / Quantidade Total
        if df_preco_filtrado['TOTQTD'].sum() > 0:
            preco_medio_geral = df_preco_filtrado['TOTLIQUIDO'].sum() / df_preco_filtrado['TOTQTD'].sum()
        else:
            preco_medio_geral = 0
        st.metric("Preço Médio Geral", f"R$ {preco_medio_geral:,.2f}")
    
    with col4:
        produtos_unicos = df_preco_filtrado['CODPRODUTO'].nunique()
        st.metric("Produtos Únicos", f"{produtos_unicos:,}")
    
    st.markdown("---")
    
    # ========== GRÁFICOS ==========
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("📊 Top 10 Produtos por Faturamento")
        
        top_faturamento = df_preco_filtrado.groupby('NOMEPRODUTO')['TOTLIQUIDO'].sum().reset_index()
        top_faturamento = top_faturamento.sort_values('TOTLIQUIDO', ascending=False).head(10)
        
        fig_fat = px.bar(
            top_faturamento,
            x='TOTLIQUIDO',
            y='NOMEPRODUTO',
            orientation='h',
            labels={'NOMEPRODUTO': 'Produto', 'TOTLIQUIDO': 'Faturamento (R$)'},
            color='TOTLIQUIDO',
            color_discrete_sequence=['#1F4788']
        )
        fig_fat = aplicar_layout_grafico(fig_fat)
        st.plotly_chart(fig_fat, use_container_width=True)
    
    with col6:
        st.subheader("📈 Top 10 Produtos por Quantidade")
        
        top_quantidade = df_preco_filtrado.groupby('NOMEPRODUTO')['TOTQTD'].sum().reset_index()
        top_quantidade = top_quantidade.sort_values('TOTQTD', ascending=False).head(10)
        
        fig_qtd = px.bar(
            top_quantidade,
            x='TOTQTD',
            y='NOMEPRODUTO',
            orientation='h',
            labels={'NOMEPRODUTO': 'Produto', 'TOTQTD': 'Quantidade Vendida'},
            color='TOTQTD',
            color_discrete_sequence=['#2E86AB']
        )
        fig_qtd = aplicar_layout_grafico(fig_qtd)
        st.plotly_chart(fig_qtd, use_container_width=True)
    
    st.markdown("---")
    
    # ========== ANÁLISE DE PREÇO MÉDIO POR PERÍODO ==========
    st.subheader("📅 Evolução de Preço Médio")
    
    # Permitir seleção de produto específico
    produtos_lista = ['Todos'] + sorted(df_preco_filtrado['NOMEPRODUTO'].unique().tolist())
    produto_selecionado = st.selectbox(
        "Selecione um produto para ver evolução de preço:",
        produtos_lista,
        key="produto_evolucao"
    )
    
    if produto_selecionado != 'Todos':
        df_evolucao = df_preco_filtrado[df_preco_filtrado['NOMEPRODUTO'] == produto_selecionado]
    else:
        df_evolucao = df_preco_filtrado.copy()
    
    if len(df_evolucao) > 0:
        evolucao_preco = df_evolucao.groupby('MesAno').agg({
            'PRECOUNITMEDIO': 'mean',
            'TOTQTD': 'sum',
            'TOTLIQUIDO': 'sum'
        }).reset_index()
        evolucao_preco = evolucao_preco.sort_values('MesAno')
        
        fig_evolucao = px.line(
            evolucao_preco,
            x='MesAno',
            y='PRECOUNITMEDIO',
            labels={'MesAno': 'Período', 'PRECOUNITMEDIO': 'Preço Médio (R$)'},
            title=f'Evolução do Preço Médio - {produto_selecionado}'
        )
        fig_evolucao.update_traces(line_color='#FF6B6B', line_width=3)
        fig_evolucao = aplicar_layout_grafico(fig_evolucao)
        st.plotly_chart(fig_evolucao, use_container_width=True)
    
    st.markdown("---")
    
    # ========== TABELA DETALHADA ==========
    st.subheader("📋 Detalhamento de Preços")
    
    # Preparar dados para exibição
    df_detalhado = df_preco_filtrado[[
        'CODPRODUTO', 'NOMEPRODUTO', 'GRAMATURA', 'TOTQTD', 
        'PRECOUNITMEDIO', 'TOTLIQUIDO', 'DATA'
    ]].copy()
    
    # Ordenar por data (mais recente primeiro)
    df_detalhado = df_detalhado.sort_values('DATA', ascending=False)
    
    # Formatar para exibição
    df_detalhado_display = df_detalhado.copy()
    
    # Formatar data no padrão brasileiro com mês atual
    mes_atual = data_atual.month
    ano_atual = data_atual.year
    df_detalhado_display['DATA'] = f"{mes_atual:02d}/{ano_atual}"
    
    df_detalhado_display['PRECOUNITMEDIO'] = df_detalhado_display['PRECOUNITMEDIO'].apply(
        lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00"
    )
    df_detalhado_display['TOTLIQUIDO'] = df_detalhado_display['TOTLIQUIDO'].apply(
        lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00"
    )
    
    # Renomear colunas
    df_detalhado_display = df_detalhado_display.rename(columns={
        'CODPRODUTO': 'Código',
        'NOMEPRODUTO': 'Nome do Produto',
        'GRAMATURA': 'Gramatura',
        'TOTQTD': 'Qtd Vendida',
        'PRECOUNITMEDIO': 'Preço Médio Unit.',
        'TOTLIQUIDO': 'Total Líquido',
        'DATA': 'Período (Mês/Ano)'
    })
    
    st.dataframe(df_detalhado_display, use_container_width=True, height=400)
    
    # Botão de download
    st.download_button(
        "📥 Exportar Relatório de Preços",
        to_excel(df_detalhado),
        "relatorio_preco_medio.xlsx",
        "application/vnd.ms-excel",
        key="download_preco_medio"
    )

# ====================== PEDIDOS PENDENTES ======================
elif menu == "Pedidos Pendentes":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">Pedidos Pendentes de Faturamento</h2>', unsafe_allow_html=True)
    
    # Verificar se a planilha existe
    if not planilhas_disponiveis.get('pedidos_pendentes'):
        st.error("❌ Planilha 'PEDIDOSPENDENTES.xlsx' não encontrada")
        st.info("💡 Adicione no GitHub um arquivo com 'PEDIDOSPENDENTES' no nome")
        st.info(f"📂 Local: {GITHUB_REPO}/{GITHUB_FOLDER}/")
        st.stop()
    
    # Carregar planilha
    with st.spinner("📥 Carregando pedidos pendentes..."):
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            from io import BytesIO
            
            # Baixar arquivo
            response = requests.get(planilhas_disponiveis['pedidos_pendentes']['url'])
            excel_file = BytesIO(response.content)
            
            # Extrair shared strings
            with zipfile.ZipFile(excel_file) as z:
                with z.open('xl/sharedStrings.xml') as f:
                    strings_tree = ET.parse(f)
                    ns_str = {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    shared_strings = [si.text if si.text else '' for si in strings_tree.findall('.//ss:t', ns_str)]
                
                # Extrair sheet
                with z.open('xl/worksheets/sheet1.xml') as f:
                    sheet_tree = ET.parse(f)
                    ns = {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    
                    # Parsear dados
                    data = []
                    current_client = None
                    current_pedido = None
                    
                    for row in sheet_tree.findall('.//ss:row', ns):
                        row_data = {}
                        for cell in row.findall('.//ss:c', ns):
                            ref = cell.get('r', '')
                            col = ''.join([c for c in ref if c.isalpha()])
                            v_elem = cell.find('.//ss:v', ns)
                            if v_elem is not None and v_elem.text:
                                val_type = cell.get('t', 'n')
                                if val_type == 's':
                                    idx = int(v_elem.text)
                                    value = shared_strings[idx] if idx < len(shared_strings) else v_elem.text
                                else:
                                    value = v_elem.text
                                row_data[col] = value
                        
                        if not row_data:
                            continue
                        
                        # Detectar tipo de linha
                        col_a = row_data.get('A', '')
                        col_b = row_data.get('B', '')
                        
                        # Linha de cliente (apenas coluna A preenchida com nome)
                        if col_a and not col_b and 'N° do pedido' not in col_a and 'Valor Total' not in col_a and col_a != 'Subgrupo:':
                            current_client = col_a
                        
                        # Linha de pedido (tem "N° do pedido:")
                        elif 'N° do pedido' in col_a:
                            current_pedido = col_b
                            
                            # Extrair dados do produto
                            descricao = row_data.get('C', '')
                            if descricao and ' - ' in descricao:
                                # Extrair código do produto (ex: "476 - ATADURA...")
                                codigo_produto = descricao.split(' - ')[0].strip()
                                
                                try:
                                    qtd_contratada = float(row_data.get('D', 0))
                                    valor_unit = float(row_data.get('E', 0))  # Corrigido: E é o valor unitário
                                    qtd_entregue = float(row_data.get('H', 0))  # Corrigido: H é qtd entregue
                                    qtd_pendente = qtd_contratada - qtd_entregue
                                    valor_pendente = qtd_pendente * valor_unit
                                    
                                    # Converter data de emissão (coluna G)
                                    dt_emissao_val = row_data.get('G', '')
                                    if dt_emissao_val:
                                        try:
                                            # Data vem como número (days since 1900)
                                            dt_emissao = pd.Timestamp('1899-12-30') + pd.Timedelta(days=float(dt_emissao_val))
                                        except:
                                            dt_emissao = None
                                    else:
                                        dt_emissao = None
                                    
                                    data.append({
                                        'Cliente': current_client,
                                        'NumeroPedido': current_pedido,
                                        'CodigoProduto': codigo_produto,
                                        'Descricao': descricao,
                                        'QtdContratada': qtd_contratada,
                                        'QtdEntregue': qtd_entregue,
                                        'QtdPendente': qtd_pendente,
                                        'ValorUnit': valor_unit,
                                        'ValorPendente': valor_pendente,
                                        'DataEmissao': dt_emissao,
                                        'Vendedor': row_data.get('J', ''),  # Corrigido: J é o vendedor
                                        'PercEntregue': float(row_data.get('I', 0))  # Corrigido: I é % entregue
                                    })
                                except:
                                    continue
            
            df_pendentes = pd.DataFrame(data)
            
            if len(df_pendentes) == 0:
                st.warning("⚠️ Nenhum pedido pendente encontrado na planilha")
                st.stop()
            
            
        except Exception as e:
            st.error(f"❌ Erro ao processar planilha: {str(e)}")
            st.stop()
    
    st.markdown("---")
    
    # Filtros
    st.subheader("🔍 Filtros")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        clientes_pend = ['Todos'] + sorted(df_pendentes['Cliente'].dropna().unique().tolist())
        cliente_pend_filtro = st.selectbox("Cliente", clientes_pend, key="cli_pend")
    
    with col_f2:
        vendedores_pend = ['Todos'] + sorted(df_pendentes['Vendedor'].dropna().unique().tolist())
        vendedor_pend_filtro = st.selectbox("Vendedor", vendedores_pend, key="vend_pend")
    
    with col_f3:
        busca_produto = st.text_input("🔍 Buscar Produto", placeholder="Digite código ou descrição", key="busca_prod_pend")
    
    with col_f4:
        apenas_pendentes = st.checkbox("Apenas com pendência", value=True, key="apenas_pend")
    
    # Aplicar filtros
    df_pend_filtrado = df_pendentes.copy()
    
    if cliente_pend_filtro != 'Todos':
        df_pend_filtrado = df_pend_filtrado[df_pend_filtrado['Cliente'] == cliente_pend_filtro]
    if vendedor_pend_filtro != 'Todos':
        df_pend_filtrado = df_pend_filtrado[df_pend_filtrado['Vendedor'] == vendedor_pend_filtro]
    if busca_produto:
        df_pend_filtrado = df_pend_filtrado[
            df_pend_filtrado['CodigoProduto'].str.contains(busca_produto, case=False, na=False) |
            df_pend_filtrado['Descricao'].str.contains(busca_produto, case=False, na=False)
        ]
    if apenas_pendentes:
        df_pend_filtrado = df_pend_filtrado[df_pend_filtrado['QtdPendente'] > 0]
    
    st.markdown("---")
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pendente = df_pend_filtrado['ValorPendente'].sum()
        st.metric("Valor Total Pendente", f"R$ {total_pendente:,.2f}")
    
    with col2:
        qtd_pendente = df_pend_filtrado['QtdPendente'].sum()
        st.metric("Qtd. Total Pendente", f"{qtd_pendente:,.0f}")
    
    with col3:
        pedidos_unicos = df_pend_filtrado['NumeroPedido'].nunique()
        st.metric("Pedidos Únicos", f"{pedidos_unicos:,}")
    
    with col4:
        perc_medio = df_pend_filtrado['PercEntregue'].mean() if len(df_pend_filtrado) > 0 else 0
        st.metric("% Médio Entregue", f"{perc_medio:.1f}%")
    
    st.markdown("---")
    
    # Gráficos
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("🏢 Top 10 Clientes - Valor Pendente")
        top_clientes = df_pend_filtrado.groupby('Cliente')['ValorPendente'].sum().reset_index()
        top_clientes = top_clientes.sort_values('ValorPendente', ascending=False).head(10)
        
        fig_cli = px.bar(
            top_clientes,
            x='ValorPendente',
            y='Cliente',
            orientation='h',
            labels={'Cliente': 'Cliente', 'ValorPendente': 'Valor Pendente (R$)'},
            color='ValorPendente',
            color_discrete_sequence=['#1F4788']
        )
        fig_cli = aplicar_layout_grafico(fig_cli)
        st.plotly_chart(fig_cli, use_container_width=True)
    
    with col6:
        st.subheader("👤 Top 10 Vendedores - Valor Pendente")
        top_vend = df_pend_filtrado.groupby('Vendedor')['ValorPendente'].sum().reset_index()
        top_vend = top_vend.sort_values('ValorPendente', ascending=False).head(10)
        
        fig_vend = px.bar(
            top_vend,
            x='ValorPendente',
            y='Vendedor',
            orientation='h',
            labels={'Vendedor': 'Vendedor', 'ValorPendente': 'Valor Pendente (R$)'},
            color='ValorPendente',
            color_discrete_sequence=['#4A7BC8']
        )
        fig_vend = aplicar_layout_grafico(fig_vend)
        st.plotly_chart(fig_vend, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela detalhada
    st.subheader("📋 Detalhamento de Pedidos Pendentes")
    
    # Preparar dados para exibição
    df_pend_display = df_pend_filtrado[[
        'Cliente', 'NumeroPedido', 'CodigoProduto', 'Descricao', 
        'QtdContratada', 'QtdEntregue', 'QtdPendente',
        'ValorUnit', 'ValorPendente', 'PercEntregue', 'DataEmissao', 'Vendedor'
    ]].copy()
    
    # Formatar valores
    df_pend_display['ValorUnit'] = df_pend_display['ValorUnit'].apply(
        lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00"
    )
    df_pend_display['ValorPendente'] = df_pend_display['ValorPendente'].apply(
        lambda x: formatar_moeda(x) if pd.notnull(x) else "R$ 0,00"
    )
    df_pend_display['DataEmissao'] = df_pend_display['DataEmissao'].apply(
        lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else ''
    )
    df_pend_display['PercEntregue'] = df_pend_display['PercEntregue'].apply(
        lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%"
    )
    
    # Renomear colunas
    df_pend_display = df_pend_display.rename(columns={
        'Cliente': 'Cliente',
        'NumeroPedido': 'N° Pedido',
        'CodigoProduto': 'Código',
        'Descricao': 'Descrição',
        'QtdContratada': 'Qtd Contratada',
        'QtdEntregue': 'Qtd Entregue',
        'QtdPendente': 'Qtd Pendente',
        'ValorUnit': 'Valor Unit.',
        'ValorPendente': 'Valor Pendente',
        'PercEntregue': '% Entregue',
        'DataEmissao': 'Data Emissão',
        'Vendedor': 'Vendedor'
    })
    
    st.dataframe(df_pend_display, use_container_width=True, height=400)
    
    # Botão de download
    st.download_button(
        "📥 Exportar Pedidos Pendentes (Separado por Tipo)",
        to_excel_pedidos_pendentes(df_pend_filtrado),
        "pedidos_pendentes.xlsx",
        "application/vnd.ms-excel",
        key="download_pendentes"
    )

# ====================== RANKINGS ======================
elif menu == "Rankings":
    st.markdown('<h2 style="color:#4A7BC8;font-weight:700;margin-bottom:4px;font-size:1.35rem;">Rankings</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 Vendedores", "👥 Clientes"])
    
    with tab1:
        st.subheader("Ranking de Vendedores por Valor")
        
        ranking_vendedores = notas_unicas.groupby('Vendedor').agg({
            'Valor_Real': 'sum',
            'Numero_NF': 'count',
            'CPF_CNPJ': 'nunique'
        }).reset_index()
        ranking_vendedores.columns = ['Vendedor', 'Valor Total', 'Qtd Notas', 'Qtd Clientes']
        ranking_vendedores = ranking_vendedores.sort_values('Valor Total', ascending=False)
        ranking_vendedores.insert(0, 'Posição', range(1, len(ranking_vendedores) + 1))
        
        fig_rank_vend = px.bar(
            ranking_vendedores.head(15),
            x='Vendedor',
            y='Valor Total',
            labels={'Vendedor': 'Vendedor', 'Valor Total': 'Valor Total (R$)'},
            color='Valor Total',
            color_discrete_sequence=['#163561'],
            title='Top 15 Vendedores por Valor'
        )
        fig_rank_vend = aplicar_layout_grafico(fig_rank_vend)
        st.plotly_chart(fig_rank_vend, use_container_width=True)
        
        # Formatar para exibição
        ranking_vendedores_display = formatar_dataframe_moeda(ranking_vendedores, ['Valor Total'])
        st.dataframe(ranking_vendedores_display, use_container_width=True)
        
        st.download_button(
            "📥 Exportar Ranking Vendedores",
            to_excel(ranking_vendedores),
            "ranking_vendedores.xlsx",
            "application/vnd.ms-excel"
        )
    
    with tab2:
        st.subheader("Ranking de Clientes por Valor")
        
        top_n = st.selectbox("Exibir Top:", [10, 20, 50, 100], key="top_clientes")
        
        ranking_clientes = notas_unicas.groupby(['CPF_CNPJ', 'RazaoSocial', 'Cidade', 'Estado']).agg({
            'Valor_Real': 'sum',
            'Numero_NF': 'count'
        }).reset_index()
        ranking_clientes.columns = ['CPF/CNPJ', 'Razão Social', 'Cidade', 'Estado', 'Valor Total', 'Qtd Notas']
        ranking_clientes = ranking_clientes.sort_values('Valor Total', ascending=False).head(top_n)
        ranking_clientes.insert(0, 'Posição', range(1, len(ranking_clientes) + 1))
        
        fig_rank_cli = px.bar(
            ranking_clientes.head(15),
            x='Valor Total',
            y='Razão Social',
            orientation='h',
            labels={'Razão Social': 'Cliente', 'Valor Total': 'Valor Total (R$)'},
            color='Valor Total',
            color_discrete_sequence=['#4A7BC8'],
            title=f'Top 15 Clientes por Valor'
        )
        fig_rank_cli = aplicar_layout_grafico(fig_rank_cli)
        st.plotly_chart(fig_rank_cli, use_container_width=True)
        
        # Formatar para exibição
        ranking_clientes_display = formatar_dataframe_moeda(ranking_clientes, ['Valor Total'])
        st.dataframe(ranking_clientes_display, use_container_width=True)
        
        st.download_button(
            "📥 Exportar Ranking Clientes",
            to_excel(ranking_clientes),
            f"ranking_top{top_n}_clientes.xlsx",
            "application/vnd.ms-excel"
        )

st.markdown("""
<hr style="border-color:#E9ECEF;margin-top:32px;margin-bottom:12px;">
<div style="text-align:center;color:#ADB5BD;font-size:0.78rem;padding-bottom:16px;">
    Dashboard BI Medtextil 2.0 &nbsp;·&nbsp; Desenvolvido com Streamlit
    &nbsp;·&nbsp; <span style="color:#4A7BC8;font-weight:600;">Medtextil Produtos Textil Hospitalares</span>
</div>
""", unsafe_allow_html=True)
