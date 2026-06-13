from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.models import Regra
from controle_financeiro.normalizacao import normalizar_estabelecimento

def test_gera_regra_por_frequencia(planilha_fake):
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    importar_historico(planilha_fake, s)

    n = gerar_regras_do_historico(s)

    assert n >= 2  # Uber e Streamings viraram regra
    padroes = {r.padrao for r in s.query(Regra).all()}
    assert normalizar_estabelecimento("DL *UBERRIDES") in padroes  # "UBERRIDES"
