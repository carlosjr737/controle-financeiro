from typing import Protocol

class FonteTransacoes(Protocol):
    def buscar_transacoes(self, desde: str, ate: str) -> list[dict]:
        ...
