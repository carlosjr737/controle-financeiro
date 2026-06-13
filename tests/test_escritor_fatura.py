from deploy.sheets_adapter import criar_escritor_fatura

class _WS:
    def __init__(self, values):
        self._values = values
        self.appended = []
        self.updates = []
    def get_all_values(self): return self._values
    def append_rows(self, rows, value_input_option=None): self.appended.extend(rows)
    def update_cell(self, r, c, v): self.updates.append((r, c, v))

class _Pl:
    def __init__(self, ws): self._ws = ws
    def worksheet(self, aba): return self._ws

def test_anexa_novos_e_atualiza_classificacao():
    # linha 2: já existe id "ja", classificada como "Outros" (Status OF na col G/idx6, id na H/idx7)
    valores = [
        ["Data","Estabelecimento","Portador","Valor","Parcela","Classificação","Status","of_id"],
        ["2026-06-10","ARAMIS","Carlos","970","-","Outros","OF","ja"],
        ["2026-06-01","PIX ALUGUEL","Marcella","4146","1","Aluguel/Prestação","Pix"],  # manual: intacta
    ]
    ws = _WS(valores)
    escritor = criar_escritor_fatura(planilha=_Pl(ws))
    linhas_db = [
        {"id_externo":"ja","data":"2026-06-10","estabelecimento":"ARAMIS","portador":"Carlos",
         "valor":970.0,"parcela":"","classificacao":"Vestuário Carlos"},   # mudou -> atualiza
        {"id_externo":"novo","data":"2026-06-12","estabelecimento":"UBER","portador":"Carlos",
         "valor":20.0,"parcela":"","classificacao":"Uber"},                # novo -> anexa
    ]
    res = escritor("2026-06", linhas_db)
    assert res == {"anexadas": 1, "atualizadas": 1}
    assert ws.appended[0][1] == "UBER" and ws.appended[0][6] == "OF"
    assert ws.updates == [(2, 6, "Vestuário Carlos")]   # linha 2, coluna F
