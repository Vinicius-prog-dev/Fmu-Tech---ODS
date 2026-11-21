"""
Regras de negócio do Estoque Vital (a "inteligência" dos painéis).

Validade de cada lote
    Vencido  : já passou da data de validade
    Crítico  : vence em até 30 dias
    Atenção  : vence entre 31 e 90 dias
    OK       : vence em mais de 90 dias

Situação do estoque (por UBS x medicamento), usando só lotes dentro da validade
    cobertura = estoque válido / consumo médio mensal (em meses)
    Em falta  : estoque válido = 0
    Escasso   : cobertura < 1 mês
    Adequado  : cobertura entre 1 e 3 meses
    Excesso   : cobertura > 3 meses

Perda prevista
    Simula o consumo dos lotes na ordem "primeiro que vence, primeiro que sai"
    (FEFO) e calcula quantas unidades vão vencer antes de serem usadas.

Pedido sugerido
    Quantidade para a UBS ficar com COBERTURA_ALVO meses de estoque.

Remanejamento
    Para cada medicamento, leva unidades de UBSs com excesso (ou com lotes que vão
    vencer sem uso) para UBSs em falta ou com estoque escasso.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

DIAS_CRITICO = 30
DIAS_ATENCAO = 90
COBERTURA_ESCASSO = 1.0
COBERTURA_EXCESSO = 3.0
COBERTURA_ALVO = 2.0      # meses de estoque desejados após reposição
RESERVA_DOADORA = 1.5     # meses que a UBS doadora mantém para si
DIAS_MIN_TRANSFERENCIA = 15  # lote precisa ter pelo menos 15 dias de validade para ser enviado

ORDEM_VALIDADE = ["Vencido", "Crítico", "Atenção", "OK"]
ORDEM_ESTOQUE = ["Em falta", "Escasso", "Adequado", "Excesso"]


def status_validade(dias: int) -> str:
    if dias < 0:
        return "Vencido"
    if dias <= DIAS_CRITICO:
        return "Crítico"
    if dias <= DIAS_ATENCAO:
        return "Atenção"
    return "OK"


def status_estoque(estoque_valido: float, cobertura: float) -> str:
    if estoque_valido <= 0:
        return "Em falta"
    if cobertura < COBERTURA_ESCASSO:
        return "Escasso"
    if cobertura > COBERTURA_EXCESSO:
        return "Excesso"
    return "Adequado"


def classificar_lotes(dados: dict, hoje: date | None = None) -> pd.DataFrame:
    """Uma linha por lote, com dias para vencer, status e valor em R$."""
    hoje = hoje or date.today()
    lotes = (
        dados["lote"]
        .merge(dados["ubs"][["id_ubs", "nome"]], on="id_ubs")
        .merge(dados["medicamento"][["co_catmat", "medicamento", "preco_unitario"]], on="co_catmat")
        .rename(columns={"nome": "ubs"})
    )
    lotes["dias_para_vencer"] = [(v - hoje).days for v in lotes["data_validade"]]
    lotes["status_validade"] = lotes["dias_para_vencer"].apply(status_validade)
    lotes["valor_total"] = lotes["quantidade"] * lotes["preco_unitario"]
    return lotes.sort_values("dias_para_vencer").reset_index(drop=True)


def _perda_prevista(lotes_validos: pd.DataFrame, consumo_mensal: float) -> int:
    """Unidades que vão vencer antes de serem consumidas (consumo FEFO)."""
    consumo_dia = consumo_mensal / 30
    consumido, perda = 0.0, 0.0
    for _, lote in lotes_validos.sort_values("dias_para_vencer").iterrows():
        capacidade = max(0.0, consumo_dia * lote["dias_para_vencer"] - consumido)
        usado = min(lote["quantidade"], capacidade)
        perda += lote["quantidade"] - usado
        consumido += usado
    return int(round(perda))


def resumo_estoque(dados: dict, lotes: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por UBS x medicamento com estoque, cobertura e status."""
    base = (
        dados["consumo"]
        .merge(dados["ubs"][["id_ubs", "nome"]], on="id_ubs")
        .merge(dados["medicamento"][["co_catmat", "medicamento", "preco_unitario"]], on="co_catmat")
        .rename(columns={"nome": "ubs"})
    )

    validos = lotes[lotes["dias_para_vencer"] >= 0]
    vencidos = lotes[lotes["dias_para_vencer"] < 0]
    chave = ["id_ubs", "co_catmat"]

    est = validos.groupby(chave)["quantidade"].sum().rename("estoque_valido")
    venc = vencidos.groupby(chave)["quantidade"].sum().rename("qtd_vencida")
    prox = validos[validos["dias_para_vencer"] <= DIAS_ATENCAO].groupby(chave)["dias_para_vencer"].min()
    base = base.join(est, on=chave).join(venc, on=chave).join(prox.rename("dias_lote_mais_proximo"), on=chave)
    base[["estoque_valido", "qtd_vencida"]] = base[["estoque_valido", "qtd_vencida"]].fillna(0).astype(int)

    consumo = base["consumo_medio_mensal"].replace(0, np.nan)
    base["cobertura_meses"] = (base["estoque_valido"] / consumo).fillna(0).round(2)
    base["status_estoque"] = [status_estoque(e, c) for e, c in zip(base["estoque_valido"], base["cobertura_meses"])]

    perdas = {
        k: _perda_prevista(g, base.loc[(base["id_ubs"] == k[0]) & (base["co_catmat"] == k[1]), "consumo_medio_mensal"].iloc[0])
        for k, g in validos.groupby(chave)
    }
    base["perda_prevista"] = [perdas.get((u, c), 0) for u, c in zip(base["id_ubs"], base["co_catmat"])]

    base["valor_vencido"] = base["qtd_vencida"] * base["preco_unitario"]
    base["valor_em_risco"] = base["perda_prevista"] * base["preco_unitario"]
    base["pedido_sugerido"] = np.ceil(
        (COBERTURA_ALVO * base["consumo_medio_mensal"] - base["estoque_valido"]).clip(lower=0)
    ).astype(int)
    return base


