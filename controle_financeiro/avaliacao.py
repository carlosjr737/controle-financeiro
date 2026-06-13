from controle_financeiro.models import Transacao, Categoria

def avaliar_acuracia(sessao, classificador) -> dict:
    total = acertos = 0
    erros = []
    q = sessao.query(Transacao).filter(Transacao.categoria_id.isnot(None))
    for t in q:
        esperado = sessao.get(Categoria, t.categoria_id).nome
        r = classificador.classificar(t.estabelecimento)
        total += 1
        if r.categoria_nome == esperado:
            acertos += 1
        else:
            erros.append({"estabelecimento": t.estabelecimento,
                          "esperado": esperado, "obtido": r.categoria_nome})
    return {"total": total, "acertos": acertos,
            "acuracia": (acertos / total) if total else 0.0, "erros": erros}
