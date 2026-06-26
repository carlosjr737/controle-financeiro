"""Reconciliação do cartão: mês fechado = oficial; aberto = compras + parcelas projetadas."""
from controle_financeiro.reconciliacao import reconciliar_cartao


def test_mes_aberto_soma_parcelas_projetadas():
    faturas = [{"competencia": "2026-06", "total": 21379.92}]
    cap = {"2026-07": 17043.53}
    r = reconciliar_cartao("2026-07", cap, faturas, projecao_parcelas=4400.0)
    assert r["oficial"] is False
    assert r["compras"] == 17043.53
    assert r["parcelas"] == 4400.0
    assert r["total"] == round(17043.53 + 4400.0, 2)


def test_mes_fechado_usa_valor_oficial_exato():
    faturas = [{"competencia": "2026-07", "total": 20715.0}]
    cap = {"2026-07": 17043.53}
    r = reconciliar_cartao("2026-07", cap, faturas, projecao_parcelas=4400.0)
    assert r["oficial"] is True
    assert r["total"] == 20715.0
    assert r["parcelas"] == round(20715.0 - 17043.53, 2)   # oficial - compras


def test_sem_parcelas_e_sem_fatura():
    r = reconciliar_cartao("2026-07", {"2026-07": 100.0}, [])
    assert r == {"total": 100.0, "compras": 100.0,
                 "parcelas": 0.0, "oficial": False, "comp_ref": None}
