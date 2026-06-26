"""Probe temporário: descobre o endpoint REST de FATURA do Banco MCP e a forma
da resposta. Protegido pelo CRON_SECRET (chamado só via GET ?probe=fatura).
Remover depois que a integração da fatura estiver pronta."""
import os

from deploy.transporte_banco_mcp import criar_transporte

CAMINHOS = [
    "/credit_card_bills/list", "/credit-card-bills/list", "/creditCardBills/list",
    "/credit_card/bills/list", "/bills/list", "/faturas/list",
    "/credit_card_bills", "/bills",
]


def _resumir(resp):
    """Estrutura da resposta (sem despejar tudo): chaves + 1º item de cada lista."""
    def amostra(v, prof=0):
        if isinstance(v, dict):
            return {k: amostra(x, prof + 1) for k, x in list(v.items())[:25]}
        if isinstance(v, list):
            return {"_lista_len": len(v), "_item0": amostra(v[0], prof + 1) if v else None}
        if isinstance(v, str):
            return v[:60]
        return v
    return amostra(resp)


def probar_fatura() -> dict:
    transporte = criar_transporte()
    acc = os.environ.get("XP_ACCOUNT_ID_CARTAO")
    dia = int(os.environ.get("DIA_FECHAMENTO", "6"))
    corpos = [
        {"account_id": acc, "closing_day": dia},
        {"account_id": acc, "closingDay": dia},
        {"account_id": acc},
        {"accountId": acc, "closingDay": dia},
        {},
    ]
    tentativas = []
    for caminho in CAMINHOS:
        for corpo in corpos:
            try:
                resp = transporte(caminho, corpo)
                return {"ok": True, "endpoint": caminho,
                        "corpo": list(corpo.keys()), "resposta": _resumir(resp)}
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                tentativas.append({"endpoint": caminho,
                                   "corpo": list(corpo.keys()), "erro": msg[:140]})
                if "404" in msg or "405" in msg:
                    break   # caminho não existe -> próximo caminho
    return {"ok": False, "tentativas": tentativas[-24:]}
