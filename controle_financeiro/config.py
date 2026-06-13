import os
from controle_financeiro.db import criar_engine

def engine_from_env():
    """SQLite local por padrão; em produção defina DATABASE_URL com a string da
    Postgres/Supabase (ex.: postgresql+psycopg://user:pass@host:5432/db)."""
    url = os.environ.get("DATABASE_URL", "sqlite:///controle.db")
    return criar_engine(url)
