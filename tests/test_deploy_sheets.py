from deploy.sheets_adapter import criar_leitor_orcamento, criar_escritor_realizado

class _WS:
    def __init__(self, records=None):
        self._records = records or []
        self.appended = []
        self.cleared = False
    def get_all_records(self): return self._records
    def clear(self): self.cleared = True
    def append_row(self, row): self.appended.append(row)

class _Planilha:
    def __init__(self, ws): self._ws = ws
    def worksheet(self, aba): return self._ws

def test_leitor_orcamento_parseia_linhas():
    ws = _WS([
        {"Tipo": "Custos fixos", "Grupo": "Transporte", "Linha": "Uber",
         "Orçamento meta": 450.0, "Observação": "Corte forte"},
        {"Tipo": "Despesas", "Grupo": "Lazer", "Linha": "", "Orçamento meta": 0},  # ignorada
    ])
    leitor = criar_leitor_orcamento(planilha=_Planilha(ws))
    linhas = leitor()
    assert len(linhas) == 1
    assert linhas[0]["linha"] == "Uber" and linhas[0]["orcamento_meta"] == 450.0

def test_escritor_realizado_grava_cabecalho_e_linhas():
    ws = _WS()
    escritor = criar_escritor_realizado(planilha=_Planilha(ws))
    n = escritor("Realizado 2026-06",
                 [{"grupo": "Transporte", "linha": "Uber", "meta": 450.0,
                   "realizado": 380.0, "diferenca": 70.0}])
    assert n == 1
    assert ws.cleared is True
    assert ws.appended[0] == ["Grupo", "Linha", "Meta", "Realizado", "Diferença"]
    assert ws.appended[1] == ["Transporte", "Uber", 450.0, 380.0, 70.0]


import gspread

def test_leitor_preserva_meta_zero():
    ws = _WS([{"Tipo": "Despesas", "Grupo": "Lazer", "Linha": "Streamings",
               "Orçamento meta": 0, "Observação": "Corte forte"}])
    leitor = criar_leitor_orcamento(planilha=_Planilha(ws))
    linhas = leitor()
    assert linhas[0]["orcamento_meta"] == 0   # não vira None

class _PlanilhaSemAba:
    """Levanta WorksheetNotFound e registra a aba criada."""
    def __init__(self, ws): self._ws = ws; self.criada = None
    def worksheet(self, aba): raise gspread.WorksheetNotFound(aba)
    def add_worksheet(self, title, rows, cols):
        self.criada = title
        return self._ws

def test_escritor_cria_aba_quando_nao_existe():
    ws = _WS()
    pl = _PlanilhaSemAba(ws)
    escritor = criar_escritor_realizado(planilha=pl)
    n = escritor("Realizado 2026-07",
                 [{"grupo": "G", "linha": "L", "meta": 1.0, "realizado": 2.0, "diferenca": -1.0}])
    assert n == 1
    assert pl.criada == "Realizado 2026-07"
    assert ws.appended[0][0] == "Grupo"
