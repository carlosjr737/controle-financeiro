"""Converte Junho/Julho de 'mês que paga' -> 'mês do gasto' (cost-month).

Para cada aba alvo, a nova versão é:
  - CARTÃO: linhas 'OF' com DATA no mês da aba (de qualquer aba), sem PGTO FATURA
    nem estorno.
  - MANUAL mantido: Pix/fixos (estabelecimento == classificação) + dinheiro
    (estabelecimento começa com número). O resto (cartão colado à mão) vai pro backup.

SEGURANÇA: --backup duplica as abas antes; sem --apply é só SIMULAÇÃO.

Uso:
    python -m scripts.converter_custo_mes
    python -m scripts.converter_custo_mes --backup --apply
"""
import os
import re
import sys
import datetime
import unicodedata

ALVOS = {"2026-06": "Fatura Jun", "2026-07": "Fatura Jul"}
FONTES = ["Fatura Jun", "Fatura Jul"]      # de onde tiramos as linhas OF p/ reencaixar
COLS = 8


def _carregar_env(caminho=".env"):
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_carregar_env()
from deploy.sheets_adapter import _abrir_planilha, _parse_num   # noqa: E402

HEADER = ["Data", "Estabelecimento", "Portador", "Valor", "Parcela",
          "Classificação", "Status", "of_id"]


def _norm(s):
    s = (str(s) if s is not None else "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


DIA_FECHAMENTO = int(os.environ.get("DIA_FECHAMENTO", "7"))


def _mes(v):
    # agrupa pelo CICLO DA FATURA (fecha dia 7), rotulado pelo mês que cobre
    from controle_financeiro.competencia import competencia_ciclo
    if isinstance(v, (datetime.datetime, datetime.date)):
        s = v.strftime("%Y-%m-%d")
    else:
        s = str(v or "")[:10]
    if len(s) < 10 or s[4] != "-":
        return None
    return competencia_ciclo(s, DIA_FECHAMENTO)


def _eh_of(r):
    return str(r[6]).strip().upper() == "OF" if len(r) > 6 else False


def _eh_dinheiro(estab):
    return bool(re.match(r"^\s*\d", str(estab or "")))


def _manter_manual(r):
    classif = r[5] if len(r) > 5 else ""
    estab = r[1] if len(r) > 1 else ""
    return (_norm(estab) == _norm(classif) and _norm(classif)) or _eh_dinheiro(estab)


def _ler(pl, titulo):
    import gspread
    try:
        ws = pl.worksheet(titulo)
    except gspread.WorksheetNotFound:
        return None, []
    out = []
    for row in ws.get_all_values()[1:]:
        row = list(row) + [""] * (COLS - len(row))
        if any(str(c).strip() for c in row):
            out.append(row)
    return ws, out


def main(apply, fazer_backup):
    print(f"### Conversão Jun/Jul p/ 'mês do gasto' — {'APLICANDO' if apply else 'SIMULAÇÃO'} ###")
    pl = _abrir_planilha()

    # coleta linhas das fontes; OF deduplicado por of_id (col H) — a mesma compra
    # pode estar em 2 abas (Jun e Jul) por causa da migração.
    dados = {t: _ler(pl, t) for t in FONTES}
    todas_of = []
    vistos_of = set()
    for _, linhas in dados.values():
        for r in linhas:
            if not _eh_of(r):
                continue
            ofid = str(r[7]).strip() if len(r) > 7 else ""
            chave = ofid or f"{r[0]}|{r[1]}|{r[3]}"     # fallback se não tiver id
            if chave in vistos_of:
                continue
            vistos_of.add(chave)
            todas_of.append(r)

    if fazer_backup:
        print("\n[backup]")
        existentes = {ws.title for ws in pl.worksheets()}
        for t in ALVOS.values():
            ws = dados.get(t, (None, None))[0] or _ler(pl, t)[0]
            if ws and f"BKP {t}" not in existentes:
                pl.duplicate_sheet(ws.id, new_sheet_name=f"BKP {t}")
                print(f"  criado: BKP {t}")
            else:
                print(f"  já existe ou sem aba: BKP {t}")

    novo = {}
    for mes, titulo in ALVOS.items():
        card = [r for r in todas_of if _mes(r[0]) == mes
                and _norm(r[5]) != "pgto fatura" and "estorn" not in _norm(r[5])]
        ws, linhas = dados.get(titulo, (None, []))
        manuais = [r for r in linhas if not _eh_of(r)]
        manter = [r for r in manuais if _manter_manual(r)]
        novo[titulo] = manter + card
        soma = sum((_parse_num(r[3]) or 0) for r in novo[titulo])
        print(f"\n  {titulo}: {len(card)} cartão + {len(manter)} manual "
              f"(de {len(manuais)}) = R$ {soma:,.2f}")

    if not apply:
        print("\n>> SIMULAÇÃO. Pra aplicar com backup: "
              "python -m scripts.converter_custo_mes --backup --apply")
        return

    print("\n[gravando]")
    for titulo, linhas in novo.items():
        ws = pl.worksheet(titulo)
        ws.clear()
        out = [HEADER]
        for r in linhas:
            v = _parse_num(r[3])
            out.append([r[0], r[1], r[2], v if v is not None else r[3],
                        r[4], r[5], r[6], r[7] if len(r) > 7 else ""])
        ws.append_rows(out, value_input_option="USER_ENTERED")
        print(f"  {titulo}: {len(linhas)} linhas")
    print("\n✅ Convertido. Confira contra 'BKP Fatura Jun/Jul'.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv, fazer_backup="--backup" in sys.argv)
