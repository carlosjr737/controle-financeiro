"""Consultas pro bot: detalhe de linha, pendentes, contexto p/ IA e comandos."""
from controle_financeiro.comparador import comparar_orcamento
from controle_financeiro.models import Transacao, Categoria

def detalhe_linha(sessao, mes: str, categoria_nome: str,
                  realizado_externo: dict | None = None) -> str:
    alvo = categoria_nome.strip().lower()
    linhas = {l["linha"].lower(): l
              for l in comparar_orcamento(sessao, mes, realizado_externo=realizado_externo)}
    l = linhas.get(alvo)
    cat = sessao.query(Categoria).filter(
        Categoria.nome.ilike(categoria_nome.strip())).one_or_none()
    if l is None and cat is None:
        return f"Não achei a categoria “{categoria_nome}”. Veja os nomes na aba Orçamentos."
    partes = []
    if l:
        marca = "estourou" if l["status"] == "vermelho" else f"{l['pct']:.0%}"
        partes.append(f"{l['linha']}: R$ {l['realizado']:.0f} / R$ {l['meta']:.0f} ({marca})")
    if cat:
        txs = (sessao.query(Transacao)
               .filter(Transacao.categoria_id == cat.id,
                       Transacao.mes_competencia == mes,
                       Transacao.status_classificacao != "estorno").all())
        if not l:
            partes.append(f"{cat.nome}: R$ {sum(abs(t.valor) for t in txs):.0f} (sem meta no orçamento)")
        for t in txs[:15]:
            partes.append(f"  - {t.data or ''} {t.estabelecimento[:24]} R$ {abs(t.valor):.0f}")
    return "\n".join(partes)

def pendentes_texto(sessao, mes: str) -> str:
    pend = (sessao.query(Transacao)
            .filter(Transacao.mes_competencia == mes,
                    Transacao.status_classificacao == "pendente").all())
    if not pend:
        return "Nenhum pendente. 🎉"
    partes = [f"Pendentes ({len(pend)}):"]
    for t in pend[:30]:
        partes.append(f"  - {t.estabelecimento[:26]} R$ {abs(t.valor):.0f}")
    return "\n".join(partes)

def contexto_para_ia(sessao, mes: str, realizado_externo: dict | None = None) -> str:
    linhas = comparar_orcamento(sessao, mes, realizado_externo=realizado_externo)
    partes = [f"Mês (ciclo de fatura): {mes}",
              "Fonte de verdade = aba Fatura/DRE (cartão + Pix por categoria).",
              "Orçamento (gasto / meta):"]
    for l in linhas:
        partes.append(f"- {l['linha']}: R$ {l['realizado']:.0f} / R$ {l['meta']:.0f}")
    total = sum(l["realizado"] for l in linhas
                if (l["linha"] or "").strip().upper() != "PGTO FATURA")
    partes.append(f"Total gasto no mês (cartão + Pix): R$ {total:.0f}")
    txs = (sessao.query(Transacao)
           .filter(Transacao.mes_competencia == mes,
                   Transacao.status_classificacao != "estorno")
           .order_by(Transacao.id.desc()).limit(40).all())
    partes.append("Transações recentes (estab | valor | categoria):")
    for t in txs:
        cat = sessao.get(Categoria, t.categoria_id) if t.categoria_id else None
        partes.append(f"- {t.estabelecimento[:26]} | R$ {abs(t.valor):.0f} | {cat.nome if cat else '?'}")
    return "\n".join(partes)

def responder_comando(sessao, texto: str, mes: str, teto, hoje: str,
                      realizado_externo: dict | None = None) -> str:
    partes = texto.split(maxsplit=1)
    cmd = partes[0].lower()
    arg = partes[1] if len(partes) > 1 else ""
    if cmd in ("/resumo", "/start"):
        from controle_financeiro.telegram.resumo import montar_resumo_diario
        return montar_resumo_diario(sessao, mes, hoje, teto=teto,
                                    realizado_externo=realizado_externo)
    if cmd == "/linha":
        if not arg:
            return "Use: /linha <categoria>. Ex.: /linha Uber"
        return detalhe_linha(sessao, mes, arg, realizado_externo=realizado_externo)
    if cmd == "/pendentes":
        return pendentes_texto(sessao, mes)
    if cmd == "/ajuda":
        return ("Comandos:\n/resumo — status do mês\n/revisar — classificar gastos (botões)\n"
                "/linha <categoria> — detalhe de uma linha\n/pendentes — o que falta confirmar\n"
                "/corrigir <termo> — trocar a categoria de um gasto\n\n"
                "Ou mande uma pergunta normal, ex.: “quanto gastei com iFood?”")
    return "Não conheço esse comando. Mande /ajuda."
