"""Diagnóstico (SÓ LEITURA) das abas de Fatura: mostra quantas linhas são do
sistema (Status 'OF') vs manuais, e a soma por classificação — pra enxergar
duplicação. Não altera nada.

Uso:
    python -m scripts.diagnostico_fatura                  # Jun e Jul
    python -m scripts.diagnostico_fatura "Fatura Mai" "Fatura Jun"
"""
import os
import sys


def _carregar_env(caminho: str = ".env") -> None:
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


_carregar_env()

from deploy.sheets_adapter import _abrir_planilha, _parse_num  # noqa: E402


def _num(x):
    v = _parse_num(x)
    return v if v is not None else 0.0


def diagnosticar(aba: str) -> None:
    import gspread
    pl = _abrir_planilha()
    try:
        ws = pl.worksheet(aba)
    except gspread.WorksheetNotFound:
        print(f"\n=== {aba}: NÃO EXISTE ===")
        return
    valores = ws.get_all_values()
    if not valores:
        print(f"\n=== {aba}: vazia ===")
        return

    of_linhas, of_total = 0, 0.0
    man_linhas, man_total = 0, 0.0
    por_classif = {}            # classificação -> [soma_of, soma_manual]
    for row in valores[1:]:     # pula cabeçalho
        if not any((c or "").strip() for c in row):
            continue
        valor = _num(row[3] if len(row) > 3 else None)        # col D
        classif = (row[5].strip() if len(row) > 5 else "")    # col F
        status = (row[6].strip() if len(row) > 6 else "")     # col G
        eh_of = status.upper() == "OF"
        slot = por_classif.setdefault(classif or "(sem classif.)", [0.0, 0.0])
        if eh_of:
            of_linhas += 1; of_total += valor; slot[0] += valor
        else:
            man_linhas += 1; man_total += valor; slot[1] += valor

    print(f"\n=== {aba} ===")
    print(f"  Sistema (OF): {of_linhas} linhas  | soma R$ {of_total:,.2f}")
    print(f"  Manuais:      {man_linhas} linhas  | soma R$ {man_total:,.2f}")
    print(f"  TOTAL aba:    R$ {of_total + man_total:,.2f}")
    print("  Por classificação (OF | manual):")
    for c, (o, m) in sorted(por_classif.items(), key=lambda kv: -(kv[1][0] + kv[1][1])):
        flag = "  <-- DUPLICADO?" if o and m else ""
        print(f"    - {c[:28]:<28} OF R$ {o:>9,.2f} | manual R$ {m:>9,.2f}{flag}")


def main(abas):
    if not abas:
        abas = ["Fatura Jun", "Fatura Jul"]
    for aba in abas:
        diagnosticar(aba)


if __name__ == "__main__":
    main(sys.argv[1:])