def sugerir_remanejamentos(resumo: pd.DataFrame, lotes: pd.DataFrame) -> pd.DataFrame:
    """Casa UBSs com sobra com UBSs em falta/escassez do mesmo medicamento."""
    transferiveis = (
        lotes[lotes["dias_para_vencer"] >= DIAS_MIN_TRANSFERENCIA]
        .groupby(["id_ubs", "co_catmat"])["quantidade"].sum()
    )
    sugestoes = []
    for catmat, grupo in resumo.groupby("co_catmat"):
        receptores = grupo[grupo["status_estoque"].isin(["Em falta", "Escasso"])].copy()
        if receptores.empty:
            continue
        receptores["necessidade"] = (
            COBERTURA_ALVO * receptores["consumo_medio_mensal"] - receptores["estoque_valido"]
        ).clip(lower=0)

        doadores = grupo[(grupo["status_estoque"] == "Excesso") | (grupo["perda_prevista"] > 0)].copy()
        if doadores.empty:
            continue
        doadores["disponivel"] = [
            max(0.0, transferiveis.get((u, catmat), 0) - RESERVA_DOADORA * c)
            for u, c in zip(doadores["id_ubs"], doadores["consumo_medio_mensal"])
        ]
        doadores["perda_restante"] = doadores["perda_prevista"].astype(float)
        doadores = doadores.sort_values(["perda_prevista", "disponivel"], ascending=False)

        for _, rec in receptores.sort_values("cobertura_meses").iterrows():
            falta = rec["necessidade"]
            for idx, doa in doadores.iterrows():
                if falta <= 0:
                    break
                qtd = int(min(falta, doadores.at[idx, "disponivel"]))
                if qtd <= 0:
                    continue
                evitada = min(qtd, doadores.at[idx, "perda_restante"])
                sugestoes.append({
                    "medicamento": rec["medicamento"],
                    "co_catmat": catmat,
                    "origem": doa["ubs"],
                    "destino": rec["ubs"],
                    "situacao_destino": rec["status_estoque"],
                    "quantidade": qtd,
                    "valor_transferido": qtd * rec["preco_unitario"],
                    "perda_evitada": evitada * rec["preco_unitario"],
                    "motivo": "Lote da origem venceria sem uso" if evitada > 0 else "Origem com estoque em excesso",
                })
                doadores.at[idx, "disponivel"] -= qtd
                doadores.at[idx, "perda_restante"] -= evitada
                falta -= qtd

    colunas = ["medicamento", "co_catmat", "origem", "destino", "situacao_destino",
               "quantidade", "valor_transferido", "perda_evitada", "motivo"]
    return pd.DataFrame(sugestoes, columns=colunas)


def pedido_pos_remanejamento(resumo: pd.DataFrame, remanejamentos: pd.DataFrame) -> pd.DataFrame:
    """Quanto a CAF ainda precisa enviar de cada medicamento depois dos remanejamentos."""
    recebido = remanejamentos.groupby(["destino", "co_catmat"])["quantidade"].sum()
    r = resumo.copy()
    r["recebido_remanejamento"] = [recebido.get((u, c), 0) for u, c in zip(r["ubs"], r["co_catmat"])]
    r["pedido_final"] = (r["pedido_sugerido"] - r["recebido_remanejamento"]).clip(lower=0)
    pedido = (
        r.groupby(["co_catmat", "medicamento", "preco_unitario"])
        .agg(ubs_atendidas=("pedido_final", lambda s: int((s > 0).sum())),
             quantidade=("pedido_final", "sum"))
        .reset_index()
    )
    pedido["custo_estimado"] = pedido["quantidade"] * pedido["preco_unitario"]
    return pedido[pedido["quantidade"] > 0].sort_values("custo_estimado", ascending=False)


def calcular_tudo(dados: dict, hoje: date | None = None) -> dict:
    """Atalho usado pelas telas: roda todas as regras de uma vez."""
    lotes = classificar_lotes(dados, hoje)
    resumo = resumo_estoque(dados, lotes)
    remanejamentos = sugerir_remanejamentos(resumo, lotes)
    pedido = pedido_pos_remanejamento(resumo, remanejamentos)
    return {"lotes": lotes, "resumo": resumo, "remanejamentos": remanejamentos, "pedido": pedido}
