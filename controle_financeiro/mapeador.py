def mapear_transacao(raw: dict, portador: str | None = None,
                     tipo: str | None = None, dia_fechamento: int | None = None) -> dict:
    data = str(raw.get("date", ""))[:10]
    ccm = raw.get("creditCardMetadata") or {}
    parcela = None
    if ccm.get("totalInstallments") and ccm.get("installmentNumber") is not None:
        parcela = f"{ccm.get('installmentNumber')} de {ccm.get('totalInstallments')}"
    tipo_final = tipo or ("cartao" if ccm else "conta")

    # Competência = ciclo da fatura, rotulado pelo mês que cobre (fecha dia X).
    mes_comp = data[:7] if len(data) >= 7 else None
    if dia_fechamento and len(data) >= 10:
        from controle_financeiro.competencia import competencia_ciclo
        mes_comp = competencia_ciclo(data, dia_fechamento)

    return {
        "id_externo": raw.get("id"),
        "estabelecimento": raw.get("description") or (raw.get("merchant") or {}).get("name") or "",
        "valor": float(raw.get("amount")) if raw.get("amount") is not None else 0.0,
        "data": data,
        "parcela": parcela,
        "tipo": tipo_final,
        "portador": portador,
        "mes_competencia": mes_comp,
    }
