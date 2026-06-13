import requests
from deploy.telegram_envio import criar_enviar

class _Resp:
    def raise_for_status(self): pass

def test_enviar_posta_no_endpoint_certo(monkeypatch):
    capturado = {}
    def fake_post(url, json=None, timeout=None):
        capturado["url"] = url; capturado["json"] = json
        return _Resp()
    monkeypatch.setattr(requests, "post", fake_post)

    enviar = criar_enviar(token="123:ABC", chat_id="999")
    enviar("Resumo de hoje")

    assert capturado["url"] == "https://api.telegram.org/bot123:ABC/sendMessage"
    assert capturado["json"] == {"chat_id": "999", "text": "Resumo de hoje"}
