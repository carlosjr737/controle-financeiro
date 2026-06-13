# scripts/resumo_demo.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.classificador import Classificador
from controle_financeiro.telegram.bot import enviar_resumo, processar_confirmacao

def main():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    importar_historico("dados/DRE da Familia (3).xlsx", s)
    gerar_regras_do_historico(s)

    # orçamento de exemplo + dois gastos do mês
    lazer = s.query(Categoria).filter_by(nome="Lazer").one()
    s.add(Orcamento(mes="2026-06", grupo="Lazer", linha="Lazer", valor_meta=800.0))
    s.add(Transacao(estabelecimento="VIAGEM", valor=1000.0, categoria_id=lazer.id,
                    mes_competencia="2026-06", status_classificacao="sugerida"))
    pend = Transacao(estabelecimento="LOJA NOVA XYZ", valor=200.0,
                     mes_competencia="2026-06", status_classificacao="pendente")
    s.add(pend); s.commit()

    print("=== RESUMO ANTES DA CONFIRMACAO ===")
    enviar_resumo(s, "2026-06", "2026-06-13", enviar=print, teto=27060.0)

    print("\n=== usuário confirma a pendente como 'Outros' ===")
    processar_confirmacao(s, pend.id, "Outros")
    r = Classificador(s).classificar("LOJA NOVA XYZ")
    print(f"Agora o classificador aprende: 'LOJA NOVA XYZ' -> {r.categoria_nome} "
          f"(confianca {r.confianca}, origem {r.origem})")

if __name__ == "__main__":
    main()
