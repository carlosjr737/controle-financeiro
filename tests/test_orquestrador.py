# tests/test_orquestrador.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.orquestrador import executar_ciclo

def _transporte(_c, _p):
    return {"results": [
        {"id": "t1", "description": "DL *UBERRIDES", "amount": 27.98, "date": "2026-06-02",
         "type": "DEBIT", "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},
    ]}

def test_ciclo_ingere_e_envia_resumo(planilha_fake):
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    importar_historico(planilha_fake, s); gerar_regras_do_historico(s)
    fonte = BancoMcpFonte(transporte=_transporte, account_id="acc1")
    enviados = []

    resumo = executar_ciclo(s, fonte, Classificador(s), mes="2026-06",
                            data="2026-06-13", enviar=enviados.append,
                            desde="2026-06-01", ate="2026-06-30",
                            portador="Carlos", teto=27060.0)

    assert resumo["ingestao"]["novas"] == 1
    assert len(enviados) == 1
    assert "Resumo de 2026-06-13" in enviados[0]
