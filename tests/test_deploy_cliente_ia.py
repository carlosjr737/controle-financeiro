from deploy.cliente_ia import criar_cliente_ia
from controle_financeiro.ia.fallback import criar_fallback_ia

class _Bloco:
    def __init__(self, text): self.text = text
class _Msg:
    def __init__(self, text): self.content = [_Bloco(text)]
class _Messages:
    def __init__(self, resposta): self._r = resposta
    def create(self, **kwargs): return _Msg(self._r)
class _ClientFake:
    def __init__(self, resposta): self.messages = _Messages(resposta)

def test_cliente_devolve_texto_e_integra_no_fallback():
    cliente = criar_cliente_ia(client=_ClientFake("Outros"))
    fb = criar_fallback_ia(cliente)
    assert fb("LOJA NOVA XYZ", ["Uber", "Outros", "Lazer"]) == "Outros"

def test_fallback_rejeita_resposta_invalida():
    cliente = criar_cliente_ia(client=_ClientFake("Inexistente"))
    fb = criar_fallback_ia(cliente)
    assert fb("LOJA NOVA XYZ", ["Uber", "Outros"]) is None
