"""Envio de mensagens no Telegram (resumo, botões, respostas de callback)."""
import os


def _tok():
    return os.environ["TELEGRAM_BOT_TOKEN"]

def _api(metodo: str, payload: dict):
    import requests
    requests.post(f"https://api.telegram.org/bot{_tok()}/{metodo}",
                  json=payload, timeout=15)

def criar_enviar(token: str | None = None, chat_id: str | None = None):
    tok = token or os.environ["TELEGRAM_BOT_TOKEN"]
    cid = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    def enviar(texto: str) -> None:
        import requests
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": cid, "text": texto}, timeout=15).raise_for_status()
    return enviar

def criar_enviar_botoes(token: str | None = None, chat_id: str | None = None):
    tok = token or os.environ["TELEGRAM_BOT_TOKEN"]
    cid = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    def enviar_botoes(texto: str, teclado: dict) -> None:
        import requests
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": cid, "text": texto, "reply_markup": teclado},
                      timeout=15)
    return enviar_botoes

def responder_callback(callback_id: str, texto: str = "") -> None:
    _api("answerCallbackQuery", {"callback_query_id": callback_id, "text": texto})

def editar_mensagem(chat_id, message_id, texto: str) -> None:
    _api("editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": texto})
