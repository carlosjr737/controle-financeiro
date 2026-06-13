# tests/test_aprendizado.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao, Regra
from controle_financeiro.classificador import Classificador
from controle_financeiro.aprendizado import registrar_correcao

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

def test_correcao_atualiza_transacao_e_cria_regra_prioritaria():
    s = _sessao()
    cursos = Categoria(nome="Cursos"); ifood = Categoria(nome="Ifood")
    s.add_all([cursos, ifood]); s.flush()
    # regra ruim do bootstrap: "CURSOS EV LTDA" -> Ifood
    s.add(Regra(padrao="CURSOS EV LTDA", categoria_id=ifood.id, prioridade=100, origem="bootstrap"))
    t = Transacao(estabelecimento="IFD CURSOS EV LTDA", valor=120.0,
                  mes_competencia="2026-06", status_classificacao="pendente")
    s.add(t); s.commit()

    registrar_correcao(s, t.id, "Cursos")

    # transação confirmada na categoria certa
    assert t.status_classificacao == "confirmada"
    assert t.categoria_id == cursos.id
    # nova regra de prioridade alta sobrepõe o bootstrap
    r = Classificador(s).classificar("IFD CURSOS EV LTDA")
    assert r.categoria_nome == "Cursos"
    assert r.confianca == 1.0
