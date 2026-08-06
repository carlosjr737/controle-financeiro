"""Envio de mensagens no Telegram (resumo, botões, respostas de callback)."""
import os


def _tok():
    return os.environ["TELEGRAM_BOT_TOKEN"]

def _api(metodo: str, payload: dict):
    import requests
    requests.post(f"https://api.telegram.org/bot{_tok()}/{metodo}",
                  json=payload, timeout=15)

def criar_enviar(token: str | None = None, chat_id: str | None = None):
    """Envia o resumo pro dono + destinos extras (esposa/grupo) via
    TELEGRAM_CHAT_IDS_EXTRA (ids separados por vírgula)."""
    tok = token or os.environ["TELEGRAM_BOT_TOKEN"]
    principal = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    extras = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_IDS_EXTRA", "").split(",") if c.strip()]
    destinos = [principal] + [e for e in extras if e != principal]

    def enviar(texto: str) -> None:
        import requests
        for cid in destinos:
            try:
                requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                              json={"chat_id": cid, "text": texto}, timeout=15)
            except Exception:  # noqa: BLE001
                pass
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


def responder_chat(chat_id, texto: str) -> None:
    _api("sendMessage", {"chat_id": chat_id, "text": texto})


def editar_teclado(chat_id, message_id, teclado: dict) -> None:
    _api("editMessageReplyMarkup",
         {"chat_id": chat_id, "message_id": message_id, "reply_markup": teclado})


def responder_chat_botoes(chat_id, texto: str, teclado: dict) -> None:
    _api("sendMessage", {"chat_id": chat_id, "text": texto, "reply_markup": teclado})
