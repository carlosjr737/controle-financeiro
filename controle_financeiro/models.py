from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from controle_financeiro.db import Base

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    grupo = Column(String)
    tipo = Column(String)  # "Custo Fixo" | "Despesa" | "Receita"

class Regra(Base):
    __tablename__ = "regras"
    id = Column(Integer, primary_key=True)
    padrao = Column(String, nullable=False)            # estabelecimento normalizado
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    prioridade = Column(Integer, default=100)
    origem = Column(String, default="bootstrap")        # "bootstrap" | "correcao"

class Transacao(Base):
    __tablename__ = "transacoes"
    id = Column(Integer, primary_key=True)
    id_externo = Column(String, unique=True)            # nulo no historico
    data = Column(String)                               # ISO date
    estabelecimento = Column(String, nullable=False)
    portador = Column(String)
    valor = Column(Float, nullable=False)
    parcela = Column(String)                            # ex. "3 de 6"
    tipo = Column(String)                               # cartao | pix | debito
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    status_classificacao = Column(String, default="sugerida")
    confianca = Column(Float, default=0.0)
    mes_competencia = Column(String)                    # "YYYY-MM"
    raw_json = Column(Text)

class Orcamento(Base):
    __tablename__ = "orcamento"
    id = Column(Integer, primary_key=True)
    mes = Column(String, nullable=False)            # "YYYY-MM"
    grupo = Column(String)
    linha = Column(String, nullable=False)          # nome da categoria/linha
    valor_meta = Column(Float)
    observacao = Column(String)

class FechamentoMensal(Base):
    __tablename__ = "fechamento_mensal"
    id = Column(Integer, primary_key=True)
    mes = Column(String, unique=True, nullable=False)   # "YYYY-MM"
    status = Column(String, default="aberto")           # aberto | fechado
    data_fechamento = Column(String)
    totais_json = Column(Text)
