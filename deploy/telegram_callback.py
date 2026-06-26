"""Processa updates do Telegram: cliques de botão (confirmar/corrigir/abrir lista)
e mensagens de texto (comandos + perguntas via IA). Só responde ao dono."""
import os
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.models import Categoria
from controle_financeiro.competencia import competencia_fatura
from controle_financeiro.telegram.botoes import parse_callback, montar_pagina_categorias
from controle_financeiro.aprendizado import confirmar_sugestao, corrigir_por_categoria_id
from controle_financeiro.consultas import responder_comando, contexto_para_ia
from deploy.telegram_envio import (responder_callback, editar_mensagem,
                                   editar_teclado, responder_chat, responder_chat_botoes)


def _sessao():
    engine = engine_from_env(); Base.metadata.create_all(engine)
    return engine, criar_sessao(engine)

def _mes_hoje():
    hoje = datetime.date.today()
    dia = int(os.environ.get("DIA_FECHAMENTO", "7"))
    return competencia_fatura(hoje.isoformat(), dia), hoje.isoformat()

def _eh_dono(chat_id) -> bool:
    dono = os.environ.get("TELEGRAM_CHAT_ID")
    return dono is None or str(chat_id) == str(dono)


def _totais_fatura(s, mes):
    """Sincroniza as metas da planilha e devolve os totais da aba Fatura
    (cartão + Pix por categoria) — a fonte única de verdade. None se falhar."""
    try:
        from deploy.sheets_adapter import criar_leitor_fatura_totais, criar_leitor_orcamento
        from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento
        sincronizar_orcamento(s, mes, criar_leitor_orcamento())
        return criar_leitor_fatura_totais()(mes)
    except Exception:  # noqa: BLE001
        return None


def _fatura_cartao(s, mes):
    """Reconcilia o cartão com a fatura oficial do banco (híbrido). None se falhar."""
    try:
        from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
        from controle_financeiro.dre_fatura import linhas_para_fatura
        from controle_financeiro.reconciliacao import reconciliar_cartao
        from controle_financeiro.parcelas import projecao_parcelas
        from deploy.transporte_banco_mcp import criar_transporte
        dia = int(os.environ.get("DIA_FECHAMENTO", "7"))
        fonte = BancoMcpFonte(transporte=criar_transporte(),
                              account_id=os.environ["XP_ACCOUNT_ID_CARTAO"])
        faturas = fonte.buscar_faturas(dia)
        ano, m = int(mes[:4]), int(mes[5:7]) - 1
        if m == 0:
            ano, m = ano - 1, 12
        prev = f"{ano:04d}-{m:02d}"
        compras = {x: sum(l["valor"] for l in linhas_para_fatura(s, x) if l["valor"] > 0)
                   for x in (mes, prev)}
        proj = projecao_parcelas(s, mes, prev)
        return reconciliar_cartao(mes, compras, faturas, projecao_parcelas=proj)
    except Exception:  # noqa: BLE001
        return None


def tratar_update(update: dict) -> None:
    cq = update.get("callback_query")
    if cq:
        return _tratar_callback(cq)
    msg = update.get("message")
    if msg and isinstance(msg.get("text"), str):
        return _tratar_mensagem(msg)


def _tratar_callback(cq):
    m = cq.get("message") or {}
    chat = (m.get("chat") or {})
    if not _eh_dono(chat.get("id")):
        return
    parsed = parse_callback(cq.get("data", ""))
    engine, s = _sessao()
    try:
        # abrir lista paginada de categorias (edita só o teclado)
        if parsed[0] == "cat":
            txid, page = parsed[1], parsed[2]
            cats = [(c.id, c.nome) for c in s.query(Categoria).order_by(Categoria.nome).all()]
            if chat.get("id") and m.get("message_id"):
                editar_teclado(chat["id"], m["message_id"],
                               montar_pagina_categorias(txid, cats, page))
            responder_callback(cq["id"], "")
            return

        if parsed[0] == "ok":
            feedback = "✅ " + confirmar_sugestao(s, parsed[1])
            _atualizar_fatura(s, parsed[1])
        elif parsed[0] == "set":
            feedback = "✅ " + corrigir_por_categoria_id(s, parsed[1], parsed[2])
            _atualizar_fatura(s, parsed[1])
        else:
            feedback = "ignorado"
        responder_callback(cq["id"], feedback)
        if chat.get("id") and m.get("message_id"):
            editar_mensagem(chat["id"], m["message_id"], f"{m.get('text','')}\n{feedback}")
    finally:
        s.close(); engine.dispose()


