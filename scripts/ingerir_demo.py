import json
from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.ingestao import ingerir
from controle_financeiro.models import Transacao, Categoria

def main():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    importar_historico("dados/DRE da Familia (3).xlsx", s)
    gerar_regras_do_historico(s)

    raws = json.load(open("tests/fixtures/transacoes_xp.json"))
    fonte = BancoMcpFonte(transporte=lambda c, b: {"result": {"results": raws}}, account_id="demo")
    resumo = ingerir(s, fonte, Classificador(s), "2026-06-01", "2026-06-30", portador="Carlos")

    print("Resumo:", resumo)
    for t in s.query(Transacao).filter(Transacao.id_externo.isnot(None)).all():
        nome = s.get(Categoria, t.categoria_id).nome if t.categoria_id else "—"
        print(f"  {t.data} {t.estabelecimento[:30]:30} R${t.valor:8.2f} -> {nome} "
              f"({t.status_classificacao}, {t.confianca})")

if __name__ == "__main__":
    main()
