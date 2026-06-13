# Guia de Deploy — Controle Financeiro

Este guia leva o sistema-núcleo (já construído e validado contra o XP real) para
rodar sozinho, todo dia, com acompanhamento no Telegram.

O código do núcleo está pronto e testado (43 testes offline). O que falta são
**adaptadores finos** que conectam o núcleo ao mundo real (HTTP do Banco MCP,
Google Sheets, Telegram, IA) + **configuração** (contas, segredos, hospedagem).
Cada adaptador tem um "encaixe" injetável já definido no código.

---

## 1. Visão geral — o que vai rodar

Um pequeno serviço Python roda **2–3x ao dia** (agendado) e, no início do mês,
faz o fechamento. Fluxo de cada execução:

```
[agendador] -> executar_ciclo():
    1. BancoMcpFonte (HTTP REST)  -> busca transações novas do XP
    2. mapeia + deduplica (id_externo) -> grava no Postgres
    3. classifica (regras do histórico + IA pro que sobra)
    4. compara com o orçamento (lido do Google Sheets)
    5. envia o resumo no Telegram (com botões de confirmação)
[no início do mês] -> fechar_mes() + escreve a aba "Realizado <mes>" no Sheets
```

---

## 2. Checklist de contas e credenciais

Marque conforme for obtendo cada um:

- [ ] **Banco MCP — Plano Plus (R$ 29,90/mês).** Necessário para a **API REST**
  (o serviço autônomo precisa dela; o teste grátis e o plano Solo não têm REST).
  No painel `app.mcp.ai` → assine o Plus → pegue a **chave de API / URL pessoal**
  na seção da API. Guarde como segredo.
- [ ] **Remover a conexão XP duplicada.** No painel do Banco MCP você tem 2
  conexões XP iguais — desconecte uma para não arriscar contar gasto em dobro.
  Deixe apenas um `item_id`.
- [ ] **Bot do Telegram.** No app, fale com o **@BotFather** → `/newbot` → guarde o
  **token**. Depois mande uma mensagem qualquer pro seu bot e descubra o seu
  **chat_id** (ex.: via @userinfobot ou o endpoint `getUpdates`).
- [ ] **Chave de um modelo de IA** (para o fallback de classificação dos
  estabelecimentos novos). Ex.: chave da API da Anthropic. Guarde como segredo.
- [ ] **Google Service Account** (para ler o orçamento e escrever a aba
  "Realizado"). No Google Cloud: crie um projeto → ative a **Google Sheets API**
  → crie uma **conta de serviço** → gere uma **chave JSON** → **compartilhe sua
  planilha** com o e-mail da conta de serviço (permissão de edição).
- [ ] **Banco de dados Postgres.** O mais simples é **Supabase** (tem plano
  grátis). Pegue a **connection string** (`DATABASE_URL`).
- [ ] **Hospedagem.** Um lugar barato pra rodar o serviço agendado: Railway,
  Render, Fly.io, uma VM pequena, ou até um Raspberry Pi / seu próprio PC com
  `cron`. Precisa rodar Python e ter acesso à internet.

---

## 3. Variáveis de ambiente (segredos)

Crie um arquivo `.env` (NÃO comite no git) com:

```bash
# Banco / dados
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/postgres

# Banco MCP (Open Finance / XP) — plano Plus
BANCO_MCP_BASE_URL=https://api.mcp.ai          # confirme a base REST no painel
BANCO_MCP_TOKEN=tk_xxxxxxxxxxxxxxxxxxxx         # sua chave/URL pessoal (Plus)
XP_ACCOUNT_ID_CARTAO=7fcc6f40-...              # account_id do cartão (de list_accounts)
XP_ITEM_ID=18ce8778-...                        # a conexão que você manteve

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-...
TELEGRAM_CHAT_ID=000000000

# IA (fallback de classificação)
LLM_API_KEY=sk-ant-...

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_JSON=/caminho/para/credenciais.json
SHEET_ID=1AbC...                               # ID da sua planilha DRE
```

> **Segurança:** o `BANCO_MCP_TOKEN` (a URL `tk_…`) dá leitura aos seus dados
> bancários — trate como senha. Nunca comite o `.env` nem o JSON do Google.

---

## 4. Adaptadores reais (JÁ IMPLEMENTADOS na pasta `deploy/`)

> **Atualização:** estes adaptadores já estão escritos e testados (mocks de rede)
> na pasta `deploy/`. O código abaixo é a referência do que cada um faz. Para
> entrar em produção, você só precisa: (a) instalar as libs, (b) preencher os
> segredos da seção 3, e (c) **confirmar no painel do mcp.ai o formato exato da
> auth REST do plano Plus** (header `Bearer` vs token na URL — o transporte já
> suporta os dois via `auth_no_header`).

