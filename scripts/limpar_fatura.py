"""Limpeza única das abas de Fatura (resolve a duplicação cartão manual x OF).

Regras:
- Junho: remove as linhas do SISTEMA (Status 'OF') -> volta pro seu Junho manual.
- Julho: mantém OF (cartão) + Pix fixos (estab == classificação); remove as
  linhas manuais de cartão/parcela (estab != classificação).

SEGURANÇA: por padrão roda em SIMULAÇÃO (não altera nada). Só apaga com --apply.

Uso:
    python -m scripts.limpar_fatura            # simulação (recomendado primeiro)
    python -m scripts.limpar_fatura --apply    # aplica de verdade
"""
import os
import sys
import unicodedata


def _carregar_env(caminho: str = ".env") -> None:
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_carregar_env()

from deploy.sheets_adapter import _abrir_planilha, _parse_num   # noqa: E402


def _norm(s):
    s = (str(s) if s is not None else "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _linha_vazia(row):
    return not any(c is not None and str(c).strip() for c in row)


def _coletar(aba, criterio):
    """Retorna (ws, [(rownum, estab, valor, classif)] que casam o critério)."""
    import gspread
    pl = _abrir_planilha()
    try:
        ws = pl.worksheet(aba)
    except gspread.WorksheetNotFound:
        print(f"  [{aba}] não existe — pulando.")
        return None, []
    valores = ws.get_all_values()
    alvo = []
    for i, row in enumerate(valores[1:], start=2):     # 1-based, pula cabeçalho
        if _linha_vazia(row):
            continue
        estab = row[1] if len(row) > 1 else ""
        valor = _parse_num(row[3]) if len(row) > 3 else None
        classif = row[5] if len(row) > 5 else ""
        status = (row[6].strip() if len(row) > 6 else "")
        if criterio(estab, classif, status):
            alvo.append((i, estab, valor or 0.0, classif))
    return ws, alvo


def _relatorio(titulo, alvo):
    print(f"\n=== {titulo}: {len(alvo)} linhas | R$ {sum(v for _, _, v, _ in alvo):,.2f} ===")
    for _, e, v, c in alvo[:25]:
        print(f"   {str(e)[:30]:<30} R$ {v:>10,.2f} | {c}")
    if len(alvo) > 25:
        print(f"   ...(+{len(alvo) - 25} linhas)")


def _apagar(ws, alvo):
    # exclusão em LOTE: uma única chamada à API (sem travar no limite de escritas).
    # Ordena de baixo pra cima pra os índices não se deslocarem dentro do lote.
    requests = [{
        "deleteDimension": {
            "range": {"sheetId": ws.id, "dimension": "ROWS",
                      "startIndex": rownum - 1, "endIndex": rownum}
        }
    } for rownum, *_ in sorted(alvo, key=lambda x: -x[0])]
    if requests:
        ws.spreadsheet.batch_update({"requests": requests})


def main(apply: bool):
    modo = "APLICANDO" if apply else "SIMULAÇÃO (nada será alterado)"
    print(f"### Limpeza das faturas — {modo} ###")

    # Junho: remover linhas OF (do sistema)
    ws_jun, jun = _coletar("Fatura Jun",
                           lambda e, c, st: st.upper() == "OF")
    _relatorio("Fatura Jun — REMOVER (linhas OF do sistema)", jun)

    # Julho: remover manuais de cartão/parcela (estab != classificação, e não-OF)
    ws_jul, jul = _coletar("Fatura Jul",
                           lambda e, c, st: st.upper() != "OF"
                           and _norm(e) != _norm(c) and _norm(c) != "")
    _relatorio("Fatura Jul — REMOVER (cartão/parcela manual)", jul)

    if not apply:
        print("\n>> Simulação. Reveja a lista acima. Pra aplicar: "
              "python -m scripts.limpar_fatura --apply")
        return
    if ws_jun and jun:
        _apagar(ws_jun, jun)
    if ws_jul and jul:
        _apagar(ws_jul, jul)
    print("\n✅ Limpeza aplicada.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
