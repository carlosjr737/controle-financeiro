"""O resumo soma os encargos no total e mostra o bloco da fatura do cartão."""
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento
from controle_financeiro.telegram.resumo import montar_resumo_diario


def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    s.add(Categoria(nome="Lazer", grupo="Lazer"))
    s.add(Orcamento(mes="2026-07", grupo="Lazer", linha="Lazer", valor_meta=600.0))
    s.commit()
    return s


def test_resumo_aberto_soma_encargos_e_mostra_estimada():
    s = _sessao()
    externo = {"Lazer": 4273.0}                       # Pix/compras na aba Fatura
    fc = {"total": 20715.0, "compras": 17043.0, "encargos": 3672.0,
          "oficial": False, "comp_ref": "2026-06"}
    txt = montar_resumo_diario(s, "2026-07", "2026-06-24",
                               teto=27060.0, realizado_externo=externo, fatura_cartao=fc)
    assert "Já gasto no mês: R$ 7945" in txt          # 4273 + 3672 encargos
    assert "💳 Fatura cartão (estimada): R$ 20715" in txt


def test_resumo_fechado_mostra_oficial():
    s = _sessao()
    fc = {"total": 21380.0, "compras": 17700.0, "encargos": 3680.0,
          "oficial": True, "comp_ref": "2026-07"}
    txt = montar_resumo_diario(s, "2026-07", "2026-07-10",
                               teto=27060.0, realizado_externo={"Lazer": 100.0},
                               fatura_cartao=fc)
    assert "💳 Fatura cartão (oficial do banco): R$ 21380" in txt
