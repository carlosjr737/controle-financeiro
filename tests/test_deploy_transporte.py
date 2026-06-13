import requests
from deploy.transporte_banco_mcp import criar_transporte

class _Resp:
    def __init__(self, payload): self._p = payload
    def raise_for_status(self): pass
    def json(self): return self._p

def test_transporte_post_bearer_json(monkeypatch):
    cap = {}
    def fake_post(url, json=None, headers=None, timeout=None):
        cap["url"] = url; cap["json"] = json; cap["headers"] = headers
        return _Resp({"ok": True, "result": {"results": []}})
    monkeypatch.setattr(requests, "post", fake_post)

    transporte = criar_transporte(base_url="https://api.mcp.ai/api/openfinance",
                                  token="sk_live_x")
    out = transporte("/transactions/list", {"account_id": "a"})

    assert out["ok"] is True
    assert cap["url"] == "https://api.mcp.ai/api/openfinance/transactions/list"
    assert cap["headers"]["Authorization"] == "Bearer sk_live_x"
    assert cap["headers"]["Content-Type"] == "application/json"
    assert cap["json"] == {"account_id": "a"}
