"""Entrypoint do ciclo diário: ingestão -> classificação -> resumo no Telegram,
e (melhor esforço) IA nos pendentes + mensagens com botões de confirmação."""
import os
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.orquestrador import executar_ciclo
from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento
from controle_financeiro.ia.fallback import criar_fallback_ia
from controle_financeiro.revisao import (reclassificar_pendentes,
                                         categorias_frequentes, transacoes_para_revisar)
from controle_financeiro.telegram.botoes import montar_teclado

from deploy.transporte_banco_mcp import criar_transporte
from deploy.cliente_ia import criar_cliente_ia
from deploy.telegram_envio import criar_enviar, criar_enviar_botoes
from deploy.sheets_adapter import criar_leitor_orcamento
from deploy.runner import janela_datas


def rodar_ciclo(hoje: datetime.date | None = None) -> dict:
    hoje = hoje or datetime.date.today()
    mes = hoje.strftime("%Y-%m")
    teto = float(os.environ.get("TETO_MENSAL", "27060"))
    portador = os.environ.get("PORTADOR", "Carlos")
    janela_dias = int(os.environ.get("JANELA_DIAS", "7"))
    revisao_max = int(os.environ.get("REVISAO_MAX", "12"))
    desde, ate = janela_datas(hoje, janela_dias)

    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)

    orcamento_aviso = None
    try:
        sincronizar_orcamento(s, mes, criar_leitor_orcamento())
    except Exception as e:  # noqa: BLE001
        orcamento_aviso = f"sync de orçamento falhou: {e}"

    fonte = BancoMcpFonte(transporte=criar_transporte(),
                          account_id=os.environ["XP_ACCOUNT_ID_CARTAO"])
    fallback = criar_fallback_ia(criar_cliente_ia()) if os.environ.get("LLM_API_KEY") else None
    classificador = Classificador(s, fallback=fallback)

    # ingestão + resumo de texto (sempre acontece)
    resultado = executar_ciclo(
        s, fonte, classificador, mes=mes, data=hoje.isoformat(),
        enviar=criar_enviar(), desde=desde, ate=ate,
        portador=portador, teto=teto, tipo="cartao",
    )
    if orcamento_aviso:
        resultado["orcamento_aviso"] = orcamento_aviso

    # IA nos pendentes + botões de confirmação (melhor esforço; já mandamos o resumo)
    try:
        reclassificar_pendentes(s, classificador, mes, limite=revisao_max)
        enviar_botoes = criar_enviar_botoes()
        freq = categorias_frequentes(s)
        itens = transacoes_para_revisar(s, mes, limite=revisao_max)
        for item in itens:
            teclado = montar_teclado(item["id"], item["categoria_nome"], freq)
            enviar_botoes(f'"{item["estabelecimento"]}" R$ {item["valor"]:.0f}', teclado)
        resultado["revisao_enviada"] = len(itens)
    except Exception as e:  # noqa: BLE001
        resultado["revisao_aviso"] = str(e)

    return resultado


if __name__ == "__main__":
    print(rodar_ciclo())