### 4.1 Transporte HTTP do Banco MCP

O `BancoMcpFonte` (em `controle_financeiro/fontes/banco_mcp.py`) recebe um
`transporte(caminho, params) -> dict`. Implemente o real:

```python
# deploy/transporte_banco_mcp.py
import os, requests

def criar_transporte():
    base = os.environ["BANCO_MCP_BASE_URL"].rstrip("/")
    token = os.environ["BANCO_MCP_TOKEN"]
    def transporte(caminho: str, params: dict) -> dict:
        # CONFIRME no painel/docs do mcp.ai o formato exato da auth REST do Plus
        # (header Authorization Bearer vs token na URL). Ajuste abaixo se preciso.
        url = f"{base}{caminho}"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    return transporte
```

> **Ajuste do `tipo`:** como consultamos o cartão (conta CREDIT), passe
> `portador` e trate como `tipo="cartao"`. No mapeador, derive o `tipo` do tipo
> da conta consultada (CREDIT→cartao, BANK→conta) em vez de depender de
> `creditCardMetadata` — basta o serviço saber qual `account_id` está lendo.

### 4.2 Cliente de IA (fallback)

O `criar_fallback_ia(cliente)` (em `controle_financeiro/ia/fallback.py`) recebe
`cliente(prompt) -> str`:

```python
# deploy/cliente_ia.py
import os
import anthropic   # pip install anthropic

def criar_cliente_ia():
    client = anthropic.Anthropic(api_key=os.environ["LLM_API_KEY"])
    def cliente(prompt: str) -> str:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    return cliente
```

### 4.3 Bot do Telegram

`enviar_resumo(..., enviar=...)` recebe um `enviar(texto)`. Para o envio simples:

```python
# deploy/telegram_envio.py
import os, requests

def criar_enviar():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    def enviar(texto: str) -> None:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat_id, "text": texto}, timeout=15)
    return enviar
```

> Para os **botões de confirmação** interativos, use a biblioteca
> `python-telegram-bot`: cada botão chama `processar_confirmacao(sessao,
> transacao_id, categoria_nome)`. O envio acima já entrega o resumo diário; os
> botões são um incremento.

### 4.4 Leitor e escritor do Google Sheets

`sincronizar_orcamento(..., leitor=...)` recebe `leitor() -> list[dict]` e
`escrever_realizado(..., escritor=...)` recebe `escritor(aba, linhas) -> int`:

```python
# deploy/sheets_adapter.py
import os, gspread   # pip install gspread google-auth

def _planilha():
    gc = gspread.service_account(filename=os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    return gc.open_by_key(os.environ["SHEET_ID"])

def criar_leitor_orcamento():
    def leitor() -> list[dict]:
        ws = _planilha().worksheet("Orçamentos")
        # ajuste os nomes de coluna conforme sua aba (Tipo, Grupo, Linha, Orçamento meta...)
        linhas = []
        for row in ws.get_all_records():
            linhas.append({
                "tipo": row.get("Tipo"), "grupo": row.get("Grupo"),
                "linha": row.get("Linha"),
                "orcamento_meta": row.get("Orçamento meta"),
                "observacao": row.get("Observação"),
            })
        return linhas
    return leitor

def criar_escritor_realizado():
    def escritor(aba: str, linhas: list) -> int:
        pl = _planilha()
        try:
            ws = pl.worksheet(aba)
            ws.clear()
        except gspread.WorksheetNotFound:
            ws = pl.add_worksheet(title=aba, rows=100, cols=10)
        ws.append_row(["Grupo", "Linha", "Meta", "Realizado", "Diferença"])
        for l in linhas:
            ws.append_row([l["grupo"], l["linha"], l["meta"], l["realizado"], l["diferenca"]])
        return len(linhas)
    return escritor
```

### 4.5 Entrypoint (amarra tudo) + agendamento

