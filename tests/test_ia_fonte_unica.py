"""IA e /resumo devem usar a MESMA fonte (aba Fatura) — sem dispersão de dados."""
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.consultas import contexto_para_ia, detalhe_linha


def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    c = Categoria(nome="Lazer", grupo="Lazer"); s.add(c); s.flush()
    s.add(Orcamento(mes="2026-07", grupo="Lazer", linha="Lazer", valor_meta=600.0))
    # no banco só R$ 100 (sub-captado); a verdade vem da aba Fatura
    s.add(Transacao(estabelecimento="Bar", valor=100.0, categoria_id=c.id,
                    mes_competencia="2026-07", status_classificacao="sugerida"))
    s.commit()
    return s


def test_contexto_ia_usa_total_da_fatura():
    s = _sessao()
    externo = {"Lazer": 4273.0}
    ctx = contexto_para_ia(s, "2026-07", realizado_externo=externo)
    assert "Lazer: R$ 4273 / R$ 600" in ctx          # usa a aba Fatura, não o banco (100)
    assert "Total gasto no mês (cartão + Pix): R$ 4273" in ctx


def test_detalhe_linha_usa_total_da_fatura():
    s = _sessao()
    txt = detalhe_linha(s, "2026-07", "Lazer", realizado_externo={"Lazer": 4273.0})
    assert "4273" in txt and "600" in txt
