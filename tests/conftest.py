"""Shared pytest fixtures for the cold-email-workflow test suite."""

import pytest

from src.state import AgentState


# ── Default user/company fixtures ────────────────────────────────────────────


@pytest.fixture
def user_id() -> str:
    return "karl"


@pytest.fixture
def base_state(user_id: str) -> AgentState:
    """Minimal valid AgentState for unit tests."""
    return AgentState(
        user_id=user_id,
        company_name="Acme Corp",
        user_notes=None,
        company_domain=None,
        company_linkedin_url=None,
        company_size=None,
        company_stage=None,
        qualification_passed=None,
        out_of_range_reason=None,
        contact_name=None,
        contact_linkedin_url=None,
        contact_role=None,
        contact_recent_posts=None,
        website_summary=None,
        blog_posts=None,
        personalization_hooks=None,
        procedural_doc=None,
        semantic_profile=None,
        draft_email=None,
        eval_scores=None,
        eval_passed=None,
        attempt_count=0,
        eval_feedback_history=[],
        user_action=None,
        user_edit_text=None,
        user_regen_feedback=None,
        final_email=None,
        episode_id=None,
        errors=[],
    )


@pytest.fixture
def qualified_state(base_state: AgentState) -> AgentState:
    """State after successful company qualification."""
    return {
        **base_state,
        "company_domain": "acme.com",
        "company_linkedin_url": "https://linkedin.com/company/acme",
        "company_size": 45,
        "company_stage": "series_a",
        "qualification_passed": True,
        "contact_name": "Jane Doe",
        "contact_linkedin_url": "https://linkedin.com/in/janedoe",
        "contact_role": "CTO",
    }


@pytest.fixture
def fully_enriched_state(qualified_state: AgentState) -> AgentState:
    """State with all signals gathered, ready for email drafting."""
    return {
        **qualified_state,
        "contact_recent_posts": [
            {"text": "Excited about our new AI infra overhaul", "date": "2026-04-20", "url": None},
            {"text": "The best engineers I know are all curious generalists", "date": "2026-04-15", "url": None},
        ],
        "website_summary": "Acme builds developer tooling for AI teams.",
        "blog_posts": [
            {"title": "Why we rewrote in Rust", "content": "Performance was our bottleneck...", "url": "https://acme.com/blog/rust"},
        ],
        "personalization_hooks": [
            "Rebuilding infra in Rust — performance-first culture",
            "CTO emphasises curious generalist engineers",
            "AI developer tooling — small, high-leverage team",
        ],
        "procedural_doc": "No em dashes. Lead with value. Keep under 180 words.",
        "semantic_profile": "Karl Andres — 2nd year CS student. Built a distributed task queue in Rust. Interned at a fintech startup. Interested in infra, systems, and AI tooling.",
    }
