from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao, Regra
from controle_financeiro.aprendizado import confirmar_sugestao, corrigir_por_categoria_id

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

def test_confirmar_sugestao_vira_regra():
    s = _sessao()
    cat = Categoria(nome="Uber"); s.add(cat); s.flush()
    t = Transacao(estabelecimento="DL*UberRides", valor=10, categoria_id=cat.id,
                  mes_competencia="2026-06", status_classificacao="sugerida", confianca=0.5)
    s.add(t); s.commit()
    nome = confirmar_sugestao(s, t.id)
    assert nome == "Uber"
    assert t.status_classificacao == "confirmada"
    assert s.query(Regra).filter_by(origem="correcao").count() == 1

def test_corrigir_por_categoria_id():
    s = _sessao()
    errada = Categoria(nome="Ifood"); certa = Categoria(nome="Cursos")
    s.add_all([errada, certa]); s.flush()
    t = Transacao(estabelecimento="IFD CURSOS", valor=10, categoria_id=errada.id,
                  mes_competencia="2026-06", status_classificacao="sugerida", confianca=0.5)
    s.add(t); s.commit()
    nome = corrigir_por_categoria_id(s, t.id, certa.id)
    assert nome == "Cursos"
    assert t.categoria_id == certa.id and t.status_classificacao == "confirmada"
