"""Alimenta a aba 'Fatura [mês]' (que a DRE soma via SUMIF) sem tocar nas
fórmulas da DRE nem nas linhas manuais. As linhas do sistema levam Status 'OF'
e um id na última coluna, pra deduplicar e atualizar a classificação depois."""
from controle_financeiro.models import Transacao, Categoria

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

def aba_fatura(mes: str) -> str:
    return f"Fatura {MESES[int(mes[5:7]) - 1]}"

def linhas_para_fatura(sessao, mes: str) -> list[dict]:
    q = (sessao.query(Transacao)
         .filter(Transacao.mes_competencia == mes,
                 Transacao.tipo == "cartao",
                 Transacao.status_classificacao != "estorno"))
    linhas = []
    for t in q:
        cat = sessao.get(Categoria, t.categoria_id) if t.categoria_id else None
        linhas.append({
            "id_externo": t.id_externo or f"local-{t.id}",
            "data": t.data or "",
            "estabelecimento": t.estabelecimento,
            "portador": t.portador or "",
            "valor": t.valor,   # com sinal: pagamento sai negativo
            "parcela": t.parcela or "",
            "classificacao": cat.nome if cat else "",
        })
    return linhas

def diff_fatura(linhas_db: list[dict], existentes: dict):
    """existentes: {id_externo: {'row': n, 'classificacao': str}}.
    Retorna (anexar: list[dict], atualizar: list[(row, classificacao)])."""
    anexar, atualizar = [], []
    for ln in linhas_db:
        ex = existentes.get(ln["id_externo"])
        if ex is None:
            anexar.append(ln)
        elif (ex.get("classificacao") or "") != (ln["classificacao"] or ""):
            atualizar.append((ex["row"], ln["classificacao"]))
    return anexar, atualizar
