# controle_financeiro/sheets/realizado_writer.py
from typing import Callable
from controle_financeiro.fechamento import gerar_linhas_realizado

def escrever_realizado(sessao, mes: str,
                       escritor: Callable[[str, list], int]) -> int:
    """Gera as linhas do realizado e delega a escrita a um `escritor(aba, linhas)`.
    Em produção, o escritor é um adaptador da Google Sheets API que cria/atualiza
    a aba 'Realizado <mes>'. Nos testes é injetado um fake."""
    linhas = gerar_linhas_realizado(sessao, mes)
    return escritor(f"Realizado {mes}", linhas)
