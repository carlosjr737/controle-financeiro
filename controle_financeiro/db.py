from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def criar_engine(url: str = "sqlite:///controle.db"):
    return create_engine(url, future=True)

def criar_sessao(engine):
    return sessionmaker(bind=engine, future=True)()
