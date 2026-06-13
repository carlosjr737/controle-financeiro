from controle_financeiro.fontes.banco_mcp import BancoMcpFonte

def test_inclui_page_size_no_body():
    cap = {}
    def transporte(caminho, body):
        cap.update(body)
        return {"result": {"results": []}}
    BancoMcpFonte(transporte=transporte, account_id="acc1", page_size=150)\
        .buscar_transacoes("2026-06-01", "2026-06-07")
    assert cap["page_size"] == 150
    assert cap["account_id"] == "acc1"
