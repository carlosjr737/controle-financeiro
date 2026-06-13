"""Processa um update do Telegram (clique de botão) vindo pelo webhook."""
from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.telegram.botoes import parse_callback
from controle_financeiro.aprendizado import confirmar_sugestao, corrigir_por_categoria_id
from deploy.telegram_envio import responder_callback, editar_mensagem


def tratar_update(update: dict) -> None:
    cq = update.get("callback_query")
    if not cq:
        return
    parsed = parse_callback(cq.get("data", ""))
    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)

    if parsed[0] == "ok":
        feedback = "✅ " + confirmar_sugestao(s, parsed[1])
    elif parsed[0] == "set":
        feedback = "✅ " + corrigir_por_categoria_id(s, parsed[1], parsed[2])
    else:
        feedback = "ignorado"

    responder_callback(cq["id"], feedback)
    msg = cq.get("message") or {}
    if msg.get("chat") and msg.get("message_id"):
        original = msg.get("text", "")
        editar_mensagem(msg["chat"]["id"], msg["message_id"], f"{original}\n{feedback}")
