# controle_financeiro/telegram/resumo.py
from calendar import monthrange
from controle_financeiro.models import Transacao
from controle_financeiro.comparador import comparar_orcamento, projecao_fechamento
from controle_financeiro.alertas import linhas_em_alerta

def montar_resumo_diario(sessao, mes: str, data: str, teto: float | None = None) -> str:
    linhas = comparar_orcamento(sessao, mes)
    alertas = linhas_em_alerta(linhas)
    pendentes = (sessao.query(Transacao)
                 .filter(Transacao.mes_competencia == mes,
                         Transacao.status_classificacao == "pendente").all())

    partes = [f"Resumo de {data}"]

    if alertas:
        partes.append("Orçamento em atenção:")
        for a in alertas:
            marca = "estourou" if a["status"] == "vermelho" else f"{a['pct']:.0%}"
            partes.append(f"  - {a['linha']}: R$ {a['realizado']:.0f} / "
                          f"R$ {a['meta']:.0f} ({marca})")
    else:
        partes.append("Nenhuma linha em alerta. ")

    if pendentes:
        partes.append(f"Pra confirmar ({len(pendentes)}):")
        for t in pendentes:
            partes.append(f"  - \"{t.estabelecimento}\" R$ {abs(t.valor):.0f}")

    realizado_total = sum(l["realizado"] for l in linhas)
    dias_no_mes = monthrange(int(mes[:4]), int(mes[5:7]))[1]
    dia_atual = int(data[8:10])
    proj = projecao_fechamento(realizado_total, dia_atual, dias_no_mes)
    linha_teto = f" vs teto R$ {teto:.0f}" if teto else ""
    partes.append(f"Projeção de fechamento: R$ {proj:.0f}{linha_teto}")

    return "\n".join(partes)
