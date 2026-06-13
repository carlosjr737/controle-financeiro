from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Transacao
from controle_financeiro.upsert import upsert_transacao

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

DADOS = {"id_externo": "tx1", "estabelecimento": "UBER", "valor": 10.0,
         "data": "2026-05-01", "parcela": None, "tipo": "cartao",
         "portador": "Carlos", "mes_competencia": "2026-05"}

def test_insere_quando_novo():
    s = _sessao()
    t, criada = upsert_transacao(s, DADOS)
    assert criada is True
    assert s.query(Transacao).count() == 1

def test_nao_duplica_mesmo_id_externo():
    s = _sessao()
    upsert_transacao(s, DADOS)
    t, criada = upsert_transacao(s, {**DADOS, "valor": 99.0})  # mesmo id_externo
    assert criada is False
    assert s.query(Transacao).count() == 1
    assert s.query(Transacao).one().valor == 99.0   # atualizou valor
