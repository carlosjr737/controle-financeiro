"""Ciclo diário: ingestão -> escreve a aba 'Fatura' (cartão) -> lê os totais da
Fatura aberta (cartão + Pix manuais) -> resumo no Telegram espelhando a DRE."""
import os
import datetime

from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.ingestao import ingerir
from controle_financeiro.telegram.bot import enviar_resumo
from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento, sincronizar_categorias
from controle_financeiro.ia.fallback import criar_fallback_ia
from controle_financeiro.competencia import competencia_fatura, competencia_ciclo
from controle_financeiro.revisao import (reclassificar_pendentes,
                                         categorias_frequentes, transacoes_para_revisar)
from controle_financeiro.telegram.botoes import montar_teclado
from controle_financeiro.dre_fatura import linhas_para_fatura
from controle_financeiro.reconciliacao import reconciliar_cartao
from controle_financeiro.parcelas import projecao_parcelas

from deploy.transporte_banco_mcp import criar_transporte
from deploy.cliente_ia import criar_cliente_ia
from deploy.telegram_envio import criar_enviar, criar_enviar_botoes
from deploy.sheets_adapter import (criar_leitor_orcamento, criar_escritor_fatura,
                                   criar_leitor_descricoes_dre, criar_leitor_fatura_totais)


def _mes_anterior(mes: str) -> str:
    ano = int(mes[:4]); m = int(mes[5:7]) - 1
    if m == 0:
        m = 12; ano -= 1
    return f"{ano:04d}-{m:02d}"


def inicio_ciclo_fatura(mes: str, dia_fechamento: int, margem_dias: int = 0) -> datetime.date:
    """1º dia do ciclo da fatura `mes` (competência): dia seguinte ao fechamento,
    no mês calendário anterior. Ex.: fatura 2026-07, fecha dia 6 -> 2026-06-07.
    `margem_dias` recua mais pra trás (backfill manual, se necessário)."""
    ano, m = int(mes[:4]), int(mes[5:7]) - 1
    if m == 0:
        m = 12; ano -= 1
    inicio = datetime.date(ano, m, min(dia_fechamento + 1, 28))
    return inicio - datetime.timedelta(days=max(margem_dias, 0))


def rodar_ciclo(hoje: datetime.date | None = None) -> dict:
    hoje = hoje or datetime.date.today()
    dia_fechamento = int(os.environ.get("DIA_FECHAMENTO", "7"))
    mes = competencia_ciclo(hoje.isoformat(), dia_fechamento)   # ciclo da fatura aberta
    teto = float(os.environ.get("TETO_MENSAL", "27060"))
    portador = os.environ.get("PORTADOR", "Carlos")
    revisao_max = int(os.environ.get("REVISAO_MAX", "12"))
    page_size = int(os.environ.get("PAGE_SIZE", "500"))
    # janela = do 1º dia do mês ANTERIOR até hoje (cobre o mês corrente + atrasos).
    desde = (hoje.replace(day=1) - datetime.timedelta(days=1)).replace(day=1).isoformat()
    ate = hoje.isoformat()

    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    try:
        resultado = {}

        # 0. realinha competência das transações p/ o ciclo da fatura (idempotente)
        try:
            from controle_financeiro.models import Transacao
            n = 0
            for t in s.query(Transacao).all():
                if t.data and len(t.data) >= 10:
                    alvo = competencia_ciclo(t.data, dia_fechamento)
                    if t.mes_competencia != alvo:
                        t.mes_competencia = alvo; n += 1
            if n:
                s.commit()
            resultado["recompetencia"] = n
        except Exception as e:  # noqa: BLE001
            resultado["recompetencia_aviso"] = str(e)

        # 1. orçamento + vocabulário da DRE
        try:
            sincronizar_orcamento(s, mes, criar_leitor_orcamento())
            sincronizar_categorias(s, criar_leitor_descricoes_dre()() + ["PGTO FATURA"])
        except Exception as e:  # noqa: BLE001
            resultado["orcamento_aviso"] = f"sync falhou: {e}"

        # 2. fontes + classificador
        transporte = criar_transporte()
        fonte = BancoMcpFonte(transporte=transporte,
                              account_id=os.environ["XP_ACCOUNT_ID_CARTAO"], page_size=page_size)
        ids_conta = [x.strip() for x in os.environ.get("XP_ACCOUNT_IDS_CONTA", "").split(",") if x.strip()]
        contas_extra = [(BancoMcpFonte(transporte=transporte, account_id=a, page_size=page_size), "conta")
                        for a in ids_conta]
        fallback = criar_fallback_ia(criar_cliente_ia()) if os.environ.get("LLM_API_KEY") else None
        classificador = Classificador(s, fallback=fallback)

        # 3. ingestão (cartão + contas correntes, se houver)
        resultado["ingestao"] = ingerir(s, fonte, classificador, desde, ate,
                                        portador=portador, tipo="cartao", dia_fechamento=dia_fechamento)
        extra = {}
        for f, t in contas_extra:
            extra[t] = ingerir(s, f, classificador, desde, ate,
                               portador=portador, tipo=t, dia_fechamento=dia_fechamento)
        if extra:
            resultado["ingestao_extra"] = extra

        # 4. escreve a aba 'Fatura' do MÊS ABERTO só (nunca mexe em mês fechado)
        try:
            escritor_fatura = criar_escritor_fatura()
            res_fat = {mes: escritor_fatura(mes, linhas_para_fatura(s, mes))}
            resultado["fatura"] = res_fat
            # diagnóstico: total do CARTÃO da fatura aberta (compare com o app)
            linhas_aberta = linhas_para_fatura(s, mes)
            gastos = [l["valor"] for l in linhas_aberta if l["valor"] > 0]
            resultado["cartao_fatura_aberta"] = {
                "mes": mes, "lancamentos": len(gastos), "total": round(sum(gastos), 2)}
        except Exception as e:  # noqa: BLE001
            resultado["fatura_aviso"] = str(e)

        # 5. lê os totais da Fatura aberta (cartão + Pix manuais) — espelho da DRE
        realizado_externo = None
        try:
            realizado_externo = criar_leitor_fatura_totais()(mes)
        except Exception as e:  # noqa: BLE001
            resultado["totais_aviso"] = str(e)

        # 5b. projeta as parcelas que ainda vão postar nesta fatura (postam ~no
        # fechamento) -> Telegram mostra o total que bate com a fatura do banco.
        fatura_cartao = None
        try:
            faturas = fonte.buscar_faturas(dia_fechamento)
            def _compras(m):
                return sum(l["valor"] for l in linhas_para_fatura(s, m) if l["valor"] > 0)
            cap = {mes: _compras(mes), _mes_anterior(mes): _compras(_mes_anterior(mes))}
            proj = projecao_parcelas(s, mes, _mes_anterior(mes))
            fatura_cartao = reconciliar_cartao(mes, cap, faturas, projecao_parcelas=proj)
            resultado["fatura_cartao"] = fatura_cartao
        except Exception as e:  # noqa: BLE001
            resultado["fatura_cartao_aviso"] = str(e)

        # 6. resumo no Telegram (espelhando a DRE)
        enviar_resumo(s, mes, hoje.isoformat(), enviar=criar_enviar(), teto=teto,
                      realizado_externo=realizado_externo, fatura_cartao=fatura_cartao)

        # 7. IA nos pendentes + botões (melhor esforço)
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

        return resultado
    finally:
        s.close(); engine.dispose()


if __name__ == "__main__":
    print(rodar_ciclo())
