from sqlalchemy import func
from controle_financeiro.models import Transacao, Categoria

def reclassificar_pendentes(sessao, classificador, mes: str, limite: int = 8) -> int:
    """Re-roda o classificador nos pendentes do mês (útil quando a IA é ligada).
    Limitado por execução pra caber no tempo da função serverless."""
    pend = (sessao.query(Transacao)
            .filter(Transacao.mes_competencia == mes,
                    Transacao.status_classificacao == "pendente")
            .order_by(Transacao.id.desc()).limit(limite).all())
    n = 0
    for t in pend:
        r = classificador.classificar(t.estabelecimento)
        if r.categoria_nome:
            cat = sessao.query(Categoria).filter_by(nome=r.categoria_nome).one_or_none()
            t.categoria_id = cat.id if cat else None
            t.status_classificacao = "sugerida"
            t.confianca = r.confianca
            n += 1
    sessao.commit()
    return n

def categorias_frequentes(sessao, n: int = 6) -> list:
    q = (sessao.query(Categoria.id, Categoria.nome)
         .join(Transacao, Transacao.categoria_id == Categoria.id)
         .group_by(Categoria.id, Categoria.nome)
         .order_by(func.count(Transacao.id).desc()).limit(n))
    return [(cid, nome) for cid, nome in q]

def transacoes_para_revisar(sessao, mes: str, limite: int = 12) -> list:
    """Itens que valem revisão: confiança < 1.0 (IA/substring/pendente) e ainda
    não confirmados. As regras de alta confiança (1.0) não aparecem."""
    q = (sessao.query(Transacao)
         .filter(Transacao.mes_competencia == mes,
                 Transacao.status_classificacao.in_(["sugerida", "pendente"]),
                 Transacao.confianca < 1.0)
         .order_by(Transacao.id.desc()).limit(limite))
    itens = []
    for t in q:
        cat = sessao.get(Categoria, t.categoria_id) if t.categoria_id else None
        itens.append({"id": t.id, "estabelecimento": t.estabelecimento,
                      "valor": abs(t.valor), "categoria_nome": cat.nome if cat else None})
    return itens
