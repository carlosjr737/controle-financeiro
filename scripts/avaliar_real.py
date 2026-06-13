from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.classificador import Classificador
from controle_financeiro.avaliacao import avaliar_acuracia

def main():
    engine = criar_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    importar_historico("dados/DRE da Familia (3).xlsx", s)
    regras = gerar_regras_do_historico(s)
    rel = avaliar_acuracia(s, Classificador(s))
    print(f"Regras geradas: {regras}")
    print(f"Total avaliado: {rel['total']}")
    print(f"Acertos: {rel['acertos']}  Acurácia: {rel['acuracia']:.1%}")
    print(f"Erros (amostra): {rel['erros'][:15]}")

if __name__ == "__main__":
    main()
