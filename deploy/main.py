"""Ciclo diário: ingestão (competência por ciclo de fatura) -> classificação ->
resumo no Telegram -> IA/botões -> escrita na aba 'Fatura [mês]' (DRE se atualiza)."""
import os
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.orquestrador import executar_ciclo
from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento, sincronizar_categorias
from controle_financeiro.ia.fallback import criar_fallback_ia
from controle_financeiro.competencia import competencia_fatura
from controle_financeiro.revisao import (reclassificar_pendentes,
                                         categorias_frequentes, transacoes_para_revisar)
from controle_financeiro.telegram.botoes import montar_teclado
from controle_financeiro.dre_fatura import linhas_para_fatura

from deploy.transporte_banco_mcp import criar_transporte
from deploy.cliente_ia import criar_cliente_ia
from deploy.telegram_envio import criar_enviar, criar_enviar_botoes
from deploy.sheets_adapter import (criar_leitor_orcamento, criar_escritor_fatura,
                                   criar_leitor_descricoes_dre)
from deploy.runner import janela_datas


def _mes_anterior(mes: str) -> str:
    ano = int(mes[:4]); m = int(mes[5:7]) - 1
    if m == 0:
        m = 12; ano -= 1
    return f"{ano:04d}-{m:02d}"


def rodar_ciclo(hoje: datetime.date | None = None) -> dict:
    hoje = hoje or datetime.date.today()
    dia_fechamento = int(os.environ.get("DIA_FECHAMENTO", "6"))
    mes = competencia_fatura(hoje.isoformat(), dia_fechamento)   # fatura aberta agora
    teto = float(os.environ.get("TETO_MENSAL", "27060"))
    portador = os.environ.get("PORTADOR", "Carlos")
    janela_dias = int(os.environ.get("JANELA_DIAS", "7"))
    revisao_max = int(os.environ.get("REVISAO_MAX", "12"))
    desde, ate = janela_datas(hoje, janela_dias)

    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    try:
        orcamento_aviso = None
        try:
            sincronizar_orcamento(s, mes, criar_leitor_orcamento())
            sincronizar_categorias(s, criar_leitor_descricoes_dre()() + ["PGTO FATURA"])  # vocabulário da DRE + pagamento
        except Exception as e:  # noqa: BLE001
            orcamento_aviso = f"sync de orçamento/categorias falhou: {e}"

        fonte = BancoMcpFonte(transporte=criar_transporte(),
                              account_id=os.environ["XP_ACCOUNT_ID_CARTAO"])
        fallback = criar_fallback_ia(criar_cliente_ia()) if os.environ.get("LLM_API_KEY") else None
        classificador = Classificador(s, fallback=fallback)

        resultado = executar_ciclo(
            s, fonte, classificador, mes=mes, data=hoje.isoformat(),
            enviar=criar_enviar(), desde=desde, ate=ate,
            portador=portador, teto=teto, tipo="cartao", dia_fechamento=dia_fechamento,
        )
        if orcamento_aviso:
            resultado["orcamento_aviso"] = orcamento_aviso

        # IA nos pendentes + botões (melhor esforço)
        try:
            reclassificar_pendentes(s, classificador, mes, limite=revisao_max)
            enviar_botoes = criar_enviar_botoes()
            freq = categorias_frequentes(s)
            itens = transacoes_para_revisar(s, mes, limite=revisao_max)
            for item in itens:
                enviar_botoes(
                    f'{item.get("data","")} · "{item["estabelecimento"]}" R$ {item["valor"]:.0f}',
                    montar_teclado(item["id"], item["categoria_nome"], freq))
            resultado["revisao_enviada"] = len(itens)
        except Exception as e:  # noqa: BLE001
            resultado["revisao_aviso"] = str(e)

        # escreve a aba 'Fatura [mês]' do ciclo atual e do anterior -> DRE se atualiza
        try:
            escritor_fatura = criar_escritor_fatura()
            res_fat = {}
            for m in (mes, _mes_anterior(mes)):
                res_fat[m] = escritor_fatura(m, linhas_para_fatura(s, m))
            resultado["fatura"] = res_fat
        except Exception as e:  # noqa: BLE001
            resultado["fatura_aviso"] = str(e)

        return resultado
    finally:
        s.close(); engine.dispose()


if __name__ == "__main__":
    print(rodar_ciclo())
