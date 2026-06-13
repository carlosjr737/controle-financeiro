# Controle Financeiro — núcleo (Planos 1–3)

Sistema de acompanhamento de gastos orçado-vs-real, treinado no histórico do Sheets.

## Como rodar os testes
    cd controle-financeiro
    PYTHONPATH=. python3 -m pytest -v

## Demos
    PYTHONPATH=. python3 scripts/avaliar_real.py    # acurácia do classificador no histórico
    PYTHONPATH=. python3 scripts/ingerir_demo.py    # ingestão (transações simuladas) + dedup + classificação
    PYTHONPATH=. python3 scripts/resumo_demo.py     # resumo diário + loop de aprendizado

## Estado
- Plano 1: motor de classificação (offline) — 95,5% de acurácia no histórico real.
- Plano 2: ingestão (Banco MCP REST, dedup por id_externo) + sync do orçamento (Sheets) + config Postgres.
- Plano 3: comparador orçado-vs-real, alertas, resumo/bot Telegram, aprendizado, fallback de IA.
- Falta (deploy): transporte HTTP real do Banco MCP (plano Plus), adaptador Google Sheets, cliente LLM, token do bot Telegram; e o Plano 4 (agendamento + fechamento).

Tudo testável offline (37 testes). As integrações externas são injetáveis.

## Deploy
Ver `DEPLOY.md` — adaptadores reais já implementados em `deploy/`. Faltam só credenciais e hospedagem.
