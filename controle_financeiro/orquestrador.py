from controle_financeiro.ingestao import ingerir
from controle_financeiro.telegram.bot import enviar_resumo

def executar_ciclo(sessao, fonte, classificador, mes: str, data: str, enviar,
                   desde: str, ate: str, portador: str | None = None,
                   teto: float | None = None, tipo: str | None = None) -> dict:
    resumo_ingestao = ingerir(sessao, fonte, classificador, desde, ate,
                              portador=portador, tipo=tipo)
    enviar_resumo(sessao, mes, data, enviar=enviar, teto=teto)
    return {"ingestao": resumo_ingestao}
