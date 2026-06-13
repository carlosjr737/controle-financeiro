# scripts/fechamento_demo.py
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.models import Categoria, Orcamento, Transacao
from controle_financeiro.fechamento import fechar_mes
from controle_financeiro.sheets.realizado_writer import escrever_realizado

def main():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    importar_historico("dados/DRE da Familia (3).xlsx", s)
    gerar_regras_do_historico(s)

    uber = s.query(Categoria).filter_by(nome="Uber").one()
    s.add(Orcamento(mes="2026-06", grupo="Transporte", linha="Uber", valor_meta=450.0))
    s.add(Transacao(estabelecimento="UBER", valor=380.0, categoria_id=uber.id,
                    mes_competencia="2026-06"))
    s.commit()

    resumo = fechar_mes(s, "2026-06", hoje="2026-07-01")
    print("Fechamento:", {k: resumo[k] for k in
                          ("mes", "meta_total", "realizado_total", "economia_vs_orcado")})

    def escritor(aba, linhas):
        print(f"Escreveria a aba '{aba}' com {len(linhas)} linha(s):")
        for l in linhas:
            print(f"  {l['linha']}: meta {l['meta']} | real {l['realizado']} "
                  f"| dif {l['diferenca']}")
        return len(linhas)

    escrever_realizado(s, "2026-06", escritor)

if __name__ == "__main__":
    main()
