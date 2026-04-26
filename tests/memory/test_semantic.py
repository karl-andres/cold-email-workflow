"""Tests for semantic memory (profile doc) module."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_load_profile_returns_empty_when_no_row(mock_db):
    from src.memory.semantic import load_profile

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    result = await load_profile(mock_db, "karl")
    assert result == ""


@pytest.mark.asyncio
async def test_load_profile_returns_doc(mock_db):
    from src.memory.semantic import load_profile

    fake_row = MagicMock()
    fake_row.profile_doc = "Karl is a 2nd year CS student."
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row

    result = await load_profile(mock_db, "karl")
    assert "Karl" in result


@pytest.mark.asyncio
async def test_save_profile_upserts_when_no_existing_row(mock_db):
    from src.memory.semantic import save_profile

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    await save_profile(mock_db, "karl", "New profile text")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_save_profile_updates_existing_row(mock_db):
    from src.memory.semantic import save_profile

    fake_row = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row

    await save_profile(mock_db, "karl", "Updated profile")
    assert fake_row.profile_doc == "Updated profile"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_append_fact_adds_bullet_to_existing_doc(mock_db):
    from src.memory.semantic import append_fact

    fake_row = MagicMock()
    fake_row.profile_doc = "Karl is a 2nd year CS student."
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row

    result = await append_fact(mock_db, "karl", "Built a Rust distributed task queue in 2026.")
    assert "Rust" in result
    assert "Karl is a 2nd year CS student." in result


@pytest.mark.asyncio
async def test_append_fact_creates_doc_when_empty(mock_db):
    from src.memory.semantic import append_fact

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    result = await append_fact(mock_db, "karl", "First fact ever.")
    assert "First fact ever." in result
