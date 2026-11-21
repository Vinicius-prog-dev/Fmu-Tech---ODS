"""
Persistência em SQLite (data/estoque_vital.db).

Tabelas:
    ubs          (id_ubs, nome, bairro, porte)
    medicamento  (co_catmat, medicamento, preco_unitario, ...)   <- BPS real
    consumo      (id_ubs, co_catmat, consumo_medio_mensal)       <- simulado
    lote         (id_lote, id_ubs, co_catmat, quantidade, data_validade) <- simulado
    meta         (chave, valor)  - guarda a data em que os dados foram gerados

Se o banco não existir, ou tiver sido gerado em outro dia, ele é recriado
automaticamente para que as validades continuem relativas à data de hoje.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from src.mock import gerar_dados

RAIZ = Path(__file__).resolve().parents[1]
ARQ_BANCO = RAIZ / "data" / "estoque_vital.db"
ARQ_MEDICAMENTOS = RAIZ / "data" / "medicamentos_referencia.csv"
TABELAS = ["ubs", "medicamento", "consumo", "lote"]


def _data_geracao(con: sqlite3.Connection) -> str | None:
    try:
        linha = con.execute("SELECT valor FROM meta WHERE chave = 'data_geracao'").fetchone()
        return linha[0] if linha else None
    except sqlite3.OperationalError:
        return None


def criar_banco(hoje: date) -> None:
    medicamentos = pd.read_csv(ARQ_MEDICAMENTOS)
    dados = gerar_dados(medicamentos, hoje)
    with sqlite3.connect(ARQ_BANCO) as con:
        for nome in TABELAS:
            dados[nome].to_sql(nome, con, if_exists="replace", index=False)
        pd.DataFrame([{"chave": "data_geracao", "valor": hoje.isoformat()}]).to_sql(
            "meta", con, if_exists="replace", index=False
        )


def carregar_dados(hoje: date | None = None) -> dict:
    """Garante que o banco está atualizado e devolve as tabelas como DataFrames."""
    hoje = hoje or date.today()
    precisa_criar = not ARQ_BANCO.exists()
    if not precisa_criar:
        with sqlite3.connect(ARQ_BANCO) as con:
            precisa_criar = _data_geracao(con) != hoje.isoformat()
    if precisa_criar:
        criar_banco(hoje)

    with sqlite3.connect(ARQ_BANCO) as con:
        dados = {nome: pd.read_sql(f"SELECT * FROM {nome}", con) for nome in TABELAS}
    dados["lote"]["data_validade"] = pd.to_datetime(dados["lote"]["data_validade"]).dt.date
    return dados
