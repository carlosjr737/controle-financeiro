from typing import Callable
from controle_financeiro.telegram.resumo import montar_resumo_diario
from controle_financeiro.aprendizado import registrar_correcao

def enviar_resumo(sessao, mes: str, data: str, enviar: Callable[[str], None],
                  teto: float | None = None, realizado_externo: dict | None = None,
                  fatura_cartao: dict | None = None) -> None:
    texto = montar_resumo_diario(sessao, mes, data, teto=teto,
                                 realizado_externo=realizado_externo,
                                 fatura_cartao=fatura_cartao)
    enviar(texto)

def processar_confirmacao(sessao, transacao_id: int, categoria_nome: str):
    return registrar_correcao(sessao, transacao_id, categoria_nome)
