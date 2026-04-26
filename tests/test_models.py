"""Unit tests for ORM models — no DB connection required."""

import uuid

import pytest

from src.models import (
    Episode,
    FirecrawlCache,
    ProceduralMemory,
    ProceduralMemoryHistory,
    ProxycurlCache,
    SemanticProfile,
)


def test_episode_defaults():
    ep = Episode(user_id="karl", company_name="Acme")
    assert ep.status == "drafted"
    assert ep.attempt_count == 1


def test_episode_valid_statuses():
    assert "drafted" in Episode.VALID_STATUSES
    assert "sent" in Episode.VALID_STATUSES
    assert "replied" in Episode.VALID_STATUSES
    assert "no_reply" in Episode.VALID_STATUSES
    assert "abandoned" in Episode.VALID_STATUSES


def test_episode_has_expected_columns():
    cols = {c.key for c in Episode.__table__.columns}
    expected = {
        "id", "user_id", "company_name", "company_domain", "company_linkedin_url",
        "contact_name", "contact_linkedin_url", "contact_role", "draft_email",
        "final_email", "status", "attempt_count", "eval_scores", "created_at", "updated_at",
    }
    assert expected.issubset(cols)


def test_procedural_memory_version_default():
    pm = ProceduralMemory(user_id="karl", current_doc="rules")
    assert pm.version == 1


def test_procedural_memory_history_columns():
    cols = {c.key for c in ProceduralMemoryHistory.__table__.columns}
    assert {"id", "user_id", "doc", "version", "change_reason", "created_at"}.issubset(cols)


def test_semantic_profile_columns():
    cols = {c.key for c in SemanticProfile.__table__.columns}
    assert {"id", "user_id", "profile_doc", "updated_at"}.issubset(cols)


def test_proxycurl_cache_columns():
    cols = {c.key for c in ProxycurlCache.__table__.columns}
    assert {"id", "url", "response_json", "fetched_at"}.issubset(cols)


def test_firecrawl_cache_columns():
    cols = {c.key for c in FirecrawlCache.__table__.columns}
    assert {"id", "url", "response_markdown", "fetched_at"}.issubset(cols)


def test_all_models_have_uuid_pk():
    for Model in (Episode, ProceduralMemory, ProceduralMemoryHistory, SemanticProfile, ProxycurlCache, FirecrawlCache):
        pk_cols = [c for c in Model.__table__.columns if c.primary_key]
        assert len(pk_cols) == 1, f"{Model.__name__} should have exactly one PK"
