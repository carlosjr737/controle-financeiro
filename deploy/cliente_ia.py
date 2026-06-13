"""Cliente LLM para o fallback de classificação.

Em produção usa a API da Anthropic (chave em LLM_API_KEY). Para teste, passe um
`client` falso com .messages.create(...).
"""
import os


def criar_cliente_ia(client=None, model: str = "claude-haiku-4-5-20251001"):
    if client is None:
        import anthropic  # import tardio: só exige a lib em produção
        client = anthropic.Anthropic(api_key=os.environ["LLM_API_KEY"])

    def cliente(prompt: str) -> str:
        msg = client.messages.create(
            model=model, max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        # resposta no formato content[0].text
        try:
            return msg.content[0].text.strip()
        except (AttributeError, IndexError, TypeError):
            return ""

    return cliente
