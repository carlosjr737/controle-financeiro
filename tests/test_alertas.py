# tests/test_alertas.py
from controle_financeiro.alertas import linhas_em_alerta

LINHAS = [
    {"linha": "Supermercado", "pct": 0.53, "status": "verde"},
    {"linha": "Uber", "pct": 0.84, "status": "amarelo"},
    {"linha": "Lazer", "pct": 1.4, "status": "vermelho"},
]

def test_retorna_apenas_amarelo_e_vermelho():
    alertas = linhas_em_alerta(LINHAS)
    nomes = {a["linha"] for a in alertas}
    assert nomes == {"Uber", "Lazer"}

def test_ordena_por_pct_desc():
    alertas = linhas_em_alerta(LINHAS)
    assert alertas[0]["linha"] == "Lazer"  # maior pct primeiro
