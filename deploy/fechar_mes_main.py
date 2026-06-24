"""Entrypoint de fechamento mensal: roda no dia 1, fecha o mês anterior e
escreve a aba 'Realizado <mes>' no Sheets. Agende com cron (0 6 1 * *)."""
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.fechamento import fechar_mes
from controle_financeiro.sheets.realizado_writer import escrever_realizado
from controle_financeiro.dre_fatura import MESES
from deploy.sheets_adapter import (criar_escritor_realizado, criar_anexar_coluna_mes,
                                   criar_leitor_fatura_totais)


def _mes_anterior(hoje: datetime.date) -> str:
    primeiro = hoje.replace(day=1)
    ultimo_mes_passado = primeiro - datetime.timedelta(days=1)
    return ultimo_mes_passado.strftime("%Y-%m")


def _label_mes(mes: str) -> str:
    ano, m = int(mes[:4]), int(mes[5:7])
    return f"{MESES[m - 1]}/{str(ano)[2:]}"


def rodar_fechamento(hoje: datetime.date | None = None) -> dict:
    hoje = hoje or datetime.date.today()
    mes = _mes_anterior(hoje)
    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    try:
        resumo = fechar_mes(s, mes, hoje=hoje.isoformat())
        escrever_realizado(s, mes, criar_escritor_realizado())
        # adiciona a coluna do mês fechado na aba 'Orçamentos' (histórico p/ perseguir)
        try:
            totais = criar_leitor_fatura_totais()(mes)
            totais = {k: v for k, v in totais.items()
                      if (k or "").strip().upper() != "PGTO FATURA"}
            resumo["orcamento_coluna"] = criar_anexar_coluna_mes()(_label_mes(mes), totais)
        except Exception as e:  # noqa: BLE001
            resumo["orcamento_coluna_aviso"] = str(e)
        return resumo
    finally:
        s.close(); engine.dispose()


if __name__ == "__main__":
    print(rodar_fechamento())
