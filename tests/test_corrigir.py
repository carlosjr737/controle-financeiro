from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.revisao import transacoes_para_corrigir

def test_corrigir_inclui_ja_classificadas_e_filtra_por_termo():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    uber = Categoria(nome="Uber"); s.add(uber); s.flush()
    s.add(Transacao(estabelecimento="DL*UberRides", valor=20, categoria_id=uber.id,
                    mes_competencia="2026-07", status_classificacao="confirmada", confianca=1.0))
    s.add(Transacao(estabelecimento="SUPERMERCADO", valor=50, categoria_id=uber.id,
                    mes_competencia="2026-07", status_classificacao="sugerida", confianca=1.0))
    s.commit()
    # sem termo: pega as duas (mesmo confirmadas/alta confiança)
    assert len(transacoes_para_corrigir(s, "2026-07")) == 2
    # com termo: filtra
    itens = transacoes_para_corrigir(s, "2026-07", termo="uber")
    assert len(itens) == 1 and itens[0]["estabelecimento"] == "DL*UberRides"
