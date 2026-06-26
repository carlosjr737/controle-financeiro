"""Reconcilia o total do CARTÃO com a fatura do banco.

- Mês FECHADO: usa o total OFICIAL exato da fatura do banco.
- Mês ABERTO: compras lançadas + PROJEÇÃO determinística das parcelas já
  contratadas que ainda vão cair nesta fatura (postam ~no dia do fechamento).
"""


def reconciliar_cartao(mes: str, capturado_por_mes: dict, faturas: list,
                       projecao_parcelas: float = 0.0) -> dict:
    """mes: competência aberta (ex.: '2026-07').
    capturado_por_mes: {competência: soma das compras lançadas do cartão}.
    faturas: [{competencia, total}] das faturas FECHADAS (valor oficial).
    projecao_parcelas: parcelas contratadas que ainda vão cair na fatura aberta.
    Retorna {total, compras, parcelas, oficial, comp_ref}."""
    oficiais = {f["competencia"]: f["total"] for f in faturas
                if f.get("competencia") and f.get("total") is not None}
    compras = round(capturado_por_mes.get(mes, 0.0), 2)

    if mes in oficiais:                       # fatura já fechou -> valor exato
        total = oficiais[mes]
        return {"total": round(total, 2), "compras": compras,
                "parcelas": round(total - compras, 2), "oficial": True, "comp_ref": mes}

    # fatura aberta -> compras + parcelas projetadas (determinístico)
    parcelas = round(max(projecao_parcelas, 0.0), 2)
    return {"total": round(compras + parcelas, 2), "compras": compras,
            "parcelas": parcelas, "oficial": False, "comp_ref": None}
