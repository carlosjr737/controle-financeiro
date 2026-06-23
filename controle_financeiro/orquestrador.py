from controle_financeiro.ingestao import ingerir
from controle_financeiro.telegram.bot import enviar_resumo

def executar_ciclo(sessao, fonte, classificador, mes: str, data: str, enviar,
                   desde: str, ate: str, portador: str | None = None,
                   teto: float | None = None, tipo: str | None = None,
                   dia_fechamento: int | None = None, contas_extra=None,
                   realizado_externo: dict | None = None) -> dict:
    resumo_ingestao = ingerir(sessao, fonte, classificador, desde, ate,
                              portador=portador, tipo=tipo, dia_fechamento=dia_fechamento)
    extra = {}
    for f, t in (contas_extra or []):
        r = ingerir(sessao, f, classificador, desde, ate,
                    portador=portador, tipo=t, dia_fechamento=dia_fechamento)
        extra[t] = {k: extra.get(t, {}).get(k, 0) + v for k, v in r.items()}
    enviar_resumo(sessao, mes, data, enviar=enviar, teto=teto, realizado_externo=realizado_externo)
    out = {"ingestao": resumo_ingestao}
    if extra:
        out["ingestao_extra"] = extra
    return out
