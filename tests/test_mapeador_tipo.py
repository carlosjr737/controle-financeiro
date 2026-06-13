from controle_financeiro.mapeador import mapear_transacao

def test_tipo_explicito_vence_heuristico():
    raw = {"id": "x", "description": "DL*UberRides", "amount": "20.95",
           "date": "2026-06-12T13:40:15Z", "type": "DEBIT", "status": "PENDING"}
    d = mapear_transacao(raw, portador="Carlos", tipo="cartao")
    assert d["tipo"] == "cartao"          # mesmo sem creditCardMetadata
    assert d["valor"] == 20.95            # amount vem como string
    assert d["data"] == "2026-06-12"

def test_sem_tipo_cai_no_heuristico():
    raw = {"id": "y", "description": "PIX", "amount": "10", "date": "2026-06-01"}
    assert mapear_transacao(raw)["tipo"] == "conta"
