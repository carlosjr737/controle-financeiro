# Deploy no Vercel — passo a passo

O serviço já está pronto pra Vercel: duas funções serverless em `api/` e o
agendamento em `vercel.json`.

> **Limite do plano grátis (Hobby):** o Vercel Cron roda **1x por dia**. Isso te
> dá acompanhamento **diário** (seu mínimo). Os horários do cron são em **UTC**:
> `0 11 * * *` = 08:00 de Brasília; `0 9 1 * *` (dia 1) = 06:00 BRT.

---

## O que tem na pasta

- `api/cron_diario.py` — função do ciclo diário (ingestão → classificação → resumo no Telegram).
- `api/fechamento.py` — função do fechamento mensal (dia 1; escreve a aba "Realizado").
- `vercel.json` — agenda as duas funções (Vercel Cron) e dá 60s de execução.
- `requirements.txt` — dependências Python (o Vercel instala sozinho).
- `scripts/seed_producao.py` — rode **uma vez, localmente**, pra preparar o banco.

---

## Passo 1 — Subir o código pro GitHub

Crie um repositório no GitHub e suba esta pasta (`git init`, `commit`, `push`).
O Vercel faz deploy a partir do GitHub.

## Passo 2 — Provisionar o Postgres (Supabase)

Crie um projeto grátis no **Supabase** → pegue a **connection string**. Ela vira
a variável `DATABASE_URL` (formato `postgresql+psycopg://...`).

## Passo 3 — Seed (uma vez, no seu computador)

As funções do Vercel **não** importam o histórico — isso é feito uma vez:

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://...supabase..."   # o MESMO de produção
PYTHONPATH=. python3 scripts/seed_producao.py
```

Isso cria as tabelas e gera as regras do classificador a partir do seu histórico.

## Passo 4 — Importar no Vercel

`vercel.com` → **Add New… → Project** → importe o repositório do GitHub.
O Vercel detecta o `requirements.txt` e a pasta `api/` automaticamente. **Não
faça deploy ainda** — primeiro configure as variáveis (Passo 5).

## Passo 5 — ONDE COLAR A CHAVE (variáveis de ambiente) 🔑

No projeto do Vercel: **Settings → Environment Variables**. Adicione cada uma
(uma por linha, Name = Value). É AQUI que entra a chave da API e todos os segredos:

| Name | Value (exemplo) | O que é |
|------|-----------------|---------|
| `DATABASE_URL` | `postgresql+psycopg://...supabase...` | banco Postgres |
| `BANCO_MCP_BASE_URL` | `https://api.mcp.ai` | base da API REST |
| `BANCO_MCP_TOKEN` | *(sua API key do Plus)* | **a chave** — do painel mcp.ai, seção API |
| `XP_ACCOUNT_ID_CARTAO` | `7fcc6f40-693e-4b47-b0cb-05700cd8dd56` | id do cartão (do list_accounts) |
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-...` | token do @BotFather |
| `TELEGRAM_CHAT_ID` | `000000000` | seu chat id |
| `LLM_API_KEY` | `sk-ant-...` | chave do modelo de IA (fallback) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | *(cole o JSON inteiro da conta de serviço)* | credencial do Sheets |
| `SHEET_ID` | `1AbC...` | id da sua planilha |
| `CRON_SECRET` | *(uma senha aleatória longa)* | protege as funções do cron |
| `TETO_MENSAL` | `27060` | teto do orçamento (opcional) |
| `JANELA_DIAS` | `7` | quantos dias buscar a cada run (opcional) |

Notas:
- **`BANCO_MCP_TOKEN`** = a API key que aparece no painel `app.mcp.ai` na seção de
  **API/Developers** (liberada agora que você é Plus). Cole o valor aqui — nunca no código.
- **`GOOGLE_SERVICE_ACCOUNT_JSON`**: no Vercel, cole o **conteúdo do JSON inteiro**
  (o adaptador detecta que é JSON e usa direto — não precisa de arquivo).
- **`CRON_SECRET`**: invente uma senha aleatória. O Vercel envia ela
  automaticamente nas chamadas do cron, e as funções só rodam se ela bater.

Marque as variáveis para **Production** (e Preview, se quiser testar).

## Passo 6 — Deploy

Clique em **Deploy**. O Vercel lê o `vercel.json` e agenda os dois crons.

## Passo 7 — Testar na hora (sem esperar o cron)

Com o `CRON_SECRET` em mãos, chame a função manualmente:

```bash
curl -H "Authorization: Bearer SEU_CRON_SECRET" \
     https://SEU-PROJETO.vercel.app/api/cron_diario
```

Deve responder `{"ok": true, ...}` e você recebe o resumo no Telegram. Se vier
`{"ok": false, "erro": "..."}`, o erro indica o que ajustar (geralmente uma
variável faltando ou o formato da auth REST — veja abaixo).

---

## Confirmação da auth REST do Banco MCP

A API REST usa `Authorization: Bearer <BANCO_MCP_TOKEN>` na base
`https://api.mcp.ai` (endpoints `/v1/openfinance/...`). O adaptador já vem assim.
Se o painel do mcp.ai indicar que o token vai na URL (e não no header), basta
abrir `deploy/transporte_banco_mcp.py` e passar `auth_no_header=True` em
`criar_transporte()` dentro de `deploy/main.py`.

## Limitações e alternativas

- **1 run/dia** no plano grátis. Se quiser 2–3x/dia, o caminho mais simples e
  também grátis é **GitHub Actions** (cron de verdade, sem esse limite) — o mesmo
  código roda lá com pouca adaptação. Posso montar essa versão se um dia quiser.
- Se uma execução passar de 60s (muitos estabelecimentos novos chamando a IA),
  reduza `JANELA_DIAS` ou confirme mais "pendentes" no Telegram (vira regra e
  para de chamar a IA).
