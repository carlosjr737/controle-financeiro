"""Reconciliação do cartão com a fatura oficial (híbrido)."""
from controle_financeiro.reconciliacao import reconciliar_cartao


def test_mes_aberto_estima_encargos_pela_ultima_fechada():
    # Junho fechou em 21.379,92; capturamos 17.700 -> encargos 3.679,92.
    # Julho (aberto) capturou 17.043 -> total = 17.043 + 3.679,92.
    faturas = [{"competencia": "2026-06", "total": 21379.92},
               {"competencia": "2026-05", "total": 32005.37}]
    cap = {"2026-07": 17043.53, "2026-06": 17700.0}
    r = reconciliar_cartao("2026-07", cap, faturas)
    assert r["oficial"] is False
    assert r["compras"] == 17043.53
    assert r["encargos"] == round(21379.92 - 17700.0, 2)
    assert r["total"] == round(17043.53 + (21379.92 - 17700.0), 2)
    assert r["comp_ref"] == "2026-06"


def test_mes_fechado_usa_valor_oficial_exato():
    faturas = [{"competencia": "2026-07", "total": 20715.0}]
    cap = {"2026-07": 17043.53}
    r = reconciliar_cartao("2026-07", cap, faturas)
    assert r["oficial"] is True
    assert r["total"] == 20715.0
    assert r["encargos"] == round(20715.0 - 17043.53, 2)


def test_sem_faturas_cai_pro_capturado():
    r = reconciliar_cartao("2026-07", {"2026-07": 100.0}, [])
    assert r == {"total": 100.0, "compras": 100.0,
                 "encargos": 0.0, "oficial": False, "comp_ref": None}


def test_encargos_nao_ficam_negativos():
    # se capturamos MAIS que a fatura de referência, encargos = 0 (não desconta)
    faturas = [{"competencia": "2026-06", "total": 1000.0}]
    cap = {"2026-07": 500.0, "2026-06": 1200.0}
    r = reconciliar_cartao("2026-07", cap, faturas)
    assert r["encargos"] == 0.0
    assert r["total"] == 500.0
