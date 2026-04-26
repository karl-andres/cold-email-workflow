"""Integration tests for DB connectivity. Skipped if DB is not running."""

import pytest

import src.models  # noqa: F401 — registers all ORM models


@pytest.mark.integration
def test_base_metadata_has_all_tables():
    from src.db import Base
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "episodes",
        "procedural_memory",
        "procedural_memory_history",
        "semantic_profile",
        "proxycurl_cache",
        "firecrawl_cache",
    }
    assert expected.issubset(table_names)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_engine_can_connect():
    """Requires a running Postgres instance."""
    from sqlalchemy import text
    from src.db import engine

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_db_yields_session():
    from src.db import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    gen = get_db()
    session = await gen.__anext__()
    assert isinstance(session, AsyncSession)
    try:
        await gen.aclose()
    except Exception:
        pass
