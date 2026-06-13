"""Roda UMA VEZ, localmente, com DATABASE_URL apontando p/ o Postgres de produção."""
import os
from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.importador import importar_historico
from controle_financeiro.bootstrap import gerar_regras_do_historico

def main():
    assert os.environ.get("DATABASE_URL"), "Defina DATABASE_URL (Postgres de produção)."
    print("1/3 Conectando e criando tabelas...", flush=True)
    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    print("2/3 Importando histórico (pode levar alguns segundos)...", flush=True)
    importar_historico("dados/DRE da Familia (3).xlsx", s)
    print("3/3 Gerando regras...", flush=True)
    n = gerar_regras_do_historico(s)
    print(f"Seed concluído: {n} regras geradas a partir do histórico.", flush=True)

if __name__ == "__main__":
    main()
