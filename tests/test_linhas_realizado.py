# tests/test_linhas_realizado.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.fechamento import gerar_linhas_realizado

def test_gera_linhas_com_diferenca():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    uber = Categoria(nome="Uber", grupo="Transporte"); s.add(uber); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="UBER", valor=380.0, categoria_id=uber.id,
                    mes_competencia="2026-06"))
    s.commit()

    linhas = gerar_linhas_realizado(s, "2026-06")
    assert linhas == [{"grupo": "Transporte", "linha": "Uber", "meta": 450.0,
                       "realizado": 380.0, "diferenca": 70.0}]
