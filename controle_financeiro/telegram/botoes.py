"""Teclado inline do Telegram + parsing de callback_data.
callbacks: 'ok:<txid>', 'set:<txid>:<catid>', 'cat:<txid>:<page>' (abrir lista)."""

def parse_callback(data: str):
    p = (data or "").split(":")
    if len(p) == 2 and p[0] == "ok":
        return ("ok", int(p[1]))
    if len(p) == 3 and p[0] == "set":
        return ("set", int(p[1]), int(p[2]))
    if len(p) == 3 and p[0] == "cat":
        return ("cat", int(p[1]), int(p[2]))
    return (None,)

def montar_teclado(transacao_id: int, categoria_sugerida: str | None,
                   alternativas: list) -> dict:
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
    linhas.append([{"text": "📋 Outra categoria", "callback_data": f"cat:{transacao_id}:0"}])
    return {"inline_keyboard": linhas}

def montar_pagina_categorias(transacao_id: int, categorias: list,
                             page: int, por_pagina: int = 8) -> dict:
    """categorias: list[(id, nome)] ordenada. Lista paginada com navegação."""
    ini = page * por_pagina
    fatia = categorias[ini:ini + por_pagina]
    linhas, linha = [], []
    for cid, nome in fatia:
        linha.append({"text": nome, "callback_data": f"set:{transacao_id}:{cid}"})
        if len(linha) == 2:
            linhas.append(linha); linha = []
    if linha:
        linhas.append(linha)
    nav = []
    if page > 0:
        nav.append({"text": "◀️", "callback_data": f"cat:{transacao_id}:{page-1}"})
    if ini + por_pagina < len(categorias):
        nav.append({"text": "▶️", "callback_data": f"cat:{transacao_id}:{page+1}"})
    if nav:
        linhas.append(nav)
    return {"inline_keyboard": linhas}
