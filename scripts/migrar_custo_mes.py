"""Converte as abas de Fatura de 'mês que paga' -> 'mês do gasto'.

Como:
- Linhas do sistema (Status 'OF') = cartão com DATA real -> reencaixadas na aba do
  mês da sua data (ex.: linha de 20/mai que está em 'Fatura Jun' vai pra 'Fatura Mai').
- Linhas manuais: ficam na aba de origem; só SAI a que casa em VALOR com uma linha
  OF da mesma aba (cópia da fatura). Pix/dinheiro/fixos ficam.

SEGURANÇA:
- --backup duplica cada aba como 'BKP <nome>' antes de tudo.
- Sem --apply, roda em SIMULAÇÃO (não altera nada).

Uso:
    python -m scripts.migrar_custo_mes                 # simulação
    python -m scripts.migrar_custo_mes --backup        # só cria os backups
    python -m scripts.migrar_custo_mes --backup --apply  # backup + converte
"""
import os
import sys
import datetime
import unicodedata

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
COLS = 8   # Data, Estab, Portador, Valor, Parcela, Classificação, Status, of_id


def _carregar_env(caminho: str = ".env") -> None:
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_carregar_env()
from deploy.sheets_adapter import _abrir_planilha, _parse_num   # noqa: E402


def _mes_da_data(v):
    """'2026-05-20' / data -> '2026-05'. None se não der."""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m")
    s = str(v or "").strip()[:10]
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    return None


def _aba_do_mes(mes):                       # '2026-05' -> 'Fatura Mai'
    return f"Fatura {MESES[int(mes[5:7]) - 1]}"


def _abas_fatura(pl):
    return [ws for ws in pl.worksheets()
            if ws.title.startswith("Fatura ") and not ws.title.startswith("BKP")]


def backup(pl):
    existentes = {ws.title for ws in pl.worksheets()}
    for ws in _abas_fatura(pl):
        nome = f"BKP {ws.title}"
        if nome in existentes:
            print(f"  backup já existe: {nome}")
            continue
        pl.duplicate_sheet(ws.id, new_sheet_name=nome)
        print(f"  backup criado: {nome}")


def main(apply: bool, fazer_backup: bool):
    print(f"### Conversão p/ 'mês do gasto' — {'APLICANDO' if apply else 'SIMULAÇÃO'} ###")
    pl = _abrir_planilha()

    if fazer_backup:
        print("\n[backup das abas]")
        backup(pl)

    abas = _abas_fatura(pl)
    header = None
    of_por_mes = {}          # mes -> [linhas OF]
    manual_por_aba = {}      # titulo -> [linhas manuais mantidas]
    stats = {}

    for ws in abas:
        valores = ws.get_all_values()
        if not valores:
            continue
        if header is None:
            header = valores[0]
        of_vals = []          # valores das linhas OF desta aba (p/ casar manuais)
        ofs, manuais = [], []
        for row in valores[1:]:
            row = list(row) + [""] * (COLS - len(row))
            if not any(str(c).strip() for c in row):
                continue
            status = str(row[6]).strip().upper()
            if status == "OF":
                ofs.append(row)
                v = _parse_num(row[3])
                if v is not None:
                    of_vals.append(round(v, 2))
            else:
                manuais.append(row)

        # reencaixa OF no mês da data
        sem_data = 0
        for row in ofs:
            mes = _mes_da_data(row[0])
            if mes is None:
                manual_por_aba.setdefault(ws.title, []).append(row); sem_data += 1; continue
            of_por_mes.setdefault(mes, []).append(row)

        # manuais: remove os que casam em valor com OF da MESMA aba (cópia da fatura)
        from collections import Counter
        disp = Counter(of_vals)
        mantidos, removidos = [], 0
        for row in manuais:
            v = _parse_num(row[3])
            vr = round(v, 2) if v is not None else None
            if vr is not None and disp.get(vr, 0) > 0:
                disp[vr] -= 1; removidos += 1            # é cópia do cartão -> sai
            else:
                mantidos.append(row)
        manual_por_aba.setdefault(ws.title, []).extend(mantidos)
        stats[ws.title] = {"of": len(ofs), "of_sem_data": sem_data,
                           "manual": len(manuais), "manual_mantidos": len(mantidos),
                           "manual_removidos": removidos}

    # monta o conteúdo final de cada aba
    print("\n[plano por aba]  (OF reencaixado por data + manuais mantidos)")
    titulos = sorted(set(list(manual_por_aba) + [_aba_do_mes(m) for m in of_por_mes]))
    final = {}
    for titulo in titulos:
        man = manual_por_aba.get(titulo, [])
        # OF cujo mês cai nesta aba
        of_aqui = []
        for mes, linhas in of_por_mes.items():
            if _aba_do_mes(mes) == titulo:
                of_aqui.extend(linhas)
        final[titulo] = man + of_aqui
        soma = sum((_parse_num(r[3]) or 0) for r in final[titulo])
        print(f"  {titulo:<16} -> {len(man):>3} manuais + {len(of_aqui):>3} OF = "
              f"{len(final[titulo]):>3} linhas | R$ {soma:,.2f}")

    print("\n[detalhe da limpeza por aba de origem]")
    for t, s in sorted(stats.items()):
        print(f"  {t:<16} OF={s['of']:>3} (s/data {s['of_sem_data']}) | "
              f"manuais {s['manual']:>3}: mantém {s['manual_mantidos']:>3}, "
              f"remove {s['manual_removidos']:>3}")

    if not apply:
        print("\n>> SIMULAÇÃO. Reveja acima. Pra aplicar (com backup): "
              "python -m scripts.migrar_custo_mes --backup --apply")
        return

    print("\n[gravando]")
    for titulo, linhas in final.items():
        try:
            ws = pl.worksheet(titulo)
        except Exception:  # noqa: BLE001
            ws = pl.add_worksheet(title=titulo, rows=max(len(linhas) + 10, 100), cols=COLS)
        ws.clear()
        dados = [header or ["Data", "Estabelecimento", "Portador", "Valor",
                            "Parcela", "Classificação", "Status", "of_id"]]
        for r in linhas:
            v = _parse_num(r[3])
            dados.append([r[0], r[1], r[2], (v if v is not None else r[3]),
                          r[4], r[5], r[6], r[7] if len(r) > 7 else ""])
        ws.append_rows(dados, value_input_option="USER_ENTERED")
        print(f"  {titulo}: {len(linhas)} linhas")
    print("\n✅ Conversão aplicada. Confira contra as abas 'BKP ...'.")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv, fazer_backup="--backup" in sys.argv)
