from calendar import monthrange
from controle_financeiro.models import Transacao, Categoria
from controle_financeiro.comparador import comparar_orcamento, projecao_fechamento
from controle_financeiro.alertas import linhas_em_alerta

def montar_resumo_diario(sessao, mes: str, data: str, teto: float | None = None) -> str:
    linhas = comparar_orcamento(sessao, mes)
    alertas = linhas_em_alerta(linhas)
    pendentes = (sessao.query(Transacao)
                 .filter(Transacao.mes_competencia == mes,
                         Transacao.status_classificacao == "pendente").all())

    partes = [f"Resumo de {data}"]

    # gastos do dia
    do_dia = (sessao.query(Transacao)
              .filter(Transacao.data == data,
                      Transacao.status_classificacao != "estorno").all())
    if do_dia:
        total_dia = sum(abs(t.valor) for t in do_dia)
        partes.append(f"Gastos de hoje ({len(do_dia)}): R$ {total_dia:.0f}")
        for t in do_dia[:20]:
            cat = sessao.get(Categoria, t.categoria_id) if t.categoria_id else None
            partes.append(f"  - {t.estabelecimento[:28]} R$ {abs(t.valor):.0f} "
                          f"({cat.nome if cat else '?'})")
    else:
        partes.append("Sem gastos novos hoje.")

    if alertas:
        partes.append("Orçamento em atenção:")
        for a in alertas:
            marca = "estourou" if a["status"] == "vermelho" else f"{a['pct']:.0%}"
            partes.append(f"  - {a['linha']}: R$ {a['realizado']:.0f} / "
                          f"R$ {a['meta']:.0f} ({marca})")

    if pendentes:
        partes.append(f"Pra confirmar ({len(pendentes)}) — veja os botões abaixo.")

    realizado_total = sum(l["realizado"] for l in linhas)
    dias_no_mes = monthrange(int(mes[:4]), int(mes[5:7]))[1]
    dia_atual = int(data[8:10])
    proj = projecao_fechamento(realizado_total, dia_atual, dias_no_mes)
    linha_teto = f" vs teto R$ {teto:.0f}" if teto else ""
    partes.append(f"Projeção de fechamento: R$ {proj:.0f}{linha_teto}")

    return "\n".join(partes)
