from typing import Callable

class BancoMcpFonte:
    """Lê transações do Banco MCP via API REST (POST /transactions/list).
    `transporte(caminho, body) -> dict` é injetado."""
    def __init__(self, transporte: Callable[[str, dict], dict], account_id: str,
                 page_size: int = 500, max_paginas: int = 20):
        self.transporte = transporte
        self.account_id = account_id
        self.page_size = page_size
        self.max_paginas = max_paginas

    def buscar_transacoes(self, desde: str, ate: str) -> list[dict]:
        """Busca todas as transações da janela, paginando quando o banco devolve
        um cursor/next (cobre faturas com muitas compras sem truncar)."""
        todas, cursor, vistos = [], None, set()
        for _ in range(self.max_paginas):
            body = {"account_id": self.account_id, "from": desde, "to": ate,
                    "page_size": self.page_size}
            if cursor:
                body["cursor"] = cursor
                body["page_token"] = cursor
            resp = self.transporte("/transactions/list", body)
            result = resp.get("result") or {}
            pagina = list(result.get("results", []))
            if not pagina:
                break
            todas.extend(pagina)
            cursor = (result.get("next_cursor") or result.get("cursor")
                      or result.get("next") or result.get("page_token"))
            # para se não há cursor, ou se o cursor repete, ou se a página veio incompleta
            if not cursor or cursor in vistos or len(pagina) < self.page_size:
                break
            vistos.add(cursor)
        return todas

    def buscar_faturas(self, closing_day=None) -> list[dict]:
        """Faturas FECHADAS do cartão (valor oficial exato do banco).
        Devolve [{competencia 'AAAA-MM', due, total, status}]. A competência é o
        mês do vencimento (fatura que vence 15/06 = competência 2026-06)."""
        body = {"account_id": self.account_id}
        if closing_day is not None:
            body["closing_day"] = closing_day
        resp = self.transporte("/credit-card-bills/list", body)
        result = resp.get("result") or {}
        out = []
        for b in (result.get("results") or []):
            due = (b.get("dueDate") or "")[:10]
            try:
                total = float(b.get("totalAmount"))
            except (TypeError, ValueError):
                continue
            if len(due) >= 7:
                out.append({"competencia": due[:7], "due": due,
                            "total": total, "status": b.get("payment_status")})
        return out
