from controle_financeiro.fontes.banco_mcp import BancoMcpFonte

def transporte_fake(caminho, params):
    # simula o GET REST do Banco MCP
    assert caminho == "/v1/openfinance/transactions"
    return {"results": [
        {"id": "t1", "description": "DL *UBERRIDES", "amount": 27.98,
         "date": "2026-05-06", "type": "DEBIT",
         "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},
        {"id": "t2", "description": "SPOTIFY", "amount": 40.9, "date": "2026-05-06",
         "type": "DEBIT", "creditCardMetadata": {"installmentNumber": 1, "totalInstallments": 1}},
    ]}

def test_busca_transacoes_retorna_raws():
    fonte = BancoMcpFonte(transporte=transporte_fake, account_id="acc1")
    raws = fonte.buscar_transacoes(desde="2026-05-01", ate="2026-05-31")
    assert len(raws) == 2
    assert raws[0]["id"] == "t1"
