from collections import Counter, defaultdict
from controle_financeiro.models import Transacao, Regra
from controle_financeiro.normalizacao import normalizar_estabelecimento

def gerar_regras_do_historico(sessao) -> int:
    contagem = defaultdict(Counter)
    q = sessao.query(Transacao).filter(Transacao.categoria_id.isnot(None))
    for t in q:
        chave = normalizar_estabelecimento(t.estabelecimento)
        if chave:
            contagem[chave][t.categoria_id] += 1

    existentes = {r.padrao for r in sessao.query(Regra).all()}  # 1 SELECT só
    criadas = 0
    for padrao, cats in contagem.items():
        if padrao in existentes:
            continue
        categoria_id, _ = cats.most_common(1)[0]
        sessao.add(Regra(padrao=padrao, categoria_id=categoria_id,
                         prioridade=100, origem="bootstrap"))
        criadas += 1
    sessao.commit()
    return criadas
