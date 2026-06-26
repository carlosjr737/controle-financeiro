def mapear_transacao(raw: dict, portador: str | None = None,
                     tipo: str | None = None, dia_fechamento: int | None = None) -> dict:
    data = str(raw.get("date", ""))[:10]
    ccm = raw.get("creditCardMetadata") or {}
    parcela = None
    if ccm.get("totalInstallments") and ccm.get("installmentNumber") is not None:
        parcela = f"{ccm.get('installmentNumber')} de {ccm.get('totalInstallments')}"
    tipo_final = tipo or ("cartao" if ccm else "conta")

    # DRE = Regime de Competência: o custo entra no MÊS DO FATO GERADOR (a compra),
    # independente da data de pagamento. -> mês calendário da data da transação.
    mes_comp = data[:7] if len(data) >= 7 else None

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
