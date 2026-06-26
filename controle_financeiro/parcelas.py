"""Projeção determinística de parcelas na fatura aberta.

As parcelas postam como transações na data do fechamento (~dia 05). No meio do
ciclo elas ainda não entraram, então projetamos: cada parcela ATIVA da fatura
anterior (installmentNumber < totalInstallments) vai repetir o mesmo valor nesta
fatura. Subtraímos as que já postaram pra não contar em dobro."""
from controle_financeiro.models import Transacao


def _parse_parcela(p):
    """'3 de 6' -> (3, 6); None se não der."""
    try:
        a, b = (p or "").lower().split(" de ")
        return int(a.strip()), int(b.strip())
    except (ValueError, AttributeError):
        return None


def _soma_parcelas(sessao, mes, so_ativas=False):
    total = 0.0
    q = (sessao.query(Transacao)
         .filter(Transacao.mes_competencia == mes,
                 Transacao.tipo == "cartao",
                 Transacao.parcela.isnot(None)))
    for t in q:
        pr = _parse_parcela(t.parcela)
        if pr is None:
            continue
        if so_ativas and not (pr[0] < pr[1]):   # já é a última parcela -> não repete
            continue
        total += abs(t.valor)
    return total


def projecao_parcelas(sessao, mes_aberto: str, mes_anterior: str) -> float:
    """Valor de parcelas já contratadas que ainda vão cair na fatura aberta."""
    ativas_anteriores = _soma_parcelas(sessao, mes_anterior, so_ativas=True)
    ja_lancadas = _soma_parcelas(sessao, mes_aberto, so_ativas=False)
    return round(max(ativas_anteriores - ja_lancadas, 0.0), 2)
