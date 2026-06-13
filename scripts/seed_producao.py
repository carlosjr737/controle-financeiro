"""Roda UMA VEZ, localmente, com DATABASE_URL apontando p/ o Postgres de produção
(Supabase). Cria as tabelas, importa o histórico e gera as regras do classificador.
Depois disso, as funções do Vercel NÃO importam histórico (só ingerem o novo)."""
import os
from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico

def main():
    assert os.environ.get("DATABASE_URL"), "Defina DATABASE_URL (Postgres de produção)."
    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    importar_historico("dados/DRE da Familia (3).xlsx", s)
    n = gerar_regras_do_historico(s)
    print(f"Seed concluído: {n} regras geradas a partir do histórico.")

if __name__ == "__main__":
    main()
