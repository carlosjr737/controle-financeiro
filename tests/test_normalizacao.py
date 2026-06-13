from controle_financeiro.normalizacao import normalizar_estabelecimento

def test_remove_prefixos_e_padroniza():
    assert normalizar_estabelecimento("DL *UBERRIDES") == "UBERRIDES"
    assert normalizar_estabelecimento("DL          *UBERRIDES") == "UBERRIDES"
    assert normalizar_estabelecimento("MP*MERCADOLIVRE") == "MERCADOLIVRE"
    assert normalizar_estabelecimento("EBN*SPOTIFY") == "SPOTIFY"
    assert normalizar_estabelecimento("  Supermercado E Padaria ") == "SUPERMERCADO E PADARIA"
    assert normalizar_estabelecimento("PARC=103OMEGA AUTO PECAS") == "OMEGA AUTO PECAS"
