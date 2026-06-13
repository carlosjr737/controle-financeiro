from controle_financeiro.competencia import competencia_fatura

def test_antes_do_fechamento_fica_no_mes():
    assert competencia_fatura("2026-06-03", 6) == "2026-06"

def test_depois_do_fechamento_vai_pro_proximo():
    assert competencia_fatura("2026-06-10", 6) == "2026-07"

def test_virada_de_ano():
    assert competencia_fatura("2026-12-20", 6) == "2027-01"
