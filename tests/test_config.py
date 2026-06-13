import os
from controle_financeiro.config import engine_from_env

def test_usa_sqlite_por_padrao(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    eng = engine_from_env()
    assert eng.url.get_backend_name() == "sqlite"

def test_usa_database_url_quando_definida(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///foo.db")
    eng = engine_from_env()
    assert str(eng.url) == "sqlite:///foo.db"
