from controle_financeiro.db import criar_engine, criar_sessao, Base
from controle_financeiro.models import Transacao
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.ingestao import ingerir

def test_conta_ignora_entrada_e_pagamento_cartao():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    def transporte(c, b):
        return {"result": {"results": [
            {"id": "g1", "description": "Aluguel/Prestação", "amount": "4146", "date": "2026-07-02",
             "type": "DEBIT"},
            {"id": "s1", "description": "Salário", "amount": "16000", "date": "2026-07-05",
             "type": "CREDIT"},                                   # entrada: ignora
            {"id": "p1", "description": "Pagamento para Banco XP S.A", "amount": "5000",
             "date": "2026-07-10", "type": "DEBIT"},              # pagamento cartão: ignora
            {"id": "p2", "description": "PAGAMENTO de FATURA", "amount": "3000",
             "date": "2026-07-10", "type": "DEBIT"},              # pagamento cartão (pix): ignora
        ]}}
    fonte = BancoMcpFonte(transporte=transporte, account_id="conta1")
    ingerir(s, fonte, Classificador(s), "2026-07-01", "2026-07-31",
            portador="Carlos", tipo="conta", dia_fechamento=6)
    nomes = {t.estabelecimento for t in s.query(Transacao).all()}
    assert nomes == {"Aluguel/Prestação"}      # só a saída de gasto entrou

def test_conta_usa_ciclo_de_fatura():
    e = criar_engine("sqlite://"); Base.metadata.create_all(e); s = criar_sessao(e)
    def transporte(c, b):
        return {"result": {"results": [
            {"id": "g2", "description": "FAXINA", "amount": "1280", "date": "2026-07-10",
             "type": "DEBIT"}]}}
    ingerir(s, BancoMcpFonte(transporte=transporte, account_id="conta1"),
            Classificador(s), "2026-07-01", "2026-07-31", tipo="conta", dia_fechamento=6)
    t = s.query(Transacao).filter_by(id_externo="g2").one()
    assert t.mes_competencia == "2026-08"   # dia 10 > fechamento 6 -> próxima fatura
