from collections import Counter, defaultdict
from controle_financeiro.models import Transacao, Regra
from controle_financeiro.normalizacao import normalizar_estabelecimento

def gerar_regras_do_historico(sessao) -> int:
    # conta categoria por estabelecimento normalizado
    contagem = defaultdict(Counter)
    q = sessao.query(Transacao).filter(Transacao.categoria_id.isnot(None))
    for t in q:
        chave = normalizar_estabelecimento(t.estabelecimento)
        if chave:
            contagem[chave][t.categoria_id] += 1

    criadas = 0
    for padrao, cats in contagem.items():
        categoria_id, _ = cats.most_common(1)[0]
        existe = sessao.query(Regra).filter_by(padrao=padrao).one_or_none()
        if existe is None:
            sessao.add(Regra(padrao=padrao, categoria_id=categoria_id,
                             prioridade=100, origem="bootstrap"))
            criadas += 1
    sessao.commit()
    return criadas
