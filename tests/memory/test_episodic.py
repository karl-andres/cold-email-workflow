"""Tests for episodic memory module."""

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
async def test_find_duplicate_returns_none_when_no_episodes(mock_db):
    from src.memory.episodic import find_duplicate

    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    result = await find_duplicate(mock_db, "karl", "Unknown Corp")
    assert result is None


@pytest.mark.asyncio
async def test_find_duplicate_finds_exact_domain_match(mock_db):
    from src.memory.episodic import find_duplicate

    fake_ep = MagicMock()
    fake_ep.company_domain = "acme.com"
    fake_ep.company_name = "Acme"
    fake_ep.id = "some-uuid"
    mock_db.execute.return_value.scalars.return_value.all.return_value = [fake_ep]

    result = await find_duplicate(mock_db, "karl", "Acme", company_domain="https://www.ACME.com/")
    assert result is not None


@pytest.mark.asyncio
async def test_find_duplicate_finds_exact_linkedin_url_match(mock_db):
    from src.memory.episodic import find_duplicate

    fake_ep = MagicMock()
    fake_ep.company_domain = None
    fake_ep.company_linkedin_url = "https://linkedin.com/company/acme"
    fake_ep.company_name = "Acme"
    fake_ep.id = "some-uuid"
    mock_db.execute.return_value.scalars.return_value.all.return_value = [fake_ep]

    result = await find_duplicate(
        mock_db, "karl", "Acme",
        company_linkedin_url="https://linkedin.com/company/acme",
    )
    assert result is not None


@pytest.mark.asyncio
async def test_find_duplicate_finds_fuzzy_name_match(mock_db):
    from src.memory.episodic import find_duplicate

    fake_ep = MagicMock()
    fake_ep.company_domain = None
    fake_ep.company_linkedin_url = None
    fake_ep.company_name = "Acme Corporation"
    fake_ep.id = "some-uuid"
    mock_db.execute.return_value.scalars.return_value.all.return_value = [fake_ep]

    # "Acme Corp" should fuzzy-match "Acme Corporation"
    result = await find_duplicate(mock_db, "karl", "Acme Corp")
    assert result is not None


@pytest.mark.asyncio
async def test_find_duplicate_no_false_positive_on_low_similarity(mock_db):
    from src.memory.episodic import find_duplicate

    fake_ep = MagicMock()
    fake_ep.company_domain = None
    fake_ep.company_linkedin_url = None
    fake_ep.company_name = "Totally Different Company"
    mock_db.execute.return_value.scalars.return_value.all.return_value = [fake_ep]

    result = await find_duplicate(mock_db, "karl", "Acme")
    assert result is None


@pytest.mark.asyncio
async def test_create_episode_returns_uuid_string(mock_db):
    from src.memory.episodic import create_episode

    episode_id = await create_episode(mock_db, "karl", "Acme Corp")
    # Must be a non-empty string (UUID format)
    assert isinstance(episode_id, str)
    assert len(episode_id) > 0
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_episode_calls_commit(mock_db):
    from src.memory.episodic import update_episode

    fake_ep = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_ep

    await update_episode(mock_db, "some-uuid", status="sent")
    assert fake_ep.status == "sent"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_list_episodes_returns_list(mock_db):
    from src.memory.episodic import list_episodes

    ep1 = MagicMock()
    ep1.id = "uuid-1"
    ep1.company_name = "Acme"
    ep1.status = "drafted"
    mock_db.execute.return_value.scalars.return_value.all.return_value = [ep1]

    results = await list_episodes(mock_db, "karl")
    assert len(results) == 1
    assert results[0]["company_name"] == "Acme"
