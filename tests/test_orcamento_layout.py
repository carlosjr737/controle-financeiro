"""Layout limpo da aba 'Orçamentos': escritor + coluna mensal, e compatibilidade
com o leitor existente (que acha a meta pelo título conter 'meta')."""
from deploy.sheets_adapter import (criar_escritor_orcamento, criar_anexar_coluna_mes,
                                   criar_leitor_orcamento)


class _WS:
    def __init__(self, values=None):
        self._values = [list(r) for r in (values or [])]
        self.cleared = False
    def get_all_values(self): return self._values
    def clear(self): self.cleared = True; self._values = []
    def append_rows(self, rows, value_input_option=None):
        self._values.extend([list(r) for r in rows])
    def update_cell(self, row, col, value):
        while len(self._values) < row:
            self._values.append([])
        linha = self._values[row - 1]
        while len(linha) < col:
            linha.append("")
        linha[col - 1] = value


class _Planilha:
    def __init__(self, ws): self._ws = ws
    def worksheet(self, aba): return self._ws


def test_escritor_layout_limpo_e_leitor_compativel():
    ws = _WS()
    linhas = [
        {"grupo": "Moradia", "linha": "Aluguel/Prestação", "referencia": 4146, "meta": 4146},
        {"grupo": "Lazer", "linha": "Lazer", "referencia": 1250, "meta": 1250},
    ]
    n = criar_escritor_orcamento(planilha=_Planilha(ws))(linhas, "📊 Realizado Mai/26 (ref.)")
    assert n == 2 and ws.cleared is True
    assert ws._values[0] == ["Grupo", "Linha", "📊 Realizado Mai/26 (ref.)", "🎯 Meta a perseguir"]
    assert ws._values[1] == ["Moradia", "Aluguel/Prestação", 4146, 4146]

    # o leitor existente continua entendendo (meta pela coluna que contém 'meta')
    lidas = criar_leitor_orcamento(planilha=_Planilha(ws))()
    assert len(lidas) == 2
    assert lidas[0]["linha"] == "Aluguel/Prestação"
    assert lidas[0]["orcamento_meta"] == 4146.0
    assert lidas[1]["linha"] == "Lazer" and lidas[1]["orcamento_meta"] == 1250.0


def test_anexar_coluna_mes_casa_por_linha():
    valores = [
        ["Grupo", "Linha", "📊 Realizado Mai/26 (ref.)", "🎯 Meta a perseguir"],
        ["Moradia", "Aluguel/Prestação", 4146, 4000],
        ["Lazer", "Lazer", 1250, 800],
    ]
    ws = _WS(valores)
    n = criar_anexar_coluna_mes(planilha=_Planilha(ws))(
        "Jun/26", {"Aluguel/Prestação": 4146.0, "Lazer": -965.0, "Inexistente": 50.0})
    assert n == 2                          # só casou as 2 linhas existentes
    assert ws._values[0][4] == "Jun/26"    # cabeçalho na 5ª coluna
    assert ws._values[1][4] == 4146        # aluguel
    assert ws._values[2][4] == 965         # lazer (abs do negativo)


def test_anexar_coluna_mes_idempotente():
    valores = [
        ["Grupo", "Linha", "🎯 Meta a perseguir", "Jun/26"],
        ["Lazer", "Lazer", 800, 900],
    ]
    ws = _WS(valores)
    criar_anexar_coluna_mes(planilha=_Planilha(ws))("Jun/26", {"Lazer": 700.0})
    assert ws._values[0][3] == "Jun/26"    # não criou coluna nova
    assert ws._values[1][3] == 700         # sobrescreveu o valor
    assert len(ws._values[0]) == 4
