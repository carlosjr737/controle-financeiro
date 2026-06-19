from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def criar_engine(url: str = "sqlite:///controle.db"):
    kwargs = {"future": True}
    if url.startswith("postgresql"):
        # serverless: não acumula conexões; cada uso abre e fecha na hora
        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {"prepare_threshold": None}
    return create_engine(url, **kwargs)

def criar_sessao(engine):
    return sessionmaker(bind=engine, future=True)()
