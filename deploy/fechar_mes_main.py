"""Entrypoint de fechamento mensal: roda no dia 1, fecha o mês anterior e
escreve a aba 'Realizado <mes>' no Sheets. Agende com cron (0 6 1 * *)."""
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.fechamento import fechar_mes
from controle_financeiro.sheets.realizado_writer import escrever_realizado
from deploy.sheets_adapter import criar_escritor_realizado


def _mes_anterior(hoje: datetime.date) -> str:
    primeiro = hoje.replace(day=1)
    ultimo_mes_passado = primeiro - datetime.timedelta(days=1)
    return ultimo_mes_passado.strftime("%Y-%m")


def rodar_fechamento(hoje: datetime.date | None = None) -> dict:
    hoje = hoje or datetime.date.today()
    mes = _mes_anterior(hoje)
    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    resumo = fechar_mes(s, mes, hoje=hoje.isoformat())
    escrever_realizado(s, mes, criar_escritor_realizado())
    return resumo


if __name__ == "__main__":
    print(rodar_fechamento())
