# controle_financeiro/fechamento.py
import json
from controle_financeiro.comparador import comparar_orcamento
from controle_financeiro.models import FechamentoMensal

def gerar_linhas_realizado(sessao, mes: str) -> list[dict]:
    linhas = []
    for l in comparar_orcamento(sessao, mes):
        linhas.append({
            "grupo": l["grupo"], "linha": l["linha"], "meta": l["meta"],
            "realizado": l["realizado"], "diferenca": round(l["meta"] - l["realizado"], 2),
        })
    return linhas

def fechar_mes(sessao, mes: str, hoje: str | None = None) -> dict:
    linhas = gerar_linhas_realizado(sessao, mes)
    meta_total = round(sum(l["meta"] for l in linhas), 2)
    realizado_total = round(sum(l["realizado"] for l in linhas), 2)
    resumo = {
        "mes": mes,
        "meta_total": meta_total,
        "realizado_total": realizado_total,
        "economia_vs_orcado": round(meta_total - realizado_total, 2),
        "linhas": linhas,
    }
    fech = sessao.query(FechamentoMensal).filter_by(mes=mes).one_or_none()
    if fech is None:
        fech = FechamentoMensal(mes=mes); sessao.add(fech)
    fech.status = "fechado"
    fech.data_fechamento = hoje
    fech.totais_json = json.dumps(resumo)
    sessao.commit()
    return resumo
