from controle_financeiro.mapeador import mapear_transacao

def test_parcela_none_quando_installment_incompleto():
    raw = {"id": "x", "description": "X", "amount": 1.0, "date": "2026-05-01",
           "creditCardMetadata": {"installmentNumber": None, "totalInstallments": 1}}
    assert mapear_transacao(raw)["parcela"] is None

def test_parcela_ok_quando_completo():
    raw = {"id": "y", "description": "Y", "amount": 1.0, "date": "2026-05-01",
           "creditCardMetadata": {"installmentNumber": 2, "totalInstallments": 6}}
    assert mapear_transacao(raw)["parcela"] == "2 de 6"
