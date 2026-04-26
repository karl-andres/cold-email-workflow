"""Tests for procedural memory module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, call


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_load_returns_empty_when_no_row(mock_db):
    from src.memory.procedural import load_procedural_doc

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    result = await load_procedural_doc(mock_db, "karl")
    assert result == ""


@pytest.mark.asyncio
async def test_load_returns_current_doc(mock_db):
    from src.memory.procedural import load_procedural_doc

    fake_row = MagicMock()
    fake_row.current_doc = "No em dashes rule."
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row

    result = await load_procedural_doc(mock_db, "karl")
    assert result == "No em dashes rule."


@pytest.mark.asyncio
async def test_save_returns_version_1_on_first_save(mock_db):
    from src.memory.procedural import save_procedural_doc

    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    version = await save_procedural_doc(mock_db, "karl", "New rules doc")
    assert version == 1
    mock_db.add.assert_called()


@pytest.mark.asyncio
async def test_save_increments_version(mock_db):
    from src.memory.procedural import save_procedural_doc

    fake_row = MagicMock()
    fake_row.current_doc = "Old rules."
    fake_row.version = 1
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row

    version = await save_procedural_doc(mock_db, "karl", "Updated rules.")
    assert version == 2


@pytest.mark.asyncio
async def test_save_creates_history_row(mock_db):
    from src.memory.procedural import save_procedural_doc

    fake_row = MagicMock()
    fake_row.current_doc = "Old rules."
    fake_row.version = 2
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row

    await save_procedural_doc(mock_db, "karl", "Newer rules.", change_reason="user edit")
    # add should be called at least once (for history row)
    assert mock_db.add.call_count >= 1


@pytest.mark.asyncio
async def test_get_history_returns_newest_first(mock_db):
    from src.memory.procedural import get_procedural_history

    fake_rows = [MagicMock(version=3, doc="v3"), MagicMock(version=2, doc="v2")]
    mock_db.execute.return_value.scalars.return_value.all.return_value = fake_rows

    history = await get_procedural_history(mock_db, "karl")
    assert history[0]["version"] == 3
    assert history[1]["version"] == 2
