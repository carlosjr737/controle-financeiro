"""Envio de mensagens no Telegram (resumo diário)."""
import os


def criar_enviar(token: str | None = None, chat_id: str | None = None):
    tok = token or os.environ["TELEGRAM_BOT_TOKEN"]
    cid = chat_id or os.environ["TELEGRAM_CHAT_ID"]

    def enviar(texto: str) -> None:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            json={"chat_id": cid, "text": texto}, timeout=15,
        ).raise_for_status()

    return enviar
