"""Transporte HTTP real para o BancoMcpFonte.

Lê BANCO_MCP_BASE_URL e BANCO_MCP_TOKEN do ambiente e faz GET autenticado.
CONFIRA no painel/docs do mcp.ai (plano Plus) o formato exato da autenticação
REST — se for token na URL em vez de header Bearer, ajuste `auth_no_header`.
"""
import os


def criar_transporte(base_url: str | None = None, token: str | None = None,
                     auth_no_header: bool = False):
    base = (base_url or os.environ["BANCO_MCP_BASE_URL"]).rstrip("/")
    tok = token or os.environ["BANCO_MCP_TOKEN"]

    def transporte(caminho: str, params: dict) -> dict:
        import requests
        url = f"{base}{caminho}"
        headers = {}
        p = dict(params or {})
        if auth_no_header:
            p["token"] = tok
        else:
            headers["Authorization"] = f"Bearer {tok}"
        resp = requests.get(url, params=p, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    return transporte
