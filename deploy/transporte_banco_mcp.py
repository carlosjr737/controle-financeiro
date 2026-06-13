"""Transporte HTTP real para o BancoMcpFonte (API REST do mcp.ai).

Faz POST com corpo JSON e auth Bearer usando a workspace API key (sk_live_...).
Base: https://api.mcp.ai/api/openfinance
"""
import os


def criar_transporte(base_url: str | None = None, token: str | None = None):
    base = (base_url or os.environ["BANCO_MCP_BASE_URL"]).rstrip("/")
    tok = token or os.environ["BANCO_MCP_TOKEN"]

    def transporte(caminho: str, body: dict) -> dict:
        import requests
        url = f"{base}{caminho}"
        headers = {"Authorization": f"Bearer {tok}",
                   "Content-Type": "application/json"}
        resp = requests.post(url, json=body or {}, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    return transporte
