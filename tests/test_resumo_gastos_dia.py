from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.telegram.resumo import montar_resumo_diario

def test_lista_gastos_do_dia():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    uber = Categoria(nome="Uber"); s.add(uber); s.flush()
    s.add(Transacao(estabelecimento="DL*UberRides", valor=20.0, data="2026-06-13",
                    categoria_id=uber.id, mes_competencia="2026-06",
                    status_classificacao="sugerida"))
    s.add(Transacao(estabelecimento="ONTEM", valor=99.0, data="2026-06-12",
                    mes_competencia="2026-06", status_classificacao="sugerida"))
    s.commit()
    texto = montar_resumo_diario(s, mes="2026-06", data="2026-06-13", teto=27060.0)
    assert "Gastos de hoje (1)" in texto
    assert "DL*UberRides" in texto and "Uber" in texto
    assert "ONTEM" not in texto   # é de ontem, não entra

def test_sem_gastos_hoje():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    texto = montar_resumo_diario(s, mes="2026-06", data="2026-06-13")
    assert "Sem gastos novos hoje." in texto
