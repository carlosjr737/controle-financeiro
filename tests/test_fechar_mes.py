# tests/test_fechar_mes.py
import json
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao, FechamentoMensal
from controle_financeiro.fechamento import fechar_mes

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

def test_fecha_mes_calcula_totais_e_marca_status():
    s = _sessao()
    uber = Categoria(nome="Uber", grupo="Transporte"); s.add(uber); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="UBER", valor=380.0, categoria_id=uber.id,
                    mes_competencia="2026-06"))
    s.commit()

    resumo = fechar_mes(s, "2026-06", hoje="2026-07-01")

    assert resumo["meta_total"] == 450.0
    assert resumo["realizado_total"] == 380.0
    assert resumo["economia_vs_orcado"] == 70.0
    f = s.query(FechamentoMensal).filter_by(mes="2026-06").one()
    assert f.status == "fechado" and f.data_fechamento == "2026-07-01"
    assert json.loads(f.totais_json)["realizado_total"] == 380.0

def test_fechar_mes_e_idempotente():
    s = _sessao()
    fechar_mes(s, "2026-06", hoje="2026-07-01")
    fechar_mes(s, "2026-06", hoje="2026-07-02")
    assert s.query(FechamentoMensal).filter_by(mes="2026-06").count() == 1
