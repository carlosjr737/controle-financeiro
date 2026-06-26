"""Projeção determinística de parcelas na fatura aberta."""
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Transacao
from controle_financeiro.parcelas import projecao_parcelas, _parse_parcela


def _s():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e)
    return criar_sessao(e)


def test_parse_parcela():
    assert _parse_parcela("3 de 6") == (3, 6)
    assert _parse_parcela("12 de 12") == (12, 12)
    assert _parse_parcela(None) is None
    assert _parse_parcela("avulsa") is None


def test_projeta_parcelas_ativas_da_fatura_anterior():
    s = _s()
    # fatura anterior (junho): 3 parcelas, 2 ativas (n<total) e 1 finalizada
    s.add(Transacao(estabelecimento="ROMA", valor=491.65, tipo="cartao",
                    parcela="3 de 6", mes_competencia="2026-06"))
    s.add(Transacao(estabelecimento="ASAAS", valor=377.00, tipo="cartao",
                    parcela="3 de 12", mes_competencia="2026-06"))
    s.add(Transacao(estabelecimento="FIM", valor=39.93, tipo="cartao",
                    parcela="12 de 12", mes_competencia="2026-06"))   # acabou
    s.commit()
    # nada lançado ainda em julho -> projeta as 2 ativas
    proj = projecao_parcelas(s, "2026-07", "2026-06")
    assert proj == round(491.65 + 377.00, 2)


def test_nao_conta_em_dobro_quando_parcela_ja_postou():
    s = _s()
    s.add(Transacao(estabelecimento="ROMA", valor=491.65, tipo="cartao",
                    parcela="3 de 6", mes_competencia="2026-06"))
    s.add(Transacao(estabelecimento="ASAAS", valor=377.00, tipo="cartao",
                    parcela="3 de 12", mes_competencia="2026-06"))
    # a parcela da ROMA já postou em julho (4 de 6)
    s.add(Transacao(estabelecimento="ROMA", valor=491.65, tipo="cartao",
                    parcela="4 de 6", mes_competencia="2026-07"))
    s.commit()
    proj = projecao_parcelas(s, "2026-07", "2026-06")
    assert proj == 377.00   # só a ASAAS falta postar
