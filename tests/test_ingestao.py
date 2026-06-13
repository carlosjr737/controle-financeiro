from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.classificador import Classificador
from controle_financeiro.models import Transacao
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.ingestao import ingerir

def _transporte(_caminho, _params):
    return {"results": [
        {"id": "t1", "description": "DL *UBERRIDES", "amount": 27.98, "date": "2026-05-06",
         "type": "DEBIT", "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},
        {"id": "t1", "description": "DL *UBERRIDES", "amount": 27.98, "date": "2026-05-06",
         "type": "DEBIT", "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},  # duplicada
        {"id": "tX", "description": "LOJA NUNCA VISTA", "amount": 12.0, "date": "2026-05-06",
         "type": "DEBIT", "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},
    ]}

def test_ingestao_dedup_e_classifica(planilha_fake):
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    importar_historico(planilha_fake, s)        # dá regra pra "UBERRIDES" -> Uber
    gerar_regras_do_historico(s)
    fonte = BancoMcpFonte(transporte=_transporte, account_id="acc1")

    resumo = ingerir(s, fonte, Classificador(s), desde="2026-05-01", ate="2026-05-31",
                     portador="Carlos")

    assert resumo["recebidas"] == 3
    assert resumo["novas"] == 2            # t1 e tX (a 2a t1 é duplicada)
    assert resumo["duplicadas"] == 1
    uber = s.query(Transacao).filter_by(id_externo="t1").one()
    assert uber.status_classificacao == "sugerida" and uber.confianca == 1.0
    desconhecida = s.query(Transacao).filter_by(id_externo="tX").one()
    assert desconhecida.status_classificacao == "pendente"
