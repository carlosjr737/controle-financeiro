from typing import Callable
from controle_financeiro.models import Orcamento, Categoria

def _garantir_categoria(sessao, nome: str):
    if nome and not sessao.query(Categoria).filter_by(nome=nome).one_or_none():
        sessao.add(Categoria(nome=nome))

def sincronizar_orcamento(sessao, mes: str, leitor: Callable[[], list[dict]]) -> int:
    linhas = leitor()
    # re-sync: limpa o mês e regrava
    sessao.query(Orcamento).filter_by(mes=mes).delete()
    n = 0
    for ln in linhas:
        nome = (ln.get("linha") or "").strip()
        if not nome:
            continue
        _garantir_categoria(sessao, nome)
        sessao.add(Orcamento(mes=mes, grupo=ln.get("grupo"), linha=nome,
                             valor_meta=ln.get("orcamento_meta"),
                             observacao=ln.get("observacao")))
        n += 1
    sessao.commit()
    return n


def sincronizar_categorias(sessao, nomes: list) -> int:
    """Garante que cada nome (ex.: Descrições da DRE) exista como Categoria."""
    existentes = {c.nome for c in sessao.query(Categoria).all()}
    n = 0
    for nome in nomes:
        nome = (nome or "").strip()
        if nome and nome not in existentes:
            sessao.add(Categoria(nome=nome)); existentes.add(nome); n += 1
    sessao.commit()
    return n
