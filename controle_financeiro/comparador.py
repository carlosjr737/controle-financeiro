# controle_financeiro/comparador.py
from controle_financeiro.models import Orcamento, Categoria, Transacao

TOLERANCIA_RS = 1.0   # ignora "estouros" de centavos (arredondamento da meta)

def _status(realizado: float, meta: float) -> str:
    if meta <= 0:
        return "verde"                          # sem meta definida -> não alerta
    if realizado - meta > TOLERANCIA_RS:
        return "vermelho"                        # estourou de fato (> R$1 acima)
    pct = realizado / meta
    if 0.8 <= pct < 0.99:
        return "amarelo"                         # quase: variável chegando perto
    return "verde"                               # dentro/no orçamento (inclui fixos ~100%)

def comparar_orcamento(sessao, mes: str, realizado_externo: dict | None = None) -> list[dict]:
    resultado = []
    for orc in sessao.query(Orcamento).filter_by(mes=mes).all():
        meta = orc.valor_meta or 0.0
        if realizado_externo is not None:
            realizado = abs(realizado_externo.get(orc.linha, 0.0))
        else:
            cat = sessao.query(Categoria).filter_by(nome=orc.linha).one_or_none()
            realizado = 0.0
            if cat:
                q = (sessao.query(Transacao)
                     .filter(Transacao.categoria_id == cat.id,
                             Transacao.mes_competencia == mes,
                             Transacao.status_classificacao != "estorno"))
                realizado = sum(abs(t.valor) for t in q)
        pct = (realizado / meta) if meta else 0.0
        resultado.append({"grupo": orc.grupo, "linha": orc.linha, "meta": meta,
                          "realizado": realizado, "pct": pct,
                          "status": _status(realizado, meta),
                          "observacao": orc.observacao})
    return resultado

def projecao_fechamento(realizado_total: float, dia_atual: int, dias_no_mes: int) -> float:
    if dia_atual <= 0:
        return 0.0
    return realizado_total / dia_atual * dias_no_mes
