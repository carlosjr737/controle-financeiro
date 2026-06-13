import gspread
from deploy.sheets_adapter import criar_leitor_orcamento, criar_escritor_realizado

class _WS:
    def __init__(self, values=None):
        self._values = values or []
        self.appended = []
        self.cleared = False
    def get_all_values(self): return self._values
    def clear(self): self.cleared = True
    def append_row(self, row): self.appended.append(row)

class _Planilha:
    def __init__(self, ws): self._ws = ws
    def worksheet(self, aba): return self._ws

def test_leitor_acha_header_apos_resumo_e_formato_br():
    valores = [
        ["Orçamento meta mensal", "", "", "", ""],
        ["Teto máximo de gastos", "27060", "", "", ""],
        ["", "", "", "", ""],
        ["Tipo", "Grupo", "Linha", "Orçamento meta", "Observação"],
        ["Custos fixos", "Transporte", "Uber", "450", "Corte forte"],
        ["Despesas", "Lazer", "Restaurantes", "1.500,00", ""],
        ["", "", "", "", ""],
    ]
    linhas = criar_leitor_orcamento(planilha=_Planilha(_WS(valores)))()
    assert len(linhas) == 2
    assert linhas[0]["linha"] == "Uber" and linhas[0]["orcamento_meta"] == 450.0
    assert linhas[1]["orcamento_meta"] == 1500.0   # formato brasileiro

def test_leitor_sem_header_retorna_vazio():
    linhas = criar_leitor_orcamento(planilha=_Planilha(_WS([["foo","bar"],["1","2"]])))()
    assert linhas == []

def test_leitor_preserva_meta_zero():
    valores = [["Tipo","Grupo","Linha","Orçamento meta"],
               ["Despesas","Lazer","Streamings","0"]]
    linhas = criar_leitor_orcamento(planilha=_Planilha(_WS(valores)))()
    assert linhas[0]["orcamento_meta"] == 0.0

def test_escritor_grava_cabecalho_e_linhas():
    ws = _WS()
    n = criar_escritor_realizado(planilha=_Planilha(ws))("Realizado 2026-06",
        [{"grupo":"Transporte","linha":"Uber","meta":450.0,"realizado":380.0,"diferenca":70.0}])
    assert n == 1 and ws.cleared is True
    assert ws.appended[0] == ["Grupo","Linha","Meta","Realizado","Diferença"]
    assert ws.appended[1] == ["Transporte","Uber",450.0,380.0,70.0]

class _PlanilhaSemAba:
    def __init__(self, ws): self._ws = ws; self.criada = None
    def worksheet(self, aba): raise gspread.WorksheetNotFound(aba)
    def add_worksheet(self, title, rows, cols):
        self.criada = title; return self._ws

def test_escritor_cria_aba_quando_nao_existe():
    ws = _WS(); pl = _PlanilhaSemAba(ws)
    n = criar_escritor_realizado(planilha=pl)("Realizado 2026-07",
        [{"grupo":"G","linha":"L","meta":1.0,"realizado":2.0,"diferenca":-1.0}])
    assert n == 1 and pl.criada == "Realizado 2026-07"
