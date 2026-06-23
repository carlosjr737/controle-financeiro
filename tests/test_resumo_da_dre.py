from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Orcamento
from controle_financeiro.comparador import comparar_orcamento
from controle_financeiro.telegram.resumo import montar_resumo_diario

def _sessao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    s.add(Orcamento(mes="2026-07", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Orcamento(mes="2026-07", grupo="Lazer", linha="Lazer", valor_meta=800.0))
    s.commit(); return s

def test_comparar_usa_realizado_externo():
    s = _sessao()
    externo = {"Uber": 380.0, "Lazer": 1000.0, "Supermercado": 200.0}
    linhas = {l["linha"]: l for l in comparar_orcamento(s, "2026-07", realizado_externo=externo)}
    assert linhas["Uber"]["realizado"] == 380.0 and linhas["Uber"]["status"] == "amarelo"
    assert linhas["Lazer"]["status"] == "vermelho"

def test_resumo_total_da_fatura_exclui_pgto():
    s = _sessao()
    externo = {"Uber": 380.0, "Lazer": 1000.0, "Supermercado": 200.0, "PGTO FATURA": -5000.0}
    texto = montar_resumo_diario(s, "2026-07", "2026-07-13", teto=27060.0, realizado_externo=externo)
    # total = 380 + 1000 + 200 (PGTO FATURA negativo é excluído) = 1580
    assert "Já gasto no mês: R$ 1580" in texto
    assert "🔴 Estourou:" in texto and "Lazer" in texto
