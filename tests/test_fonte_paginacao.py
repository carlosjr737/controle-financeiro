"""A fonte do banco deve puxar TODAS as páginas (fatura grande não trunca)."""
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte


def test_paginacao_segue_cursor_e_para_no_fim():
    paginas = [
        {"result": {"results": [{"id": "1"}, {"id": "2"}], "next_cursor": "c1"}},
        {"result": {"results": [{"id": "3"}, {"id": "4"}], "next_cursor": "c2"}},
        {"result": {"results": [{"id": "5"}]}},   # página incompleta -> última
    ]
    chamadas = []
    def transporte(caminho, body):
        chamadas.append(body.get("cursor"))
        return paginas[len(chamadas) - 1]

    fonte = BancoMcpFonte(transporte=transporte, account_id="acc", page_size=2)
    raws = fonte.buscar_transacoes("2026-05-01", "2026-06-24")
    assert [r["id"] for r in raws] == ["1", "2", "3", "4", "5"]
    assert chamadas == [None, "c1", "c2"]        # seguiu o cursor até acabar


def test_para_sem_cursor():
    def transporte(caminho, body):
        return {"result": {"results": [{"id": "1"}]}}   # sem cursor -> uma página só
    fonte = BancoMcpFonte(transporte=transporte, account_id="acc", page_size=500)
    raws = fonte.buscar_transacoes("2026-06-01", "2026-06-24")
    assert len(raws) == 1


def test_nao_entra_em_loop_se_cursor_repete():
    def transporte(caminho, body):
        return {"result": {"results": [{"id": "x"}] * 2, "next_cursor": "mesmo"}}
    fonte = BancoMcpFonte(transporte=transporte, account_id="acc", page_size=2, max_paginas=20)
    raws = fonte.buscar_transacoes("2026-06-01", "2026-06-24")
    assert len(raws) == 4   # 1ª página + a repetição do cursor para na 2ª
