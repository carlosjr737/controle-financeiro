from controle_financeiro.telegram.botoes import parse_callback, montar_teclado

def test_parse_callback():
    assert parse_callback("ok:42") == ("ok", 42)
    assert parse_callback("set:42:7") == ("set", 42, 7)
    assert parse_callback("lixo")[0] is None

def test_montar_teclado_com_sugestao_e_alternativas():
    tk = montar_teclado(42, "Uber", [(1, "Supermercado"), (2, "Restaurantes"), (3, "Lazer")])
    linhas = tk["inline_keyboard"]
    assert linhas[0][0]["callback_data"] == "ok:42"
    assert "Uber" in linhas[0][0]["text"]
    # alternativas em linhas de 2
    assert linhas[1][0]["callback_data"] == "set:42:1"
    assert linhas[1][1]["callback_data"] == "set:42:2"
    assert linhas[2][0]["callback_data"] == "set:42:3"

def test_montar_teclado_sem_sugestao():
    tk = montar_teclado(9, None, [(1, "Supermercado")])
    assert tk["inline_keyboard"][0][0]["callback_data"] == "set:9:1"
