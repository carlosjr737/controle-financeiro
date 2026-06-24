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


def criar_escritor_orcamento(planilha=None, aba: str = "Orçamentos"):
    """(Re)escreve a aba de orçamento num layout limpo e fácil de editar:
        Grupo | Linha | <rótulo de referência> | 🎯 Meta a perseguir
    A coluna de meta é a ÚNICA que o usuário edita; o leitor a reconhece por
    conter 'meta' no título. A referência é só pra orientar (o leitor a ignora)."""
    def escritor(linhas: list, ref_label: str) -> int:
        import gspread
        pl = planilha or _abrir_planilha()
        try:
            ws = pl.worksheet(aba)
            ws.clear()
        except gspread.WorksheetNotFound:
            ws = pl.add_worksheet(title=aba, rows=200, cols=26)
        dados = [["Grupo", "Linha", ref_label, "🎯 Meta a perseguir"]]
        for ln in linhas:
            dados.append([ln.get("grupo") or "", ln["linha"],
                          ln.get("referencia") or 0, ln.get("meta") or 0])
        ws.append_rows(dados, value_input_option="USER_ENTERED")
        return len(linhas)
    return escritor


def criar_anexar_coluna_mes(planilha=None, aba: str = "Orçamentos"):
    """Adiciona (ou atualiza) uma coluna com o realizado de um mês na aba de
    orçamento, casando por 'Linha'. Idempotente: se já houver uma coluna com o
    mesmo rótulo, sobrescreve os valores em vez de criar outra."""
    def anexar(mes_label: str, valores_por_linha: dict) -> int:
        pl = planilha or _abrir_planilha()
        ws = pl.worksheet(aba)
        valores = ws.get_all_values()
        header_idx = next((i for i, r in enumerate(valores)
                           if any(_norm(c) == "linha" for c in r)), None)
        if header_idx is None:
            return 0
        header = valores[header_idx]
        col_linha = next(j for j, c in enumerate(header) if _norm(c) == "linha")
        col_mes = next((j for j, c in enumerate(header)
                        if _norm(c) == _norm(mes_label)), None)
        if col_mes is None:
            col_mes = max(len(r) for r in valores)   # 1ª coluna livre (0-based)
        ws.update_cell(header_idx + 1, col_mes + 1, mes_label)
        n = 0
        for i in range(header_idx + 1, len(valores)):
            linha = valores[i]
            nome = (linha[col_linha].strip() if col_linha < len(linha) else "")
            if not nome or nome not in valores_por_linha:
                continue
            ws.update_cell(i + 1, col_mes + 1, round(abs(valores_por_linha[nome])))
            n += 1
        return n
    return anexar


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


def criar_escritor_fatura(planilha=None):
    """Escreve as transações do cartão na aba 'Fatura [mês]' (que a DRE soma).
    Linhas do sistema levam Status 'OF' + um id na coluna H pra deduplicar e
    atualizar a classificação depois. Não toca nas linhas manuais."""
    from controle_financeiro.dre_fatura import aba_fatura, diff_fatura
    CABECALHO = ["Data", "Estabelecimento", "Portador", "Valor", "Parcela",
                 "Classificação", "Status", "of_id"]

    def escritor(mes: str, linhas_db: list) -> dict:
        import gspread
        pl = planilha or _abrir_planilha()
        try:
            ws = pl.worksheet(aba_fatura(mes))
        except gspread.WorksheetNotFound:
            ws = pl.add_worksheet(title=aba_fatura(mes), rows=2000, cols=10)
            ws.append_row(CABECALHO)

        valores = ws.get_all_values()
        existentes = {}
        for i, row in enumerate(valores):
            if len(row) > 7 and row[6] == "OF":
                existentes[row[7]] = {"row": i + 1,
                                      "classificacao": row[5] if len(row) > 5 else ""}

        anexar, atualizar = diff_fatura(linhas_db, existentes)
        if anexar:
            novas = [[l["data"], l["estabelecimento"], l["portador"], l["valor"],
                      l["parcela"], l["classificacao"], "OF", l["id_externo"]]
                     for l in anexar]
            ws.append_rows(novas, value_input_option="USER_ENTERED")
        for row, classificacao in atualizar:
            ws.update_cell(row, 6, classificacao)   # coluna F = Classificação
        return {"anexadas": len(anexar), "atualizadas": len(atualizar)}
    return escritor


def criar_leitor_descricoes_dre(planilha=None, aba: str = "DRE"):
    """Lê as Descrições (coluna B) das linhas de gasto da DRE — o vocabulário
    exato que as fórmulas SUMIF esperam."""
    def leitor() -> list:
        pl = planilha or _abrir_planilha()
        ws = pl.worksheet(aba)
        nomes = []
        for row in ws.get_all_values()[1:]:           # pula cabeçalho
            desc = (row[1].strip() if len(row) > 1 else "")
            if desc and desc.lower() != "descrição":
                nomes.append(desc)
        # únicos, preservando ordem
        vistos, unicos = set(), []
        for n in nomes:
            if n not in vistos:
                vistos.add(n); unicos.append(n)
        return unicos
    return leitor


def criar_leitor_fatura_totais(planilha=None):
    """Lê a aba 'Fatura [mês]' e soma a coluna Valor (D) por Classificação (F).
    É o mesmo que a DRE faz com SUMIF — inclui cartão + Pix (manuais)."""
    from controle_financeiro.dre_fatura import aba_fatura

    def leitor(mes: str) -> dict:
        import gspread
        pl = planilha or _abrir_planilha()
        try:
            ws = pl.worksheet(aba_fatura(mes))
        except gspread.WorksheetNotFound:
            return {}
        totais = {}
        for row in ws.get_all_values()[1:]:   # pula cabeçalho
            if len(row) < 6:
                continue
            classif = (row[5] or "").strip()
            v = _parse_num(row[3] if len(row) > 3 else None)
            if not classif or v is None:
                continue
            totais[classif] = totais.get(classif, 0.0) + v
        return totais
    return leitor
