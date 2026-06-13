from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Regra, Transacao

def test_persistir_categoria_regra_transacao():
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = criar_sessao(engine)

    cat = Categoria(nome="Uber", grupo="Transporte", tipo="Despesa")
    s.add(cat); s.flush()
    s.add(Regra(padrao="UBER", categoria_id=cat.id, prioridade=100, origem="bootstrap"))
    s.add(Transacao(estabelecimento="DL *UBERRIDES", portador="Carlos",
                    valor=27.98, tipo="cartao", categoria_id=cat.id,
                    status_classificacao="confirmada", confianca=1.0,
                    mes_competencia="2026-05"))
    s.commit()

    assert s.query(Categoria).count() == 1
    assert s.query(Regra).count() == 1
    assert s.query(Transacao).first().categoria_id == cat.id
