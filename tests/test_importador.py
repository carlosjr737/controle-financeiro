from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.importador import importar_historico

def test_importa_faturas_e_categorias(planilha_fake):
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = criar_sessao(engine)

    importar_historico(planilha_fake, s)

    # categorias vieram da aba Classificações
    assert s.query(Categoria).filter_by(nome="Uber").count() == 1
    # 3 transacoes importadas
    assert s.query(Transacao).count() == 3
    # estorno classificado como tal (categoria None, status especial)
    estorno = s.query(Transacao).filter(Transacao.valor < 0).one()
    assert estorno.status_classificacao == "estorno"
