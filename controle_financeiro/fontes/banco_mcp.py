from typing import Callable

class BancoMcpFonte:
    """Fonte que lê transações do Banco MCP via API REST.
    `transporte(caminho, params) -> dict` é injetado: em produção faz o GET HTTP
    autenticado; nos testes é um fake."""
    def __init__(self, transporte: Callable[[str, dict], dict], account_id: str,
                 page_size: int = 200):
        self.transporte = transporte
        self.account_id = account_id
        self.page_size = page_size

    def buscar_transacoes(self, desde: str, ate: str) -> list[dict]:
        params = {"account_id": self.account_id, "from": desde, "to": ate,
                  "page_size": self.page_size}
        resp = self.transporte("/v1/openfinance/transactions", params)
        return list(resp.get("results", []))
