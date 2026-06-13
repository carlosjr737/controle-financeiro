from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.classificador import Classificador
from controle_financeiro.avaliacao import avaliar_acuracia

def test_acuracia_no_historico_conhecido(planilha_fake):
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    importar_historico(planilha_fake, s)
    gerar_regras_do_historico(s)

    rel = avaliar_acuracia(s, Classificador(s))

    # Uber e Streamings sao recorrentes => devem acertar 100% via regra
    assert rel["total"] == 2
    assert rel["acertos"] == 2
    assert rel["acuracia"] == 1.0
