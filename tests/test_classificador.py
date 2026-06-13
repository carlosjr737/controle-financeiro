from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.classificador import Classificador

def _setup(planilha_fake):
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    importar_historico(planilha_fake, s)
    gerar_regras_do_historico(s)
    return s

def test_regra_exata_alta_confianca(planilha_fake):
    s = _setup(planilha_fake)
    c = Classificador(s)
    r = c.classificar("DL *UBERRIDES")
    assert r.categoria_nome == "Uber"
    assert r.confianca == 1.0
    assert r.origem == "regra"

def test_substring_confianca_media(planilha_fake):
    s = _setup(planilha_fake)
    c = Classificador(s)
    r = c.classificar("UBERRIDES SAO PAULO")     # contem padrao "UBERRIDES"
    assert r.categoria_nome == "Uber"
    assert 0.5 <= r.confianca < 1.0
    assert r.origem == "substring"

def test_desconhecido_usa_fallback(planilha_fake):
    s = _setup(planilha_fake)
    c = Classificador(s, fallback=lambda estab, cats: "Outros")
    r = c.classificar("LOJA NUNCA VISTA XYZ")
    assert r.categoria_nome == "Outros"
    assert r.origem == "fallback"

def test_desconhecido_sem_fallback_fica_pendente(planilha_fake):
    s = _setup(planilha_fake)
    c = Classificador(s)
    r = c.classificar("LOJA NUNCA VISTA XYZ")
    assert r.categoria_nome is None
    assert r.origem == "pendente"
