# tests/test_projecao.py
from controle_financeiro.comparador import projecao_fechamento

def test_projecao_linear():
    # gastou 6000 em 10 dias, mês de 30 dias => projeta 18000
    assert projecao_fechamento(6000.0, 10, 30) == 18000.0

def test_projecao_dia_zero_nao_quebra():
    assert projecao_fechamento(100.0, 0, 30) == 0.0
