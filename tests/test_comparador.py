# tests/test_comparador.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.comparador import comparar_orcamento

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

def test_compara_meta_vs_realizado():
    s = _sessao()
    uber = Categoria(nome="Uber", grupo="Transporte", tipo="Despesa")
    lazer = Categoria(nome="Lazer", grupo="Lazer", tipo="Despesa")
    s.add_all([uber, lazer]); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Orcamento(mes="2026-06", grupo="Lazer", linha="Lazer", valor_meta=800.0))
    # realizado: Uber 380 (84%), Lazer 1000 (estourou)
    s.add(Transacao(estabelecimento="UBER", valor=380.0, tipo="cartao",
                    categoria_id=uber.id, mes_competencia="2026-06"))
    s.add(Transacao(estabelecimento="X", valor=1000.0, tipo="cartao",
                    categoria_id=lazer.id, mes_competencia="2026-06"))
    s.commit()

    linhas = {l["linha"]: l for l in comparar_orcamento(s, "2026-06")}
    assert linhas["Uber"]["realizado"] == 380.0
    assert round(linhas["Uber"]["pct"], 2) == 0.84
    assert linhas["Uber"]["status"] == "amarelo"
    assert linhas["Lazer"]["status"] == "vermelho"

def test_ignora_estorno_no_realizado():
    s = _sessao()
    c = Categoria(nome="Restaurantes", grupo="Lazer", tipo="Despesa"); s.add(c); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Lazer", linha="Restaurantes", valor_meta=100.0))
    s.add(Transacao(estabelecimento="R", valor=120.0, categoria_id=c.id,
                    mes_competencia="2026-06", status_classificacao="estorno"))
    s.commit()
    linhas = {l["linha"]: l for l in comparar_orcamento(s, "2026-06")}
    assert linhas["Restaurantes"]["realizado"] == 0.0
