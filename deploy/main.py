"""Entrypoint do ciclo diário: ingestão (janela rolante) -> classificação ->
resumo no Telegram. O sync do orçamento é não-fatal."""
import os
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.orquestrador import executar_ciclo
from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento
from controle_financeiro.ia.fallback import criar_fallback_ia

from deploy.transporte_banco_mcp import criar_transporte
from deploy.cliente_ia import criar_cliente_ia
from deploy.telegram_envio import criar_enviar
from deploy.sheets_adapter import criar_leitor_orcamento
from deploy.runner import janela_datas


def rodar_ciclo(hoje: datetime.date | None = None) -> dict:
    hoje = hoje or datetime.date.today()
    mes = hoje.strftime("%Y-%m")
    teto = float(os.environ.get("TETO_MENSAL", "27060"))
    portador = os.environ.get("PORTADOR", "Carlos")
    janela_dias = int(os.environ.get("JANELA_DIAS", "7"))
    desde, ate = janela_datas(hoje, janela_dias)

    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)

    # sync do orçamento é não-fatal: se a planilha tiver um problema,
    # ainda assim ingerimos e mandamos o resumo.
    orcamento_aviso = None
    try:
        sincronizar_orcamento(s, mes, criar_leitor_orcamento())
    except Exception as e:  # noqa: BLE001
        orcamento_aviso = f"sync de orçamento falhou: {e}"

    fonte = BancoMcpFonte(transporte=criar_transporte(),
                          account_id=os.environ["XP_ACCOUNT_ID_CARTAO"])
    # IA é opcional: só ativa se LLM_API_KEY estiver definida
    fallback = criar_fallback_ia(criar_cliente_ia()) if os.environ.get("LLM_API_KEY") else None
    classificador = Classificador(s, fallback=fallback)

    resultado = executar_ciclo(
        s, fonte, classificador, mes=mes, data=hoje.isoformat(),
        enviar=criar_enviar(), desde=desde, ate=ate,
        portador=portador, teto=teto, tipo="cartao",
    )
    if orcamento_aviso:
        resultado["orcamento_aviso"] = orcamento_aviso
    return resultado


if __name__ == "__main__":
    print(rodar_ciclo())
