# Cold Email Workflow

AI-powered cold email agent built with LangGraph. Give it a company name, it qualifies the target, finds the right contact, scrapes personalization signals, drafts an email, self-evaluates it in a loop, then pauses for your review before sending.

## How it works

```
intake → dedupe_check → qualify_company → find_contact → gather_signals
       → extract_hooks → load_memory → draft_email → evaluate
       → (reflect_on_failure →) human_review → persist_episodic
```

- **intake** — parses free-text or structured input
- **dedupe_check** — skips companies already contacted (fuzzy + exact match)
- **qualify_company** — filters by size (2–100) and stage (seed/pre-seed/series A)
- **find_contact** — locates the right person via Proxycurl
- **gather_signals** — scrapes the company site + blog posts via Firecrawl
- **extract_hooks** — LLM selects the best personalization angles
- **load_memory** — loads your procedural writing rules + semantic profile
- **draft_email** — Sonnet writes the email
- **evaluate** — Haiku scores it against the rubric; loops up to 3× if it fails
- **human_review** — interrupts for your approve / edit / regenerate decision
- **persist_episodic** — saves the episode to Postgres

---

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (Postgres is already running — see below)
- An Anthropic API key (minimum to run; Proxycurl + Firecrawl optional)

---

## Setup

### 1. Install dependencies

```bash
uv sync --extra dev
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```dotenv
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional — leave blank to skip those signals
PROXYCURL_API_KEY=
FIRECRAWL_API_KEY=

# Optional — LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
```

Everything else (DB URL, model names, thresholds) has sensible defaults matching the Docker setup below.

### 3. Start Postgres

```bash
docker compose up -d
```

This starts `pgvector/pgvector:pg16` on port `5432` with:
- user: `postgres`
- password: `postgres`
- database: `cold_email`

### 4. Run migrations

```bash
uv run alembic upgrade head
```

### 5. Seed memory

Seeds the initial procedural writing rules and an empty semantic profile into Postgres:

```bash
uv run python -c "import asyncio; from src.memory.seed import seed_all; asyncio.run(seed_all())"
```

---

## Running the workflow

### LangGraph Studio (recommended)

Start the dev server:

```bash
uv run langgraph dev
```

Then open the Studio URL printed to the terminal (usually `http://localhost:2024`).

Select the `cold_email` graph and submit an input. You can use either mode:

**Explicit input** — structured fields:
```json
{
  "input_mode": "explicit",
  "company_name": "Chimoney",
  "company_domain": "chimoney.io",
  "company_size": 25,
  "company_stage": "seed",
  "user_id": "karl"
}
```

**Natural language input** — free text, LLM extracts the fields:
```json
{
  "input_mode": "natural_language",
  "human_message": "Chimoney, Toronto-based fintech, ~25 employees, seed stage, domain is chimoney.io",
  "user_id": "karl"
}
```

The graph will pause at `human_review`. Resume it with one of:

```json
{ "action": "approve" }
{ "action": "edit", "text": "<your edited email>" }
{ "action": "regenerate", "feedback": "<what to change>" }
```

---

## Running tests

Unit tests only (no DB required):

```bash
uv run pytest -m "not integration"
```

All tests (requires Postgres running):

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

---

## Switching LLM providers

Change `LLM_PROVIDER` in `.env`:

| Value | Writer model | Router model |
|---|---|---|
| `anthropic` (default) | `claude-sonnet-4-5` | `claude-haiku-4-5-20251001` |
| `openai` | `gpt-4o` | `gpt-4o-mini` |
| `ollama` | `llama3.1:70b` | `llama3.1:8b` |

Model names are individually overridable via `WRITER_MODEL` / `ROUTER_MODEL` etc.

---

## Key configuration knobs

| Env var | Default | Effect |
|---|---|---|
| `MAX_DRAFT_ATTEMPTS` | `3` | Max draft-evaluate retries before surfacing to human |
| `MIN_COMPANY_SIZE` / `MAX_COMPANY_SIZE` | `2` / `100` | Qualification size gate |
| `ALLOWED_STAGES` | `seed,pre_seed,series_a` | Comma-separated allowed funding stages |
| `USER_ID` | `karl` | Single-user ID stored on episodes |
