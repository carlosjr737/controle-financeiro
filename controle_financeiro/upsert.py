from sqlalchemy.exc import IntegrityError
from controle_financeiro.models import Transacao

_CAMPOS = ("estabelecimento", "valor", "data", "parcela", "tipo",
           "portador", "mes_competencia")

def _atualizar(existente, dados):
    for k in _CAMPOS:
        if k in dados:
            setattr(existente, k, dados[k])

def upsert_transacao(sessao, dados: dict) -> tuple[Transacao, bool]:
    """Insere ou atualiza por id_externo. À prova de corrida: se outra execução
    inserir o mesmo id_externo ao mesmo tempo, recupera e atualiza em vez de quebrar."""
    id_ext = dados.get("id_externo")
    if id_ext:
        existente = sessao.query(Transacao).filter_by(id_externo=id_ext).one_or_none()
        if existente is not None:
            _atualizar(existente, dados); sessao.flush()
            return existente, False

    t = Transacao(id_externo=id_ext, **{k: dados.get(k) for k in _CAMPOS})
    sessao.add(t)
    try:
        with sessao.begin_nested():     # savepoint: se falhar, não aborta a transação toda
            sessao.flush()
        return t, True
    except IntegrityError:
        sessao.expunge(t)
        existente = sessao.query(Transacao).filter_by(id_externo=id_ext).one_or_none()
        if existente is not None:
            _atualizar(existente, dados); sessao.flush()
            return existente, False
        raise
