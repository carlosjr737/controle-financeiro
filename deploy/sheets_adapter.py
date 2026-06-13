"""Adaptadores do Google Sheets. `planilha` injetável p/ teste (objeto gspread)."""
import os


def _abrir_planilha():
    import json
    import gspread  # import tardio
    cred = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    # Vercel/serverless: env guarda o JSON inteiro (começa com "{"); local: caminho de arquivo.
    if cred.strip().startswith("{"):
        gc = gspread.service_account_from_dict(json.loads(cred))
    else:
        gc = gspread.service_account(filename=cred)
    return gc.open_by_key(os.environ["SHEET_ID"])


def _pega(row: dict, *chaves):
    """Primeira chave presente na linha (preserva 0/0.0; só pula ausência)."""
    for k in chaves:
        if k in row:
            return row[k]
    return None


def criar_leitor_orcamento(planilha=None, aba: str = "Orçamentos"):
    def leitor() -> list[dict]:
        pl = planilha or _abrir_planilha()
        ws = pl.worksheet(aba)
        linhas = []
        for row in ws.get_all_records():
            linha = _pega(row, "Linha", "linha")
            if not linha:
                continue
            linhas.append({
                "tipo": _pega(row, "Tipo", "tipo"),
                "grupo": _pega(row, "Grupo", "grupo"),
                "linha": linha,
                "orcamento_meta": _pega(row, "Orçamento meta", "orcamento_meta"),
                "observacao": _pega(row, "Observação", "observacao"),
            })
        return linhas
    return leitor


def criar_escritor_realizado(planilha=None):
    def escritor(aba: str, linhas: list) -> int:
        import gspread
        pl = planilha or _abrir_planilha()
        try:
            ws = pl.worksheet(aba)
            ws.clear()
        except gspread.WorksheetNotFound:
            ws = pl.add_worksheet(title=aba, rows=100, cols=10)
        ws.append_row(["Grupo", "Linha", "Meta", "Realizado", "Diferença"])
        for ln in linhas:
            ws.append_row([ln["grupo"], ln["linha"], ln["meta"],
                           ln["realizado"], ln["diferenca"]])
        return len(linhas)
    return escritor
