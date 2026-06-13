# controle_financeiro/ia/fallback.py
from typing import Callable, Optional

def criar_fallback_ia(cliente: Callable[[str], str]) -> Callable[[str, list], Optional[str]]:
    """Recebe um cliente LLM `cliente(prompt) -> str`. Em produção o cliente chama
    a API do modelo; nos testes é injetado um fake. O fallback só aceita uma
    resposta que seja EXATAMENTE uma das categorias válidas."""
    def fallback(estabelecimento: str, categorias: list) -> Optional[str]:
        prompt = (
            "Classifique o estabelecimento em UMA das categorias. "
            "Responda só o nome exato da categoria.\n"
            f"Estabelecimento: {estabelecimento}\n"
            f"Categorias: {', '.join(categorias)}"
        )
        resposta = (cliente(prompt) or "").strip()
        return resposta if resposta in categorias else None
    return fallback
