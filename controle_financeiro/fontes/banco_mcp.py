from typing import Callable

class BancoMcpFonte:
    """Lê transações do Banco MCP via API REST (POST /transactions/list).
    `transporte(caminho, body) -> dict` é injetado."""
    def __init__(self, transporte: Callable[[str, dict], dict], account_id: str,
                 page_size: int = 200):
        self.transporte = transporte
        self.account_id = account_id
        self.page_size = page_size

    def buscar_transacoes(self, desde: str, ate: str) -> list[dict]:
        body = {"account_id": self.account_id, "from": desde, "to": ate,
                "page_size": self.page_size}
        resp = self.transporte("/transactions/list", body)
        result = resp.get("result") or {}
        return list(result.get("results", []))
