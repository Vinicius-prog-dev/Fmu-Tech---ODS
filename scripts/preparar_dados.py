"""
Prepara a base real do Banco de Preços em Saúde (BPS) para o Estoque Vital.

Entrada : data/2026_csv.zip  (BPS 2026 - Ministério da Saúde, ~15 mil registros)
Saída   : data/medicamentos_referencia.csv  (lista enxuta usada pelo app)

O que o script faz:
1. Lê o BPS e mantém apenas a classe "DROGAS E MEDICAMENTOS".
2. Limpa preços: para cada medicamento (co_catmat + unidade de fornecimento),
   descarta registros com preço acima de 10x ou abaixo de 1/10 da mediana
   (normalmente são compras registradas por caixa em vez de por unidade).
3. Calcula o preço unitário de referência (mediana nacional já limpa).
4. Seleciona os medicamentos orais mais comprados em Porto Alegre (cidade piloto)
   e guarda a quantidade anual comprada, usada para estimar o consumo das UBSs.

Como rodar (a partir da raiz do repositório):
    python scripts/preparar_dados.py
"""
from pathlib import Path
import re

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARQ_BPS = RAIZ / "data" / "2026_csv.zip"
ARQ_SAIDA = RAIZ / "data" / "medicamentos_referencia.csv"

MUNICIPIO_PILOTO = "PORTO ALEGRE"
FORMAS_ORAIS = ["COMPRIMIDO", "CÁPSULA", "DRÁGEA"]
QTD_MEDICAMENTOS = 30

PADRAO_DOSE = re.compile(
    r"\d+(?:,\d+)?\s*(?:MG|MCG|UI|G)\b(?:\s*\+\s*\d+(?:,\d+)?\s*(?:MG|MCG|UI))?"
)


def nome_curto(no_pdm: str, ds_item: str) -> str:
    """'ENALAPRIL MALEATO' + 'DOSAGEM: 10 MG' -> 'Enalapril Maleato 10 mg'."""
    dose = PADRAO_DOSE.search(ds_item)
    nome = no_pdm.strip().title().replace(" De ", " de ")
    if dose:
        texto = re.sub(r"(\d)(MG|MCG|UI|G)\b", r"\1 \2", dose.group(0))
        nome += " " + texto.lower().replace("ui", "UI")
    return nome


def carregar_bps() -> pd.DataFrame:
    df = pd.read_csv(ARQ_BPS, sep=";", encoding="utf-8")
    df = df[df["no_classe"] == "DROGAS E MEDICAMENTOS"].copy()
    df["dt_compra"] = pd.to_datetime(df["dt_compra"], format="%d/%m/%Y")
    return df


def limpar_precos(df: pd.DataFrame) -> pd.DataFrame:
    chave = ["co_catmat", "un_fornecimento"]
    mediana = df.groupby(chave)["vl_preco_unitario"].transform("median")
    razao = df["vl_preco_unitario"] / mediana
    limpo = df[(razao <= 10) & (razao >= 0.1)].copy()
    removidos = len(df) - len(limpo)
    print(f"Registros de medicamentos: {len(df):,} | outliers de preço removidos: {removidos:,}")
    return limpo


def montar_referencia(df: pd.DataFrame) -> pd.DataFrame:
    precos = (
        df.groupby("co_catmat")
        .agg(
            preco_unitario=("vl_preco_unitario", "median"),
            preco_minimo=("vl_preco_unitario", "min"),
            preco_maximo=("vl_preco_unitario", "max"),
            compras_brasil=("vl_preco_unitario", "size"),
        )
        .reset_index()
    )

    piloto = df[(df["no_municipio"] == MUNICIPIO_PILOTO) & (df["un_fornecimento"].isin(FORMAS_ORAIS))]
    qtd = (
        piloto.groupby(["co_catmat", "no_pdm", "ds_item", "un_fornecimento"])
        .agg(qt_anual_piloto=("qt_medicamento", "sum"))
        .reset_index()
        .sort_values("qt_anual_piloto", ascending=False)
    )

    ref = qtd.merge(precos, on="co_catmat", how="left")
    ref["medicamento"] = [nome_curto(p, d) for p, d in zip(ref["no_pdm"], ref["ds_item"])]
    ref = ref.drop_duplicates("medicamento").head(QTD_MEDICAMENTOS)

    colunas = [
        "co_catmat", "medicamento", "ds_item", "un_fornecimento",
        "preco_unitario", "preco_minimo", "preco_maximo",
        "compras_brasil", "qt_anual_piloto",
    ]
    return ref[colunas].reset_index(drop=True)


def main() -> None:
    bps = limpar_precos(carregar_bps())
    ref = montar_referencia(bps)
    ref.to_csv(ARQ_SAIDA, index=False, encoding="utf-8")
    print(f"{len(ref)} medicamentos salvos em {ARQ_SAIDA.relative_to(RAIZ)}")
    print(ref[["medicamento", "preco_unitario", "qt_anual_piloto"]].to_string(index=False))


if __name__ == "__main__":
    main()
