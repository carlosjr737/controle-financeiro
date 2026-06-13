from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.classificador import Classificador
from controle_financeiro.revisao import (reclassificar_pendentes,
                                         categorias_frequentes, transacoes_para_revisar)
from controle_financeiro.models import Regra

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

def test_para_revisar_ignora_alta_confianca():
    s = _sessao()
    c = Categoria(nome="Uber"); s.add(c); s.flush()
    s.add(Transacao(estabelecimento="A", valor=10, categoria_id=c.id, mes_competencia="2026-06",
                    status_classificacao="sugerida", confianca=1.0))   # regra: não revisa
    s.add(Transacao(estabelecimento="B", valor=20, mes_competencia="2026-06",
                    status_classificacao="pendente", confianca=0.0))   # revisa
    s.add(Transacao(estabelecimento="C", valor=30, categoria_id=c.id, mes_competencia="2026-06",
                    status_classificacao="sugerida", confianca=0.5))   # IA: revisa
    s.commit()
    itens = transacoes_para_revisar(s, "2026-06")
    estabs = {i["estabelecimento"] for i in itens}
    assert estabs == {"B", "C"}

def test_reclassificar_pendentes_usa_classificador():
    s = _sessao()
    cat = Categoria(nome="Uber"); s.add(cat); s.flush()
    s.add(Regra(padrao="UBERX", categoria_id=cat.id, prioridade=100, origem="bootstrap"))
    t = Transacao(estabelecimento="UBERX", valor=10, mes_competencia="2026-06",
                  status_classificacao="pendente", confianca=0.0)
    s.add(t); s.commit()
    n = reclassificar_pendentes(s, Classificador(s), "2026-06")
    assert n == 1
    assert t.status_classificacao == "sugerida" and t.categoria_id == cat.id

def test_categorias_frequentes():
    s = _sessao()
    a = Categoria(nome="Supermercado"); b = Categoria(nome="Uber"); s.add_all([a, b]); s.flush()
    for _ in range(3):
        s.add(Transacao(estabelecimento="x", valor=1, categoria_id=a.id, mes_competencia="2026-06"))
    s.add(Transacao(estabelecimento="y", valor=1, categoria_id=b.id, mes_competencia="2026-06"))
    s.commit()
    freq = categorias_frequentes(s, n=2)
    assert freq[0][1] == "Supermercado"   # mais frequente primeiro
