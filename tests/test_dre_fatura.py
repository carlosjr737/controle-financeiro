from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.dre_fatura import aba_fatura, linhas_para_fatura, diff_fatura

def test_aba_fatura():
    assert aba_fatura("2026-06") == "Fatura Jun"
    assert aba_fatura("2026-01") == "Fatura Jan"

def test_linhas_para_fatura_so_cartao_classificado():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    uber = Categoria(nome="Uber"); s.add(uber); s.flush()
    s.add(Transacao(id_externo="x1", estabelecimento="DL*Uber", portador="Carlos",
                    valor=20.0, data="2026-06-10", parcela=None, tipo="cartao",
                    categoria_id=uber.id, mes_competencia="2026-06",
                    status_classificacao="sugerida"))
    s.add(Transacao(id_externo="x2", estabelecimento="PIX", valor=50.0, tipo="conta",
                    mes_competencia="2026-06", status_classificacao="sugerida"))  # não-cartão
    s.commit()
    linhas = linhas_para_fatura(s, "2026-06")
    assert len(linhas) == 1
    assert linhas[0]["classificacao"] == "Uber" and linhas[0]["valor"] == 20.0

def test_diff_anexa_novos_e_atualiza_mudados():
    db = [
        {"id_externo": "a", "classificacao": "Uber"},      # novo -> anexar
        {"id_externo": "b", "classificacao": "Restaurantes"},  # existe, mudou -> atualizar
        {"id_externo": "c", "classificacao": "Lazer"},     # existe, igual -> nada
    ]
    existentes = {
        "b": {"row": 5, "classificacao": "Outros"},
        "c": {"row": 6, "classificacao": "Lazer"},
    }
    anexar, atualizar = diff_fatura(db, existentes)
    assert [l["id_externo"] for l in anexar] == ["a"]
    assert atualizar == [(5, "Restaurantes")]
