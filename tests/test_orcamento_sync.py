from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Orcamento, Categoria
from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento

LINHAS = [
    {"tipo": "Custos fixos", "grupo": "Transporte", "linha": "Uber",
     "orcamento_meta": 450.0, "observacao": "Corte forte"},
    {"tipo": "Despesas", "grupo": "Lazer", "linha": "Restaurantes",
     "orcamento_meta": 1500.0, "observacao": "Corte forte"},
]

def test_sincroniza_orcamento_e_cria_categorias():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    n = sincronizar_orcamento(s, mes="2026-06", leitor=lambda: LINHAS)
    assert n == 2
    assert s.query(Orcamento).count() == 2
    # garante categorias (linha) no vocabulário
    assert s.query(Categoria).filter_by(nome="Uber").count() == 1

def test_resync_substitui_o_mes():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    sincronizar_orcamento(s, mes="2026-06", leitor=lambda: LINHAS)
    sincronizar_orcamento(s, mes="2026-06", leitor=lambda: LINHAS[:1])  # re-sync
    assert s.query(Orcamento).filter_by(mes="2026-06").count() == 1
