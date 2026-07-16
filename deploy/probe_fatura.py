"""Probe: descobre se a API do banco devolve a FATURA com as LINHAS (line items),
pra o sistema puxar a fatura pronta (exata) em vez de reconstruir pelas transações.
Protegido pelo CRON_SECRET (header X-Probe: fatura)."""
import os

from deploy.transporte_banco_mcp import criar_transporte


def _resumir(v, prof=0):
    if isinstance(v, dict):
        return {k: _resumir(x, prof + 1) for k, x in list(v.items())[:40]}
    if isinstance(v, list):
        return {"_len": len(v), "_item0": _resumir(v[0], prof + 1) if v else None}
    if isinstance(v, str):
        return v[:80]
    return v


def probar_fatura() -> dict:
    transporte = criar_transporte()
    acc = os.environ.get("XP_ACCOUNT_ID_CARTAO")
    dia = int(os.environ.get("DIA_FECHAMENTO", "7"))
    out = {}

    # 1) lista de faturas + estrutura completa da 1ª (procura line items)
    try:
        resp = transporte("/credit-card-bills/list", {"account_id": acc, "closing_day": dia})
        result = resp.get("result") or {}
        bills = result.get("results") or []
        out["qtd_faturas"] = len(bills)
        out["chaves_da_fatura"] = sorted((bills[0] or {}).keys()) if bills else []
        out["fatura_completa_0"] = _resumir(bills[0]) if bills else None
        out["faturas_resumo"] = [{"dueDate": (b.get("dueDate") or "")[:10],
                                  "total": b.get("totalAmount"),
                                  "status": b.get("payment_status")} for b in bills[:6]]
        # se a fatura tem um id, tenta endpoint de detalhe
        bid = (bills[0] or {}).get("id") if bills else None
        if bid:
            for cam in ["/credit-card-bills/get", "/credit-card-bills/transactions",
                        "/credit-card-bill/transactions", "/credit-card-bills/detail"]:
                try:
                    r2 = transporte(cam, {"account_id": acc, "bill_id": bid, "id": bid})
                    out[f"detalhe {cam}"] = _resumir(r2)
                    break
                except Exception as e:  # noqa: BLE001
                    if "404" not in str(e) and "405" not in str(e):
                        out[f"detalhe {cam} (erro)"] = str(e)[:120]
    except Exception as e:  # noqa: BLE001
        out["erro"] = str(e)[:200]
    return out
