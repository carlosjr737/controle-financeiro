import requests
from deploy.transporte_banco_mcp import criar_transporte

class _Resp:
    def __init__(self, payload): self._p = payload
    def raise_for_status(self): pass
    def json(self): return self._p

def test_transporte_usa_bearer_e_retorna_json(monkeypatch):
    capturado = {}
    def fake_get(url, params=None, headers=None, timeout=None):
        capturado["url"] = url; capturado["params"] = params; capturado["headers"] = headers
        return _Resp({"results": [{"id": "t1"}]})
    monkeypatch.setattr(requests, "get", fake_get)

    transporte = criar_transporte(base_url="https://api.mcp.ai", token="tk_abc")
    out = transporte("/v1/openfinance/transactions", {"account_id": "acc1"})

    assert out == {"results": [{"id": "t1"}]}
    assert capturado["url"] == "https://api.mcp.ai/v1/openfinance/transactions"
    assert capturado["headers"]["Authorization"] == "Bearer tk_abc"
    assert capturado["params"]["account_id"] == "acc1"

def test_transporte_token_na_url(monkeypatch):
    capturado = {}
    def fake_get(url, params=None, headers=None, timeout=None):
        capturado["params"] = params; capturado["headers"] = headers
        return _Resp({"ok": True})
    monkeypatch.setattr(requests, "get", fake_get)
    transporte = criar_transporte(base_url="https://api.mcp.ai", token="tk_x",
                                  auth_no_header=True)
    transporte("/v1/x", {})
    assert capturado["params"]["token"] == "tk_x"
    assert "Authorization" not in capturado["headers"]
