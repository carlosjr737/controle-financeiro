"""Teclado inline do Telegram e parsing de callback_data.
callback_data fica curto (usa ids inteiros internos): 'ok:<txid>' e 'set:<txid>:<catid>'."""

def parse_callback(data: str):
    partes = (data or "").split(":")
    if len(partes) == 2 and partes[0] == "ok":
        return ("ok", int(partes[1]))
    if len(partes) == 3 and partes[0] == "set":
        return ("set", int(partes[1]), int(partes[2]))
    return (None,)

def montar_teclado(transacao_id: int, categoria_sugerida: str | None,
                   alternativas: list) -> dict:
    """alternativas: list[(categoria_id, nome)]. Retorna reply_markup inline."""
    linhas = []
    if categoria_sugerida:
        linhas.append([{"text": f"✔️ {categoria_sugerida}",
                        "callback_data": f"ok:{transacao_id}"}])
    linha = []
    for cid, nome in alternativas:
        linha.append({"text": nome, "callback_data": f"set:{transacao_id}:{cid}"})
        if len(linha) == 2:
            linhas.append(linha); linha = []
    if linha:
        linhas.append(linha)
    return {"inline_keyboard": linhas}
