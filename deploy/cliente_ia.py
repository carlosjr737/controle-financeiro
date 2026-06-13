"""Cliente LLM para o fallback de classificação. Resiliente: qualquer erro
(rede, chave inválida, sem crédito) vira "" -> a transação fica 'pendente'."""
import os


def criar_cliente_ia(client=None, model: str = "claude-haiku-4-5-20251001"):
    if client is None:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["LLM_API_KEY"])

    def cliente(prompt: str) -> str:
        try:
            msg = client.messages.create(
                model=model, max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception:  # noqa: BLE001
            return ""

    return cliente


def criar_assistente(client=None, model: str = "claude-haiku-4-5-20251001"):
    """Responde perguntas livres sobre as finanças usando só o contexto dado."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["LLM_API_KEY"])

    def assistente(pergunta: str, contexto: str) -> str:
        prompt = ("Você é um assistente financeiro pessoal. Responda em português do Brasil, "
                  "curto e direto, USANDO SOMENTE os dados abaixo. Se o dado não estiver lá, "
                  "diga que não tem essa informação.\n\n"
                  f"DADOS:\n{contexto}\n\nPERGUNTA: {pergunta}")
        try:
            msg = client.messages.create(model=model, max_tokens=400,
                                         messages=[{"role": "user", "content": prompt}])
            return msg.content[0].text.strip()
        except Exception:  # noqa: BLE001
            return "Não consegui responder agora, tente de novo."
    return assistente
