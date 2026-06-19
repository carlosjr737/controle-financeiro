from controle_financeiro.telegram.botoes import parse_callback, montar_teclado, montar_pagina_categorias

def test_parse_cat():
    assert parse_callback("cat:7:2") == ("cat", 7, 2)

def test_teclado_tem_botao_outra():
    tk = montar_teclado(9, "Uber", [(1, "Supermercado")])
    textos = [b["callback_data"] for linha in tk["inline_keyboard"] for b in linha]
    assert "cat:9:0" in textos   # botão "Outra categoria"

def test_pagina_categorias_navegacao():
    cats = [(i, f"Cat{i}") for i in range(1, 21)]   # 20 categorias
    tk = montar_pagina_categorias(5, cats, page=1, por_pagina=8)
    datas = [b["callback_data"] for linha in tk["inline_keyboard"] for b in linha]
    assert "set:5:9" in datas               # itens da página 1 (índices 8..15)
    assert "cat:5:0" in datas and "cat:5:2" in datas   # ◀️ e ▶️
