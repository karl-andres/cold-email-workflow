import pytest
from unittest.mock import AsyncMock, MagicMock
from tests.conftest import *  # noqa: F401,F403

_GOOD_RUBRIC = """{
  "personalization_score": 5,
  "tone_match_score": 4,
  "clarity_score": 4,
  "cta_strength_score": 4,
  "length_score": 5,
  "rule_violations": [],
  "overall_pass": true,
  "feedback": "Looks good."
}"""

_BAD_RUBRIC = """{
  "personalization_score": 2,
  "tone_match_score": 3,
  "clarity_score": 4,
  "cta_strength_score": 3,
  "length_score": 4,
  "rule_violations": ["Contains em dash"],
  "overall_pass": false,
  "feedback": "Remove em dash and add a specific hook."
}"""


@pytest.mark.asyncio
async def test_evaluate_passes_good_email(fully_enriched_state, mocker):
    from src.nodes.evaluate import evaluate

    state = {**fully_enriched_state, "draft_email": "Saw your recent post on Rust infra..."}
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content=_GOOD_RUBRIC)
    mocker.patch("src.nodes.evaluate.get_router_llm", return_value=mock_llm)

    result = await evaluate(state)
    assert result["eval_passed"] is True
    assert result["eval_scores"]["overall_pass"] is True


@pytest.mark.asyncio
async def test_evaluate_fails_bad_email(fully_enriched_state, mocker):
    from src.nodes.evaluate import evaluate

    state = {**fully_enriched_state, "draft_email": "I hope this email finds you well — I am Karl."}
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content=_BAD_RUBRIC)
    mocker.patch("src.nodes.evaluate.get_router_llm", return_value=mock_llm)

    result = await evaluate(state)
    assert result["eval_passed"] is False
    assert len(result["eval_feedback_history"]) == 1


@pytest.mark.asyncio
async def test_evaluate_handles_empty_draft(fully_enriched_state, mocker):
    from src.nodes.evaluate import evaluate

    state = {**fully_enriched_state, "draft_email": ""}
    result = await evaluate(state)
    assert result["eval_passed"] is False
