from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/cold_email",
        description="Async SQLAlchemy DSN (psycopg3)",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/cold_email",
        description="Sync DSN used by Alembic",
    )

    # ── LLM selection ─────────────────────────────────────────
    # provider: "anthropic" | "openai" | "ollama"
    llm_provider: str = Field(default="ollama")

    # Anthropic
    anthropic_api_key: str = Field(default="")
    writer_model: str = Field(
        default="claude-sonnet-4-5",
        description="Model used for email drafting and evaluation",
    )
    router_model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="Model used for cheap routing / classification nodes",
    )

    # OpenAI (alternative)
    openai_api_key: str = Field(default="")
    openai_writer_model: str = Field(default="gpt-4o")
    openai_router_model: str = Field(default="gpt-4o-mini")

    # Ollama (alternative, local)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_writer_model: str = Field(default="llama3.1:70b")
    ollama_router_model: str = Field(default="llama3.1:8b")

    # Embeddings (used by semantic memory)
    embeddings_provider: str = Field(default="openai")  # "openai" | "ollama"
    embeddings_model: str = Field(default="text-embedding-3-small")

    # ── External APIs ─────────────────────────────────────────
    proxycurl_api_key: str = Field(default="")
    firecrawl_api_key: str = Field(default="")

    # ── LangSmith tracing ─────────────────────────────────────
    langchain_tracing_v2: bool = Field(default=False)
    langchain_api_key: str = Field(default="")
    langchain_project: str = Field(default="cold-email-workflow")

    # ── Qualification thresholds ──────────────────────────────
    min_company_size: int = Field(default=2)
    max_company_size: int = Field(default=100)
    # comma-separated list of allowed stages (lowercase)
    allowed_stages: str = Field(default="seed,pre_seed,series_a")

    @property
    def allowed_stage_list(self) -> list[str]:
        return [s.strip() for s in self.allowed_stages.split(",")]

    # ── Agent loop safety ─────────────────────────────────────
    max_draft_attempts: int = Field(
        default=3,
        description="Hard cap on draft-evaluate cycles to prevent infinite loops",
    )
    max_tool_retries: int = Field(
        default=4,
        description="Max tenacity retries for Proxycurl / Firecrawl calls",
    )

    # ── User ──────────────────────────────────────────────────
    user_id: str = Field(default="karl", description="Single-user ID")

    # ── Cache TTLs (seconds) ──────────────────────────────────
    proxycurl_cache_ttl: int = Field(default=7 * 24 * 3600)  # 7 days
    firecrawl_cache_ttl: int = Field(default=24 * 3600)  # 24 hours


settings = Settings()
