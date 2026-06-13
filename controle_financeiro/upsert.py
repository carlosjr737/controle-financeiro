from controle_financeiro.models import Transacao

_CAMPOS = ("estabelecimento", "valor", "data", "parcela", "tipo",
           "portador", "mes_competencia")

def upsert_transacao(sessao, dados: dict) -> tuple[Transacao, bool]:
    """Insere ou atualiza por id_externo. Usa flush (não commit): o chamador
    controla a transação e faz um commit único ao final (ver ingestao.ingerir).
    Atenção: quando id_externo é None (ex.: histórico do Plano 1), NÃO há dedup —
    cada chamada insere uma nova linha."""
    id_ext = dados.get("id_externo")
    existente = None
    if id_ext:
        existente = sessao.query(Transacao).filter_by(id_externo=id_ext).one_or_none()
    if existente is None:
        t = Transacao(id_externo=id_ext, **{k: dados.get(k) for k in _CAMPOS})
        sessao.add(t); sessao.flush()
        return t, True
    for k in _CAMPOS:
        if k in dados:
            setattr(existente, k, dados[k])
    sessao.flush()
    return existente, False
