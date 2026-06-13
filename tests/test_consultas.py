from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.consultas import (detalhe_linha, pendentes_texto,
                                           contexto_para_ia, responder_comando)

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    uber = Categoria(nome="Uber", grupo="Transporte"); s.add(uber); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="DL*Uber", valor=380.0, data="2026-06-10",
                    categoria_id=uber.id, mes_competencia="2026-06", status_classificacao="sugerida"))
    s.add(Transacao(estabelecimento="LOJA X", valor=99.0, mes_competencia="2026-06",
                    status_classificacao="pendente"))
    s.commit(); return s

def test_detalhe_linha():
    s = _sessao()
    txt = detalhe_linha(s, "2026-06", "uber")   # case-insensitive
    assert "Uber: R$ 380 / R$ 450" in txt and "DL*Uber" in txt

def test_pendentes_texto():
    s = _sessao()
    assert "Pendentes (1)" in pendentes_texto(s, "2026-06") and "LOJA X" in pendentes_texto(s, "2026-06")

def test_contexto_para_ia():
    s = _sessao()
    ctx = contexto_para_ia(s, "2026-06")
    assert "Uber: R$ 380 / R$ 450" in ctx and "DL*Uber" in ctx

def test_responder_comando():
    s = _sessao()
    assert "Uber" in responder_comando(s, "/linha Uber", "2026-06", 27060, "2026-06-13")
    assert "Pendentes" in responder_comando(s, "/pendentes", "2026-06", 27060, "2026-06-13")
    assert "Comandos" in responder_comando(s, "/ajuda", "2026-06", 27060, "2026-06-13")
    assert "Resumo de" in responder_comando(s, "/resumo", "2026-06", 27060, "2026-06-13")
