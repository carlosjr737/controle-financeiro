from controle_financeiro.models import Transacao, Categoria
from controle_financeiro.comparador import comparar_orcamento

def montar_resumo_diario(sessao, mes: str, data: str, teto: float | None = None,
                         realizado_externo: dict | None = None,
                         fatura_cartao: dict | None = None) -> str:
    linhas = comparar_orcamento(sessao, mes, realizado_externo=realizado_externo)
    pendentes = (sessao.query(Transacao)
                 .filter(Transacao.mes_competencia == mes,
                         Transacao.status_classificacao == "pendente").all())

    partes = [f"Resumo de {data}"]

    # gastos do dia (cartão lançado hoje)
    do_dia = (sessao.query(Transacao)
              .filter(Transacao.data == data,
                      Transacao.status_classificacao.notin_(["estorno", "pagamento"])).all())
    if do_dia:
        total_dia = sum(abs(t.valor) for t in do_dia)
        partes.append(f"Gastos de hoje ({len(do_dia)}): R$ {total_dia:.0f}")
        for t in do_dia[:20]:
            cat = sessao.get(Categoria, t.categoria_id) if t.categoria_id else None
            partes.append(f"  - {t.estabelecimento[:28]} R$ {abs(t.valor):.0f} "
                          f"({cat.nome if cat else '?'})")
    else:
        partes.append("Sem gastos novos hoje.")

    # total = espelho da Fatura/DRE quando vier de fora; senão, do banco
    if realizado_externo is not None:
        realizado_total = sum(v for k, v in realizado_externo.items()
                              if v > 0 and k.strip().upper() != "PGTO FATURA")
    else:
        todas = (sessao.query(Transacao)
                 .filter(Transacao.mes_competencia == mes,
                         Transacao.status_classificacao.notin_(["estorno", "pagamento"])).all())
        realizado_total = sum(abs(t.valor) for t in todas)
    # parcelas já contratadas que ainda vão cair na fatura (postam no fechamento);
    # no mês fechado, é a diferença pro valor oficial do banco
    parcelas = (fatura_cartao or {}).get("parcelas", 0.0) or 0.0
    realizado_total += parcelas
    teto_txt = f" (teto R$ {teto:.0f})" if teto else ""
    partes.append(f"Já gasto no mês: R$ {realizado_total:.0f}{teto_txt}")

    if fatura_cartao and fatura_cartao.get("total"):
        if fatura_cartao.get("oficial"):
            partes.append(f"💳 Fatura cartão (oficial do banco): R$ {fatura_cartao['total']:.0f}")
        else:
            partes.append(
                f"💳 Fatura cartão (parcial): R$ {fatura_cartao['total']:.0f} "
                f"— compras R$ {fatura_cartao['compras']:.0f} + "
                f"parcelas a vencer R$ {parcelas:.0f}")

    # FOCO: o que estourou e o que está quase
    estourou = sorted([l for l in linhas if l["status"] == "vermelho"],
                      key=lambda l: l["pct"], reverse=True)
    quase = sorted([l for l in linhas if l["status"] == "amarelo"],
                   key=lambda l: l["pct"], reverse=True)

    if estourou:
        partes.append("🔴 Estourou:")
        for a in estourou:
            partes.append(f"  - {a['linha']}: R$ {a['realizado']:.0f} / R$ {a['meta']:.0f} "
                          f"(+R$ {a['realizado'] - a['meta']:.0f})")
    if quase:
        partes.append("🟡 Quase estourando:")
        for a in quase:
            partes.append(f"  - {a['linha']}: R$ {a['realizado']:.0f} / R$ {a['meta']:.0f} "
                          f"({a['pct']:.0%})")
    if not estourou and not quase:
        partes.append("🟢 Tudo dentro do orçamento.")

    if pendentes:
        partes.append(f"Pra confirmar ({len(pendentes)}) — veja os botões abaixo.")

    return "\n".join(partes)
