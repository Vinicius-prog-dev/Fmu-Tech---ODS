"""
Geração dos dados SIMULADOS (mockados) do Estoque Vital.

Não existe base pública com o estoque e os lotes de cada UBS, então estes dados
são gerados a partir da base REAL do BPS:
- os medicamentos e seus preços vêm de data/medicamentos_referencia.csv (BPS 2026);
- o consumo mensal de cada UBS é estimado a partir da quantidade anual comprada
  pelo município piloto (Porto Alegre).

As datas de validade são criadas em relação à data de hoje, para que o painel
sempre tenha lotes vencidos, a vencer e em dia - inclusive no dia da apresentação.
A semente aleatória é fixa, então o cenário é sempre o mesmo.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

# UBSs fictícias com nomes de bairros de Porto Alegre e um fator de porte
UBS = [
    ("UBS01", "UBS Centro", "Centro Histórico", 1.4),
    ("UBS02", "UBS Restinga", "Restinga", 1.3),
    ("UBS03", "UBS Partenon", "Partenon", 1.1),
    ("UBS04", "UBS Sarandi", "Sarandi", 1.2),
    ("UBS05", "UBS Lomba do Pinheiro", "Lomba do Pinheiro", 1.0),
    ("UBS06", "UBS Cristal", "Cristal", 0.8),
    ("UBS07", "UBS Navegantes", "Navegantes", 0.7),
    ("UBS08", "UBS Belém Novo", "Belém Novo", 0.6),
]

# Número aproximado de unidades de saúde que dividem a compra anual do município
UNIDADES_NO_MUNICIPIO = 150

# Cenários possíveis para cada par UBS x medicamento e sua probabilidade
CENARIOS = {
    "normal": 0.52,
    "escasso": 0.12,
    "falta": 0.08,
    "excesso_vencendo": 0.12,
    "com_vencido": 0.10,
    "vencendo_logo": 0.06,
}


def _lote(rng, qtd, dias_min, dias_max, hoje):
    dias = int(rng.integers(dias_min, dias_max + 1))
    return {"quantidade": max(int(qtd), 1), "data_validade": hoje + timedelta(days=dias)}


def _lotes_do_cenario(cenario, consumo, rng, hoje):
    """Cria os lotes de um par UBS x medicamento conforme o cenário sorteado."""
    c = consumo
    lotes = []

    def estoque_normal():
        total = c * rng.uniform(1.5, 3.0)
        n = int(rng.integers(1, 3))
        for parte in rng.dirichlet(np.ones(n)) * total:
            lotes.append(_lote(rng, parte, 120, 600, hoje))

    if cenario == "normal":
        estoque_normal()
    elif cenario == "escasso":
        lotes.append(_lote(rng, c * rng.uniform(0.2, 0.9), 90, 500, hoje))
    elif cenario == "falta":
        if rng.random() < 0.5:  # às vezes sobra só um lote já vencido
            lotes.append(_lote(rng, c * rng.uniform(0.1, 0.4), -60, -1, hoje))
    elif cenario == "excesso_vencendo":
        lotes.append(_lote(rng, c * rng.uniform(3.0, 5.0), 20, 75, hoje))
        lotes.append(_lote(rng, c * rng.uniform(0.5, 1.5), 200, 600, hoje))
    elif cenario == "com_vencido":
        estoque_normal()
        lotes.append(_lote(rng, c * rng.uniform(0.3, 1.0), -90, -3, hoje))
    elif cenario == "vencendo_logo":
        estoque_normal()
        lotes.append(_lote(rng, c * rng.uniform(0.8, 1.5), 3, 30, hoje))
    return lotes


def gerar_dados(medicamentos: pd.DataFrame, hoje: date | None = None, semente: int = 42) -> dict:
    """Retorna um dicionário de DataFrames: ubs, medicamento, consumo e lote."""
    hoje = hoje or date.today()
    rng = np.random.default_rng(semente)

    ubs = pd.DataFrame(UBS, columns=["id_ubs", "nome", "bairro", "porte"])

    consumo_linhas, lote_linhas = [], []
    nomes, probs = list(CENARIOS), list(CENARIOS.values())
    seq = 1
    for _, u in ubs.iterrows():
        for _, m in medicamentos.iterrows():
            base = m["qt_anual_piloto"] / 12 / UNIDADES_NO_MUNICIPIO
            consumo = round(base * u["porte"] * rng.uniform(0.7, 1.3))
            consumo_linhas.append({"id_ubs": u["id_ubs"], "co_catmat": m["co_catmat"],
                                   "consumo_medio_mensal": consumo})
            cenario = rng.choice(nomes, p=probs)
            for lote in _lotes_do_cenario(cenario, consumo, rng, hoje):
                lote_linhas.append({"id_lote": f"L{seq:05d}", "id_ubs": u["id_ubs"],
                                    "co_catmat": m["co_catmat"], **lote})
                seq += 1

    return {
        "ubs": ubs,
        "medicamento": medicamentos.copy(),
        "consumo": pd.DataFrame(consumo_linhas),
        "lote": pd.DataFrame(lote_linhas),
    }
