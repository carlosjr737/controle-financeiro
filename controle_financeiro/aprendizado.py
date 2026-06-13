# controle_financeiro/aprendizado.py
from controle_financeiro.models import Transacao, Categoria, Regra
from controle_financeiro.normalizacao import normalizar_estabelecimento

PRIORIDADE_CORRECAO = 200

def registrar_correcao(sessao, transacao_id: int, categoria_nome: str) -> Regra:
    t = sessao.get(Transacao, transacao_id)
    cat = sessao.query(Categoria).filter_by(nome=categoria_nome).one_or_none()
    if cat is None:
        cat = Categoria(nome=categoria_nome); sessao.add(cat); sessao.flush()

    t.categoria_id = cat.id
    t.status_classificacao = "confirmada"
    t.confianca = 1.0

    padrao = normalizar_estabelecimento(t.estabelecimento)
    regra = sessao.query(Regra).filter_by(padrao=padrao, origem="correcao").one_or_none()
    if regra is None:
        regra = Regra(padrao=padrao, categoria_id=cat.id,
                      prioridade=PRIORIDADE_CORRECAO, origem="correcao")
        sessao.add(regra)
    else:
        regra.categoria_id = cat.id
    sessao.commit()
    return regra


def confirmar_sugestao(sessao, transacao_id: int) -> str:
    """Confirma a categoria já sugerida da transação (vira regra)."""
    t = sessao.get(Transacao, transacao_id)
    if t is None:
        return "transação não encontrada"
    cat = sessao.get(Categoria, t.categoria_id) if t.categoria_id else None
    if cat is None:
        return "sem categoria sugerida"
    registrar_correcao(sessao, transacao_id, cat.nome)
    return cat.nome

def corrigir_por_categoria_id(sessao, transacao_id: int, categoria_id: int) -> str:
    """Define a categoria (por id) e cria a regra."""
    cat = sessao.get(Categoria, categoria_id)
    if cat is None:
        return "categoria inválida"
    registrar_correcao(sessao, transacao_id, cat.nome)
    return cat.nome