def _tratar_mensagem(msg):
    texto = msg["text"].strip()
    chat_id = msg["chat"]["id"]
    if not _eh_dono(chat_id):
        return
    engine, s = _sessao()
    try:
        mes, hoje = _mes_hoje()
        teto = float(os.environ.get("TETO_MENSAL", "27060"))
        if texto.lower().strip() == "/revisar":
            _enviar_revisao(s, chat_id, mes)
            return
        if texto.lower().startswith("/corrigir"):
            partes = texto.split(maxsplit=1)
            termo = partes[1] if len(partes) > 1 else None
            _enviar_correcao(s, chat_id, mes, termo)
            return
        # FONTE ÚNICA: lê os totais da aba Fatura (cartão + Pix) e sincroniza as
        # metas da planilha — vale para comandos E perguntas livres (IA).
        realizado_externo = _totais_fatura(s, mes)
        fatura_cartao = _fatura_cartao(s, mes)

        if texto.startswith("/"):
            resp = responder_comando(s, texto, mes, teto, hoje,
                                     realizado_externo=realizado_externo,
                                     fatura_cartao=fatura_cartao)
        elif os.environ.get("LLM_API_KEY"):
            from deploy.cliente_ia import criar_assistente
            resp = criar_assistente()(texto, contexto_para_ia(
                s, mes, realizado_externo=realizado_externo, fatura_cartao=fatura_cartao))
        else:
            resp = ("Pra perguntas livres preciso da IA (LLM_API_KEY). Por ora use: "
                    "/resumo, /linha <categoria>, /pendentes, /ajuda.")
        responder_chat(chat_id, resp)
    finally:
        s.close(); engine.dispose()


def _enviar_revisao(s, chat_id, mes):
    from controle_financeiro.classificador import Classificador
    from controle_financeiro.ia.fallback import criar_fallback_ia
    from controle_financeiro.revisao import (reclassificar_pendentes,
                                             categorias_frequentes, transacoes_para_revisar)
    from controle_financeiro.telegram.botoes import montar_teclado
    fallback = None
    if os.environ.get("LLM_API_KEY"):
        from deploy.cliente_ia import criar_cliente_ia
        fallback = criar_fallback_ia(criar_cliente_ia())
    classificador = Classificador(s, fallback=fallback)
    reclassificar_pendentes(s, classificador, mes, limite=12)
    freq = categorias_frequentes(s)
    itens = transacoes_para_revisar(s, mes, limite=12)
    if not itens:
        responder_chat(chat_id, "Nada pra revisar agora — tudo classificado! \U0001F389 "
                                "(use /pendentes pra conferir)")
        return
    for item in itens:
        responder_chat_botoes(
            chat_id,
            f'{item.get("data","")} \u00b7 "{item["estabelecimento"]}" R$ {item["valor"]:.0f}',
            montar_teclado(item["id"], item["categoria_nome"], freq))


def _enviar_correcao(s, chat_id, mes, termo):
    from controle_financeiro.revisao import categorias_frequentes, transacoes_para_corrigir
    from controle_financeiro.telegram.botoes import montar_teclado
    freq = categorias_frequentes(s)
    itens = transacoes_para_corrigir(s, mes, termo=termo, limite=12)
    if not itens:
        extra = f" com \u201c{termo}\u201d" if termo else ""
        responder_chat(chat_id, f"N\u00e3o achei transa\u00e7\u00f5es{extra} neste m\u00eas.")
        return
    for item in itens:
        atual = item["categoria_nome"] or "\u2014"
        responder_chat_botoes(
            chat_id,
            f'{item.get("data","")} \u00b7 "{item["estabelecimento"]}" R$ {item["valor"]:.0f}\n'
            f'atual: {atual}',
            montar_teclado(item["id"], item["categoria_nome"], freq))


def _atualizar_fatura(s, transacao_id):
    """Reflete a correção na aba 'Fatura [mês]' imediatamente -> DRE soma na hora."""
    from controle_financeiro.models import Transacao
    from controle_financeiro.dre_fatura import linhas_para_fatura
    from deploy.sheets_adapter import criar_escritor_fatura
    t = s.get(Transacao, transacao_id)
    if not t or not t.mes_competencia:
        return
    try:
        criar_escritor_fatura()(t.mes_competencia, linhas_para_fatura(s, t.mes_competencia))
    except Exception:  # noqa: BLE001
        pass
