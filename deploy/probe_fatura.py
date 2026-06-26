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

# caminhos prováveis pra FATURA ATUAL (aberta, ainda não fechada)
CAMINHOS_ABERTA = [
    "/credit-card-bills/current", "/credit-card-bill/current",
    "/credit-card-bills/open", "/credit-card-bill/summary",
    "/credit-card-bills/summary", "/credit-card-bill/get",
    "/current-credit-card-bill/get", "/credit-card-bills/get",
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


def _faturas_de(resp):
    """Extrai [{dueDate,totalAmount,payment_status}] de uma resposta de faturas."""
    result = resp.get("result") or {}
    bruto = result.get("results")
    if isinstance(bruto, dict):              # caso seja 1 fatura só (objeto)
        bruto = [bruto]
    if not isinstance(bruto, list):
        return _resumir(resp)
    return [{"dueDate": (b.get("dueDate") or "")[:10],
             "totalAmount": b.get("totalAmount"),
             "payment_status": b.get("payment_status")} for b in bruto]


def probar_fatura() -> dict:
    transporte = criar_transporte()
    acc = os.environ.get("XP_ACCOUNT_ID_CARTAO")
    dia = int(os.environ.get("DIA_FECHAMENTO", "6"))
    base = {"account_id": acc, "closing_day": dia}

    # 1) endpoint que funciona, com variações de parâmetro p/ tentar trazer a aberta
    variacoes = [
        base,
        {**base, "status": "OPEN"},
        {**base, "include_open": True},
        {**base, "open": True},
        {**base, "current": True},
        {**base, "include_current": True},
        {**base, "include_open_bill": True},
    ]
    lista = []
    for corpo in variacoes:
        try:
            resp = transporte("/credit-card-bills/list", corpo)
            lista.append({"corpo": list(corpo.keys()), "faturas": _faturas_de(resp)})
        except Exception as e:  # noqa: BLE001
            lista.append({"corpo": list(corpo.keys()), "erro": str(e)[:120]})

    # 2) caminhos candidatos pra fatura ATUAL (aberta)
    abertos = []
    for caminho in CAMINHOS_ABERTA:
        try:
            resp = transporte(caminho, base)
            abertos.append({"endpoint": caminho, "resposta": _resumir(resp)})
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "404" not in msg and "405" not in msg:   # só registra caminhos que existem
                abertos.append({"endpoint": caminho, "erro": msg[:120]})

    return {"ok": True, "lista_variacoes": lista, "caminhos_aberta": abertos or "todos 404"}
