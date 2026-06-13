# tests/test_fechamento_model.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import FechamentoMensal

def test_persistir_fechamento():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    s.add(FechamentoMensal(mes="2026-06", status="fechado",
                           data_fechamento="2026-07-01", totais_json='{"realizado": 100}'))
    s.commit()
    f = s.query(FechamentoMensal).one()
    assert f.mes == "2026-06" and f.status == "fechado"
