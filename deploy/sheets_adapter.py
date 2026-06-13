"""Adaptadores do Google Sheets. `planilha` injetável p/ teste (objeto gspread)."""
import os
import unicodedata


def _abrir_planilha():
    import json
    import gspread  # import tardio
    cred = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    if cred.strip().startswith("{"):
        gc = gspread.service_account_from_dict(json.loads(cred))
    else:
        gc = gspread.service_account(filename=cred)
    return gc.open_by_key(os.environ["SHEET_ID"])


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _parse_num(s):
    if s is None:
        return None
    t = str(s).strip().replace("R$", "").replace(" ", "").replace("\xa0", "")
    if t in ("", "-"):
        return None
    if "," in t and "." in t:        # 1.234,56 -> 1234.56
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:                    # 1234,56 -> 1234.56
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def criar_leitor_orcamento(planilha=None, aba: str = "Orçamentos"):
    """Lê a aba de orçamento de forma robusta: localiza a linha de cabeçalho
    (a que contém a coluna 'Linha'), ignorando linhas de resumo no topo."""
    def leitor() -> list[dict]:
        pl = planilha or _abrir_planilha()
        ws = pl.worksheet(aba)
        valores = ws.get_all_values()

        header_idx = None
        for i, row in enumerate(valores):
            if any(_norm(c) == "linha" for c in row):
                header_idx = i
                break
        if header_idx is None:
            return []

        idx = {}
        for j, c in enumerate(valores[header_idx]):
            n = _norm(c)
            if n == "tipo":
                idx["tipo"] = j
            elif n == "grupo":
                idx["grupo"] = j
            elif n == "linha":
                idx["linha"] = j
            elif "meta" in n:
                idx.setdefault("orcamento_meta", j)
            elif "observ" in n:
                idx["observacao"] = j

        def cel(row, key):
            j = idx.get(key)
            return row[j] if (j is not None and j < len(row)) else None

        linhas = []
        for row in valores[header_idx + 1:]:
            nome = (cel(row, "linha") or "").strip()
            if not nome:
                continue
            linhas.append({
                "tipo": cel(row, "tipo"),
                "grupo": cel(row, "grupo"),
                "linha": nome,
                "orcamento_meta": _parse_num(cel(row, "orcamento_meta")),
                "observacao": cel(row, "observacao"),
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
