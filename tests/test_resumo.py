from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.telegram.resumo import montar_resumo_diario

def test_resumo_foca_em_estouro_e_quase():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    lazer = Categoria(nome="Lazer", grupo="Lazer")
    uber = Categoria(nome="Uber", grupo="Transporte")
    s.add_all([lazer, uber]); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Lazer", linha="Lazer", valor_meta=800.0))
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="X", valor=1000.0, categoria_id=lazer.id,
                    mes_competencia="2026-06", status_classificacao="sugerida"))   # estourou
    s.add(Transacao(estabelecimento="Y", valor=400.0, categoria_id=uber.id,
                    mes_competencia="2026-06", status_classificacao="sugerida"))   # 89% quase
    s.add(Transacao(estabelecimento="MSN", valor=340.0, mes_competencia="2026-06",
                    status_classificacao="pendente"))
    s.commit()
    texto = montar_resumo_diario(s, mes="2026-06", data="2026-06-13", teto=27060.0)
    assert "Resumo de 2026-06-13" in texto
    assert "Já gasto no mês: R$ 1400" in texto
    assert "🔴 Estourou:" in texto and "Lazer" in texto
    assert "🟡 Quase estourando:" in texto and "Uber" in texto
    assert "Projeção" not in texto                # removida
    assert "Pra confirmar (1)" in texto

def test_resumo_tudo_ok():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    c = Categoria(nome="Uber"); s.add(c); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="Y", valor=100.0, categoria_id=c.id,
                    mes_competencia="2026-06", status_classificacao="sugerida"))
    s.commit()
    texto = montar_resumo_diario(s, mes="2026-06", data="2026-06-13", teto=27060.0)
    assert "🟢 Tudo dentro do orçamento." in texto
