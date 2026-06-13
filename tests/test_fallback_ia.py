# tests/test_fallback_ia.py
from controle_financeiro.ia.fallback import criar_fallback_ia

def cliente_fake(prompt: str) -> str:
    return "Outros"

def cliente_invalido(prompt: str) -> str:
    return "Categoria Que Nao Existe"

def test_fallback_retorna_categoria_valida():
    fb = criar_fallback_ia(cliente_fake)
    assert fb("LOJA NOVA XYZ", ["Uber", "Outros", "Lazer"]) == "Outros"

def test_fallback_rejeita_categoria_invalida():
    fb = criar_fallback_ia(cliente_invalido)
    assert fb("LOJA NOVA XYZ", ["Uber", "Outros"]) is None
