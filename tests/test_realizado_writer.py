# tests/test_realizado_writer.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.sheets.realizado_writer import escrever_realizado

def test_escreve_aba_realizado_via_escritor():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    uber = Categoria(nome="Uber", grupo="Transporte"); s.add(uber); s.flush()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="UBER", valor=380.0, categoria_id=uber.id,
                    mes_competencia="2026-06"))
    s.commit()

    capturado = {}
    def escritor(aba, linhas):
        capturado["aba"] = aba
        capturado["linhas"] = linhas
        return len(linhas)

    n = escrever_realizado(s, "2026-06", escritor)
    assert n == 1
    assert capturado["aba"] == "Realizado 2026-06"
    assert capturado["linhas"][0]["linha"] == "Uber"
