from controle_financeiro.mapeador import mapear_transacao
from controle_financeiro.upsert import upsert_transacao
from controle_financeiro.models import Categoria

def ingerir(sessao, fonte, classificador, desde: str, ate: str,
            portador: str | None = None, tipo: str | None = None,
            dia_fechamento: int | None = None) -> dict:
    raws = fonte.buscar_transacoes(desde, ate)
    novas = duplicadas = 0
    for raw in raws:
        dados = mapear_transacao(raw, portador=portador, tipo=tipo,
                                 dia_fechamento=dia_fechamento)
        t, criada = upsert_transacao(sessao, dados)
        if not criada:
            duplicadas += 1
            continue
        novas += 1
        r = classificador.classificar(t.estabelecimento)
        if r.categoria_nome:
            cat = sessao.query(Categoria).filter_by(nome=r.categoria_nome).one_or_none()
            t.categoria_id = cat.id if cat else None
            t.status_classificacao = "sugerida"
            t.confianca = r.confianca
        else:
            t.status_classificacao = "pendente"
            t.confianca = 0.0
    sessao.commit()
    return {"recebidas": len(raws), "novas": novas, "duplicadas": duplicadas}
