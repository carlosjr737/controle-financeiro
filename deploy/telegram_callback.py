"""Processa updates do Telegram: cliques de botão e mensagens de texto."""
import os
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.competencia import competencia_fatura
from controle_financeiro.telegram.botoes import parse_callback
from controle_financeiro.aprendizado import confirmar_sugestao, corrigir_por_categoria_id
from controle_financeiro.consultas import responder_comando, contexto_para_ia
from deploy.telegram_envio import responder_callback, editar_mensagem, responder_chat


def _sessao():
    engine = engine_from_env(); Base.metadata.create_all(engine)
    return criar_sessao(engine)

def _mes_hoje():
    hoje = datetime.date.today()
    dia = int(os.environ.get("DIA_FECHAMENTO", "6"))
    return competencia_fatura(hoje.isoformat(), dia), hoje.isoformat()


def _eh_dono(chat_id) -> bool:
    dono = os.environ.get("TELEGRAM_CHAT_ID")
    return dono is None or str(chat_id) == str(dono)


def tratar_update(update: dict) -> None:
    cq = update.get("callback_query")
    if cq:
        return _tratar_callback(cq)
    msg = update.get("message")
    if msg and isinstance(msg.get("text"), str):
        return _tratar_mensagem(msg)


def _tratar_callback(cq):
    m0 = cq.get("message") or {}
    if not _eh_dono((m0.get("chat") or {}).get("id")):
        return
    parsed = parse_callback(cq.get("data", ""))
    s = _sessao()
    if parsed[0] == "ok":
        feedback = "✅ " + confirmar_sugestao(s, parsed[1])
    elif parsed[0] == "set":
        feedback = "✅ " + corrigir_por_categoria_id(s, parsed[1], parsed[2])
    else:
        feedback = "ignorado"
    responder_callback(cq["id"], feedback)
    m = cq.get("message") or {}
    if m.get("chat") and m.get("message_id"):
        editar_mensagem(m["chat"]["id"], m["message_id"], f"{m.get('text','')}\n{feedback}")


def _tratar_mensagem(msg):
    texto = msg["text"].strip()
    chat_id = msg["chat"]["id"]
    if not _eh_dono(chat_id):
        return
    s = _sessao()
    mes, hoje = _mes_hoje()
    teto = float(os.environ.get("TETO_MENSAL", "27060"))

    if texto.startswith("/"):
        resp = responder_comando(s, texto, mes, teto, hoje)
    elif os.environ.get("LLM_API_KEY"):
        from deploy.cliente_ia import criar_assistente
        resp = criar_assistente()(texto, contexto_para_ia(s, mes))
    else:
        resp = ("Pra perguntas livres preciso da IA (LLM_API_KEY). Por ora use: "
                "/resumo, /linha <categoria>, /pendentes, /ajuda.")
    responder_chat(chat_id, resp)
