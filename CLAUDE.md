# Cold Email Workflow — Claude Instructions

## Project Overview

AI-powered cold email agent system built with LangGraph. Accepts a company name as input, qualifies it, researches the right contact via Proxycurl, scrapes personalization signals via Firecrawl, drafts an email, self-evaluates it in a loop, then surfaces it for human review before sending.

## Stack

- **Python 3.13** + **uv** (package manager)
- **LangGraph** — agent orchestration, stateful graph, human-in-the-loop via `interrupt()`
- **LangChain** — tool wrappers, LLM abstraction
- **PostgreSQL + pgvector** — single DB for relational + vector data + LangGraph checkpoints
- **SQLAlchemy async** (psycopg3) + **Alembic** for migrations
- **Firecrawl** — website/blog scraping
- **Proxycurl** — LinkedIn company/person/posts data
- **LangSmith** — tracing and eval
- **Streamlit** — v1 UI (CLI also supported via `typer`)

## LLM Model Config

- **Writer/Judge**: `claude-sonnet-4-5` (Anthropic default) — configurable via `LLM_PROVIDER` env var
- **Router/Classifier**: `claude-haiku-4-5-20251001`
- Switchable to OpenAI (`gpt-4o` / `gpt-4o-mini`) or Ollama via `LLM_PROVIDER=openai|ollama`
- Factory in `src/tools/llm_factory.py`

## Project Structure

```
src/
  config.py          # pydantic-settings, all env vars
  state.py           # AgentState TypedDict — the graph's state schema
  db.py              # async SQLAlchemy engine + Base + get_db()
  models.py          # ORM models: Episode, ProceduralMemory, SemanticProfile, caches
  graph.py           # LangGraph graph assembly (Phase 3)
  tools/
    proxycurl.py     # Proxycurl API client (cached + retry)
    firecrawl.py     # Firecrawl SDK wrapper (cached + retry)
    llm_factory.py   # get_writer_llm() / get_router_llm()
  memory/
    procedural.py    # Versioned writing-rules doc (load/save/history)
    episodic.py      # Episode tracking + 3-tier dedup
    semantic.py      # Single profile doc (load/save/append_fact)
    store.py         # MemoryStore facade bundling all three
    seed.py          # Seeds initial procedural doc + empty profile
    seeds/
      procedural_initial.md  # Initial writing rules
  nodes/             # LangGraph node functions (Phase 3)
  eval/
    rubric.py        # EvalRubric TypedDict + judge prompt
  cli/
    run.py           # CLI entry point (typer)
tests/
  conftest.py        # Shared fixtures (base_state, qualified_state, etc.)
  test_models.py
  test_db.py
  tools/             # Unit tests for tool wrappers
  memory/            # Unit tests for memory modules
  nodes/             # Unit tests for graph nodes
migrations/
  versions/0001_initial.py
```

## Key Design Decisions

- **Single profile doc** (not vector collection) for semantic memory in MVP — append facts as bullet lines, full doc injected into prompt
- **Procedural memory** = single versioned markdown doc, self-updates via reflection when user edits a draft
- **Episodic dedup** = 3-tier: exact domain → exact LinkedIn URL → fuzzy name (rapidfuzz token_set_ratio > 90)
- **Max draft attempts** = 3 (hard cap via `settings.max_draft_attempts` — prevents infinite loops)
- **Max tool retries** = 4 (tenacity exponential backoff on 429/503)
- **In-memory cache** for Proxycurl (7 days TTL) and Firecrawl (24h TTL) — module-level dicts

## Qualification Thresholds

- Company size: **2–100 employees**
- Stages: **seed, pre_seed, series_a** (comma-separated in `ALLOWED_STAGES` env var)

## Email Writing Rules (Procedural Memory)

Seeded from `src/memory/seeds/procedural_initial.md`:
1. Open with how you found the company + what specifically impressed you (blog/posts/product)
2. Show 1-2 skills directly relevant to their stack/problem
3. Close with open invitation — never beg
4. **No em dashes** — use regular dashes or restructure
5. Never start with "I'm Karl" or self-introduction first
6. No filler openers ("I hope this email finds you well")
7. Never explicitly ask for an internship — end with possibility
8. Under 180 words
9. Reference something specific from posts/blog/site

## Development Commands

```bash
# Install deps
uv sync --extra dev

# Run DB (requires Docker)
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Run tests (unit only, no DB)
uv run pytest -m "not integration"

# Run all tests (requires DB running)
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

## Environment Setup

```bash
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, PROXYCURL_API_KEY, FIRECRAWL_API_KEY, LANGCHAIN_API_KEY
```

## Testing Rules

- All async tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- DB tests are marked `@pytest.mark.integration` — skipped without a running DB
- Tool tests mock all external calls (no real API calls in tests)
- Memory tests use `AsyncMock` for the SQLAlchemy session
- Target: **80% coverage minimum**

## What Not to Do

- Do not use `asyncio.run()` inside async code — LangGraph handles the event loop
- Do not make real Proxycurl/Firecrawl calls in tests — always mock
- Do not store user data outside the Postgres DB (no flat files for episodes/profile)
- Do not add features beyond the current phase — see phase ordering below
- Do not start sentences with "I" in generated emails (enforced by eval rubric)

## Build Order (Phases)

- **Phase 0** (done): config, state, db, models, migrations, seeds ✓
- **Phase 1** (done): tool wrappers (proxycurl, firecrawl, llm_factory) ✓
- **Phase 2** (done): memory system (procedural, episodic, semantic, store) ✓
- **Phase 3** (next): LangGraph nodes + graph assembly + eval harness
- **Phase 4**: CLI run.py + HITL Streamlit UI
