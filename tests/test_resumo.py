# tests/test_resumo.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.telegram.resumo import montar_resumo_diario

def test_resumo_contem_alertas_e_pendentes():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    lazer = Categoria(nome="Lazer", grupo="Lazer"); s.add(lazer); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Lazer", linha="Lazer", valor_meta=800.0))
    s.add(Transacao(estabelecimento="X", valor=1000.0, categoria_id=lazer.id,
                    mes_competencia="2026-06", status_classificacao="sugerida"))
    s.add(Transacao(estabelecimento="MSN BELVEDERE", valor=340.0,
                    mes_competencia="2026-06", status_classificacao="pendente"))
    s.commit()

    texto = montar_resumo_diario(s, mes="2026-06", data="2026-06-13", teto=27060.0)

    assert "Resumo de 2026-06-13" in texto
    assert "Lazer" in texto and "estourou" in texto.lower()
    assert "Pra confirmar (1)" in texto      # pendentes agora vão pros botões
    assert "Projeção" in texto
