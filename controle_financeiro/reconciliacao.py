"""Reconcilia o total do CARTÃO com a fatura oficial do banco.

- Mês FECHADO: usa o total oficial exato da fatura do banco.
- Mês ABERTO: compras capturadas + estimativa de encargos/parcelas/IOF
  (= diferença entre a última fatura fechada e as compras daquele mês).
"""


def reconciliar_cartao(mes: str, capturado_por_mes: dict, faturas: list) -> dict:
    """mes: competência aberta (ex.: '2026-07').
    capturado_por_mes: {competência: soma das compras capturadas do cartão}.
    faturas: [{competencia, total}] das faturas FECHADAS (valor oficial).
    Retorna {total, compras, encargos, oficial, comp_ref}."""
    oficiais = {f["competencia"]: f["total"] for f in faturas
                if f.get("competencia") and f.get("total") is not None}
    compras = round(capturado_por_mes.get(mes, 0.0), 2)

    if mes in oficiais:                       # fatura já fechou -> valor exato
        total = oficiais[mes]
        return {"total": round(total, 2), "compras": compras,
                "encargos": round(total - compras, 2), "oficial": True, "comp_ref": mes}

    # fatura aberta -> estima encargos pela última fatura fechada anterior
    anteriores = sorted([c for c in oficiais if c < mes], reverse=True)
    if not anteriores:
        return {"total": compras, "compras": compras,
                "encargos": 0.0, "oficial": False, "comp_ref": None}
    ref = anteriores[0]
    encargos = max(oficiais[ref] - capturado_por_mes.get(ref, 0.0), 0.0)
    return {"total": round(compras + encargos, 2), "compras": compras,
            "encargos": round(encargos, 2), "oficial": False, "comp_ref": ref}
