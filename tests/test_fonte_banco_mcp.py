from controle_financeiro.fontes.banco_mcp import BancoMcpFonte

def _transporte(caminho, body):
    assert caminho == "/transactions/list"
    assert body["account_id"] == "acc1"
    return {"ok": True, "tool": "openfinance_list_transactions",
            "result": {"total": 2, "results": [
                {"id": "t1", "description": "DL *UBERRIDES"},
                {"id": "t2", "description": "SPOTIFY"}]}}

def test_busca_transacoes_retorna_results():
    fonte = BancoMcpFonte(transporte=_transporte, account_id="acc1")
    raws = fonte.buscar_transacoes(desde="2026-05-01", ate="2026-05-31")
    assert len(raws) == 2
    assert raws[0]["id"] == "t1"
