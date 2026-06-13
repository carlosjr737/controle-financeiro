from controle_financeiro.mapeador import mapear_transacao

RAW_CARTAO = {
    "id": "tx_abc123", "description": "DL *UBERRIDES", "merchant": {"name": "Uber"},
    "amount": 27.98, "date": "2026-05-06T00:00:00.000Z", "type": "DEBIT", "status": "POSTED",
    "creditCardMetadata": {"installmentNumber": 3, "totalInstallments": 6, "billId": "b1"},
}
RAW_CONTA = {"id": "tx_999", "description": "PIX RECEBIDO", "amount": 1500.0,
             "date": "2026-05-02", "type": "CREDIT", "status": "POSTED"}

def test_mapeia_campos_cartao():
    d = mapear_transacao(RAW_CARTAO, portador="Carlos")
    assert d["id_externo"] == "tx_abc123"
    assert d["estabelecimento"] == "DL *UBERRIDES"   # usa description (treino das regras)
    assert d["valor"] == 27.98
    assert d["data"] == "2026-05-06"
    assert d["parcela"] == "3 de 6"
    assert d["tipo"] == "cartao"
    assert d["portador"] == "Carlos"
    assert d["mes_competencia"] == "2026-05"

def test_mapeia_conta_sem_parcela():
    d = mapear_transacao(RAW_CONTA)
    assert d["tipo"] == "conta"
    assert d["parcela"] is None
    assert d["portador"] is None
