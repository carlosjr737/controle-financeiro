# tests/test_bot.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao, Regra
from controle_financeiro.telegram.bot import enviar_resumo, processar_confirmacao

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); return criar_sessao(e)

def test_enviar_resumo_usa_callback():
    s = _sessao()
    enviados = []
    enviar_resumo(s, mes="2026-06", data="2026-06-13", enviar=enviados.append, teto=None)
    assert len(enviados) == 1
    assert "Resumo de 2026-06-13" in enviados[0]

def test_processar_confirmacao_aplica_correcao():
    s = _sessao()
    cat = Categoria(nome="Outros"); s.add(cat); s.flush()
    t = Transacao(estabelecimento="MSN BELVEDERE", valor=340.0,
                  mes_competencia="2026-06", status_classificacao="pendente")
    s.add(t); s.commit()

    processar_confirmacao(s, transacao_id=t.id, categoria_nome="Outros")

    assert t.status_classificacao == "confirmada"
    assert s.query(Regra).filter_by(origem="correcao").count() == 1
