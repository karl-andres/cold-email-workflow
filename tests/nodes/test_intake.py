import pytest
from tests.conftest import *  # noqa: F401,F403


@pytest.mark.asyncio
async def test_intake_normalizes_whitespace(base_state):
    from src.nodes.intake import intake

    state = {**base_state, "company_name": "  Acme   Corp  "}
    result = await intake(state)
    assert result["company_name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_intake_resets_attempt_count(base_state):
    from src.nodes.intake import intake

    state = {**base_state, "attempt_count": 3}
    result = await intake(state)
    assert result["attempt_count"] == 0


@pytest.mark.asyncio
async def test_intake_clears_errors(base_state):
    from src.nodes.intake import intake

    state = {**base_state, "errors": [{"node": "old", "error": "stale", "timestamp": ""}]}
    result = await intake(state)
    assert result["errors"] == []
