from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Transacao, Categoria
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.ingestao import ingerir
from controle_financeiro.regras_negocio import eh_pagamento_fatura

def test_eh_pagamento_fatura():
    assert eh_pagamento_fatura("Pagamento recebido") is True
    assert eh_pagamento_fatura("PAGAMENTO RECEBIDO - OBRIGADO") is True
    assert eh_pagamento_fatura("SUPERMERCADO E PADARIA") is False

def test_ingere_pagamento_como_negativo():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    def transporte(c, b):
        return {"result": {"results": [
            {"id": "p1", "description": "Pagamento recebido", "amount": "5000",
             "date": "2026-07-10",
             "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},
        ]}}
    fonte = BancoMcpFonte(transporte=transporte, account_id="acc1")
    ingerir(s, fonte, Classificador(s), "2026-07-01", "2026-07-31", tipo="cartao")
    t = s.query(Transacao).filter_by(id_externo="p1").one()
    assert t.valor == -5000.0
    assert t.status_classificacao == "pagamento"
    assert s.get(Categoria, t.categoria_id).nome == "PGTO FATURA"