```python
# deploy/main.py
import os, datetime
from controle_financeiro.config import engine_from_env
from controle_financeiro.db import criar_sessao, Base
from controle_financeiro.classificador import Classificador
from controle_financeiro.fontes.banco_mcp import BancoMcpFonte
from controle_financeiro.orquestrador import executar_ciclo
from controle_financeiro.sheets.orcamento_sync import sincronizar_orcamento
from controle_financeiro.ia.fallback import criar_fallback_ia

from deploy.transporte_banco_mcp import criar_transporte
from deploy.cliente_ia import criar_cliente_ia
from deploy.telegram_envio import criar_enviar
from deploy.sheets_adapter import criar_leitor_orcamento

def rodar_ciclo():
    engine = engine_from_env(); Base.metadata.create_all(engine)
    s = criar_sessao(engine)
    hoje = datetime.date.today()
    mes = hoje.strftime("%Y-%m")

    # 1) sincroniza o orçamento do Sheets (cria categorias/linhas)
    sincronizar_orcamento(s, mes, criar_leitor_orcamento())

    # 2) monta a fonte e o classificador (com IA de fallback)
    fonte = BancoMcpFonte(transporte=criar_transporte(),
                          account_id=os.environ["XP_ACCOUNT_ID_CARTAO"])
    classificador = Classificador(s, fallback=criar_fallback_ia(criar_cliente_ia()))

    # 3) roda o ciclo: ingestão -> classificação -> resumo no Telegram
    executar_ciclo(s, fonte, classificador, mes=mes, data=hoje.isoformat(),
                   enviar=criar_enviar(), desde=mes + "-01", ate=hoje.isoformat(),
                   portador="Carlos", teto=27060.0)

if __name__ == "__main__":
    rodar_ciclo()
```

Agendamento (exemplo com `cron`, 8h e 20h, horário de São Paulo):

```cron
0 8,20 * * *  cd /app && /usr/bin/python3 -m deploy.main >> /var/log/cf.log 2>&1
```

Fechamento no dia 1 de cada mês (rode `fechar_mes` + `escrever_realizado` do mês
anterior — script análogo usando `deploy/sheets_adapter.criar_escritor_realizado`).

---

## 5. Ordem de subida (passo a passo)

1. **Provisione o Postgres** (Supabase) e coloque a `DATABASE_URL` no `.env`.
2. **Instale as dependências** de deploy:
   `pip install requests gspread google-auth anthropic python-telegram-bot`
3. **Crie o banco e carregue o histórico uma vez** (gera as regras do bootstrap):
   rode um script que chame `importar_historico("dados/DRE da Familia (3).xlsx", s)`
   + `gerar_regras_do_historico(s)` apontando para a `DATABASE_URL` de produção.
4. **Teste cada adaptador isolado** (transporte busca 1 transação; envio manda
   "ok" no Telegram; leitor lê o orçamento; escritor cria uma aba de teste).
5. **Rode `deploy/main.py` manualmente** uma vez e confira o resumo no Telegram.
6. **Smoke test de reconciliação:** ingira um mês e compare os totais por linha
   com a aba "Fatura" correspondente da sua planilha — devem bater.
7. **Ative o `cron`** (2–3x ao dia) e o **fechamento** no dia 1.

---

## 6. Custos mensais (estimados)

- Banco MCP Plus: **R$ 29,90**
- Supabase: **R$ 0** (plano grátis costuma bastar)
- IA (fallback, poucas chamadas/dia): **centavos** (só para estabelecimentos novos)
- Telegram / Google Sheets API: **R$ 0**
- Hospedagem: **R$ 0–30** (free tier de Railway/Render/Fly, ou seu próprio PC)

**Total típico: ~R$ 30/mês.**

---

## 7. Manutenção

- **Consentimento Open Finance expira** (até 12 meses): quando o resumo parar de
  trazer transações, reautorize o XP no painel do Banco MCP.
- **Aprendizado:** quanto mais você confirma os "pendentes" no Telegram, menos a
  IA é acionada e mais barato/rápido fica.
- **Backup:** o Postgres (Supabase) já guarda o histórico; a planilha continua
  como visão consolidada.

---

## 8. O que já está pronto vs. o que falta

**Pronto (testado, 43 testes):** modelo de dados, importação do histórico,
classificador em camadas, ingestão+dedup, comparador orçado-vs-real, alertas,
resumo do Telegram, loop de aprendizado, fechamento mensal, geração da aba
Realizado — tudo com encaixes injetáveis.

**Também pronto:** os adaptadores reais da pasta `deploy/` (transporte HTTP,
cliente de IA, envio no Telegram, leitor/escritor do Sheets, `main.py` e
`fechar_mes_main.py`) — testados com mocks (55 testes no total).

**Falta só (não-código):** preencher as **credenciais da seção 2**, **confirmar a
auth REST do Plus** no painel do mcp.ai, instalar as libs (`pip install requests
gspread google-auth anthropic`) e escolher a **hospedagem**. É configuração, não
desenvolvimento.
