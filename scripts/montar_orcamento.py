"""Reconstrói a aba 'Orçamentos' num layout limpo e fácil de perseguir:

    Grupo | Linha | 📊 Realizado <mês ref> (ref.) | 🎯 Meta a perseguir

- Referência = realizado do último mês fechado (lido da aba 'Fatura <mês>').
- Meta começa IGUAL à referência (você corta depois onde quer economizar).
- A coluna '🎯 Meta a perseguir' é a única que você edita — é o que o Telegram cobra.

Uso (local, com as variáveis do Sheets no ambiente):
    python -m scripts.montar_orcamento            # referência = mês anterior
    python -m scripts.montar_orcamento 2026-05    # referência = um mês específico
"""
import os
import sys
import datetime


def _carregar_env(caminho: str = ".env") -> None:
    """Carrega variáveis de um .env local (sem depender de pacote externo)."""
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave = chave.strip()
            valor = valor.strip().strip('"').strip("'")
            os.environ.setdefault(chave, valor)


_carregar_env()

from deploy.sheets_adapter import (criar_leitor_orcamento, criar_escritor_orcamento,  # noqa: E402
                                   criar_leitor_fatura_totais)
from controle_financeiro.dre_fatura import MESES  # noqa: E402


def _mes_anterior(hoje: datetime.date) -> str:
    ano, m = hoje.year, hoje.month - 1
    if m == 0:
        ano, m = ano - 1, 12
    return f"{ano:04d}-{m:02d}"


def _label_ref(mes: str) -> str:
    ano, m = int(mes[:4]), int(mes[5:7])
    return f"📊 Realizado {MESES[m - 1]}/{str(ano)[2:]} (ref.)"


def main(mes_ref: str | None = None) -> None:
    mes_ref = mes_ref or _mes_anterior(datetime.date.today())
    print(f"Referência (último mês) = {mes_ref}", flush=True)

    orc_atual = criar_leitor_orcamento()()            # linhas atuais (grupo/linha)
    ref = criar_leitor_fatura_totais()(mes_ref)        # realizado por classificação
    ref_norm = {(k or "").strip(): abs(v) for k, v in ref.items()}

    if not orc_atual:
        print("⚠️  Não achei linhas na aba 'Orçamentos' atual. Abortei pra não apagar nada.")
        return

    linhas, com_ref = [], 0
    for ln in orc_atual:
        nome = ln["linha"]
        r = round(ref_norm.get(nome, 0))
        if r:
            com_ref += 1
        linhas.append({"grupo": ln.get("grupo"), "linha": nome,
                       "referencia": r, "meta": r})

    n = criar_escritor_orcamento()(linhas, _label_ref(mes_ref))
    print(f"✅ Aba 'Orçamentos' reescrita: {n} linhas "
          f"({com_ref} com referência de {mes_ref}, resto em 0 pra você preencher).",
          flush=True)
    print("Agora é só abrir a aba 'Orçamentos' e ajustar a coluna "
          "'🎯 Meta a perseguir'.", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
