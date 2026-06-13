from controle_financeiro.fontes.banco_mcp import BancoMcpFonte

def test_inclui_page_size_nos_params():
    capturado = {}
    def transporte(caminho, params):
        capturado.update(params)
        return {"results": []}
    BancoMcpFonte(transporte=transporte, account_id="acc1", page_size=150)\
        .buscar_transacoes("2026-06-01", "2026-06-07")
    assert capturado["page_size"] == 150
    assert capturado["account_id"] == "acc1"
