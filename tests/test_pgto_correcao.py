from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.aprendizado import corrigir_por_categoria_id

def test_corrigir_para_pgto_fatura_fica_negativo():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    pgto = Categoria(nome="PGTO FATURA"); s.add(pgto); s.flush()
    t = Transacao(estabelecimento="ALGO", valor=5000.0, mes_competencia="2026-07",
                  status_classificacao="sugerida", confianca=1.0)
    s.add(t); s.commit()
    corrigir_por_categoria_id(s, t.id, pgto.id)
    assert t.valor == -5000.0
    assert t.status_classificacao == "pagamento"
    assert t.categoria_id == pgto.id
