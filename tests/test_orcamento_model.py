from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Orcamento

def test_persistir_orcamento():
    engine = criar_engine("sqlite://"); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber",
                    valor_meta=450.0, observacao="Corte forte"))
    s.commit()
    o = s.query(Orcamento).one()
    assert o.linha == "Uber" and o.valor_meta == 450.0
