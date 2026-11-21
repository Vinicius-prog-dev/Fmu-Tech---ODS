"""Identidade visual e componentes reutilizados pelas telas do Streamlit."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from src.banco import carregar_dados
from src.regras import calcular_tudo

RAIZ = Path(__file__).resolve().parents[1]
LOGO = RAIZ / "assets" / "logo.jpeg"

# Paleta oficial (tirada do logotipo + cores de alerta)
CORES = {
    "azul": "#1A63AB",
    "azul_claro": "#3FA6EA",
    "verde": "#0BBF62",
    "ambar": "#F9A825",
    "vermelho": "#D32F2F",
    "fundo": "#F5F7FA",
    "texto": "#1F2937",
    "cinza": "#9CA3AF",
}

COR_VALIDADE = {
    "Vencido": CORES["vermelho"],
    "Crítico": "#EF6C00",
    "Atenção": CORES["ambar"],
    "OK": CORES["verde"],
}
COR_ESTOQUE = {
    "Em falta": CORES["vermelho"],
    "Escasso": CORES["ambar"],
    "Adequado": CORES["verde"],
    "Excesso": CORES["azul_claro"],
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700&family=Roboto:wght@400;500&display=swap');
html, body, [class*="css"], .stMarkdown, .stDataFrame {{ font-family: 'Roboto', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Inter', sans-serif !important; color: {CORES['azul']}; }}
div[data-testid="stMetric"] {{
    background: white; border-radius: 12px; padding: 14px 18px;
    border-left: 6px solid {CORES['azul']}; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}}
div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {{
    color: {CORES['texto']} !important; font-weight: 500; white-space: normal !important;
}}
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {{
    color: {CORES['azul']} !important; font-family: 'Inter', sans-serif; font-weight: 700;
    font-size: 1.7rem !important; white-space: normal !important; overflow: visible !important;
}}
</style>
"""


def configurar_pagina(titulo: str, icone: str = "🏥") -> None:
    st.set_page_config(page_title=f"{titulo} · Estoque Vital", page_icon=icone, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    if LOGO.exists():
        st.sidebar.image(str(LOGO))
    st.sidebar.caption(f"Dados de referência: {date.today():%d/%m/%Y}")


@st.cache_data(ttl=3600, show_spinner="Carregando dados do estoque...")
def obter_resultados(dia: str) -> dict:
    """Carrega o banco e roda as regras. O cache é renovado a cada dia."""
    dados = carregar_dados(date.fromisoformat(dia))
    resultado = calcular_tudo(dados, date.fromisoformat(dia))
    resultado["ubs"] = dados["ubs"]
    return resultado


def resultados_de_hoje() -> dict:
    return obter_resultados(date.today().isoformat())


def moeda(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def numero(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def colorir(coluna_status: str, mapa: dict):
    """Função para Styler.map: pinta a célula de status com a cor correspondente."""
    def _estilo(valor):
        cor = mapa.get(valor)
        return f"background-color: {cor}; color: white; font-weight: 600" if cor else ""
    return _estilo


def rodape() -> None:
    st.divider()
    st.markdown(
        "<p class='ev-aviso'>Medicamentos e preços: <b>Banco de Preços em Saúde (BPS) 2026 – "
        "Ministério da Saúde</b> (dados reais). UBSs, estoques, lotes e consumo: "
        "<b>dados simulados</b> a partir das compras reais de Porto Alegre, para fins de protótipo.</p>",
        unsafe_allow_html=True,
    )
