"""Envio de mensagens no Telegram (resumo, botões, respostas de callback)."""
import os


def _tok():
    return os.environ["TELEGRAM_BOT_TOKEN"]


def _destinos_da_planilha():
    """Lê chat_ids extras da aba 'destinatarios' (coluna A). Vazio se falhar."""
    try:
        from deploy.sheets_adapter import _abrir_planilha
        ws = _abrir_planilha().worksheet("destinatarios")
        out = []
        for r in ws.get_all_values():
            c = (r[0].strip() if r else "")
            if c and c.lower() not in ("chat_id", "id", "destinatario"):
                out.append(c)
        return out
    except Exception:  # noqa: BLE001
        return []

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
    extras += _destinos_da_planilha()
    destinos, vistos = [], set()
    for d in [principal] + extras:
        if d and d not in vistos:
            vistos.add(d); destinos.append(d)

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
