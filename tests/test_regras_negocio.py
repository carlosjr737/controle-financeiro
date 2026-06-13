from controle_financeiro.regras_negocio import eh_estorno, eh_transferencia_interna

def test_eh_estorno():
    assert eh_estorno(-124.55, "Estornado") is True
    assert eh_estorno(124.55, "Estornado") is True       # marcada como estorno
    assert eh_estorno(57.63, "Supermercado") is False

def test_eh_transferencia_interna():
    assert eh_transferencia_interna("XP PREV CERT - 2303447", "Previdencia Antonella") is False
    assert eh_transferencia_interna("Transferencia entre contas", "Transferência") is True
    assert eh_transferencia_interna("SUPER VAREJAO CAR", "Supermercado") is False
