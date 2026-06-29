"""Competência pelo ciclo da fatura (fecha dia 7), rotulado pelo mês que cobre."""
from controle_financeiro.competencia import competencia_ciclo


def test_ciclo_fecha_dia_7():
    # a fatura aberta (08/jun a 07/jul) é rotulada JUNHO
    assert competencia_ciclo("2026-06-10", 7) == "2026-06"   # dentro do ciclo aberto
    assert competencia_ciclo("2026-07-03", 7) == "2026-06"   # antes do fechamento 07/jul
    assert competencia_ciclo("2026-07-07", 7) == "2026-06"   # dia do fechamento
    assert competencia_ciclo("2026-07-08", 7) == "2026-07"   # novo ciclo
    assert competencia_ciclo("2026-06-05", 7) == "2026-05"   # caiu na fatura anterior


def test_ciclo_vira_o_ano():
    assert competencia_ciclo("2026-01-03", 7) == "2025-12"
    assert competencia_ciclo("2026-01-10", 7) == "2026-01"
