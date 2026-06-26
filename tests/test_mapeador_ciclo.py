from controle_financeiro.mapeador import mapear_transacao

def test_cartao_usa_mes_do_gasto():
    # 'mês do gasto': a competência é o mês calendário da data, ignorando o fechamento
    raw = {"id": "x", "description": "X", "amount": "10", "date": "2026-06-10T00:00:00Z"}
    d = mapear_transacao(raw, tipo="cartao", dia_fechamento=6)
    assert d["mes_competencia"] == "2026-06"

def test_sem_dia_fechamento_usa_mes_da_data():
    raw = {"id": "y", "description": "Y", "amount": "10", "date": "2026-06-10"}
    assert mapear_transacao(raw, tipo="cartao")["mes_competencia"] == "2026-06"
