from controle_financeiro.mapeador import mapear_transacao
from controle_financeiro.upsert import upsert_transacao
from controle_financeiro.models import Categoria
from controle_financeiro.regras_negocio import (eh_pagamento_fatura, eh_categoria_pagamento,
                                                eh_pagamento_cartao_conta)

def _garantir_categoria(sessao, nome):
    cat = sessao.query(Categoria).filter_by(nome=nome).one_or_none()
    if cat is None:
        cat = Categoria(nome=nome); sessao.add(cat); sessao.flush()
    return cat

def ingerir(sessao, fonte, classificador, desde: str, ate: str,
            portador: str | None = None, tipo: str | None = None,
            dia_fechamento: int | None = None) -> dict:
    raws = fonte.buscar_transacoes(desde, ate)
    vistos, unicos = set(), []
    for r in raws:
        rid = r.get("id")
        if rid and rid in vistos:
            continue
        if rid:
            vistos.add(rid)
        unicos.append(r)
    raws = unicos
    novas = duplicadas = 0
    for raw in raws:
        # conta corrente: só saídas (débito); ignora entradas e pagamento do cartão
        if tipo == "conta":
            if (raw.get("type") or "").upper() == "CREDIT":
                continue
            if eh_pagamento_cartao_conta(raw.get("description")):
                continue
        dados = mapear_transacao(raw, portador=portador, tipo=tipo,
                                 dia_fechamento=dia_fechamento)
        t, criada = upsert_transacao(sessao, dados)
        if criada:
            novas += 1
        else:
            duplicadas += 1

        # pagamento de fatura: PGTO FATURA, valor negativo, não conta como gasto
        if eh_pagamento_fatura(t.estabelecimento):
            cat = _garantir_categoria(sessao, "PGTO FATURA")
            t.categoria_id = cat.id
            t.valor = -abs(t.valor)
            t.status_classificacao = "pagamento"
            t.confianca = 1.0
            continue

        if not criada:
            continue
        r = classificador.classificar(t.estabelecimento)
        if r.categoria_nome and eh_categoria_pagamento(r.categoria_nome):
            cat = _garantir_categoria(sessao, "PGTO FATURA")
            t.categoria_id = cat.id
            t.valor = -abs(t.valor)
            t.status_classificacao = "pagamento"
            t.confianca = 1.0
        elif r.categoria_nome:
            cat = sessao.query(Categoria).filter_by(nome=r.categoria_nome).one_or_none()
            t.categoria_id = cat.id if cat else None
            t.status_classificacao = "sugerida"
            t.confianca = r.confianca
        else:
            t.status_classificacao = "pendente"
            t.confianca = 0.0
    sessao.commit()
    return {"recebidas": len(raws), "novas": novas, "duplicadas": duplicadas}
