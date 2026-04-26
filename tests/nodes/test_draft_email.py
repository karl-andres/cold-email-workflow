import pytest
from unittest.mock import AsyncMock, MagicMock
from tests.conftest import *  # noqa: F401,F403


@pytest.mark.asyncio
async def test_draft_email_calls_llm(fully_enriched_state, mocker):
    from src.nodes.draft_email import draft_email

    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="Hey, saw your blog post on Rust infra...")
    mocker.patch("src.nodes.draft_email.get_writer_llm", return_value=mock_llm)

    result = await draft_email(fully_enriched_state)
    assert result["draft_email"] == "Hey, saw your blog post on Rust infra..."
    assert result["attempt_count"] == 1


@pytest.mark.asyncio
async def test_draft_email_increments_attempt_count(fully_enriched_state, mocker):
    from src.nodes.draft_email import draft_email

    state = {**fully_enriched_state, "attempt_count": 1}
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="Second draft...")
    mocker.patch("src.nodes.draft_email.get_writer_llm", return_value=mock_llm)

    result = await draft_email(state)
    assert result["attempt_count"] == 2


@pytest.mark.asyncio
async def test_draft_email_includes_feedback_on_retry(fully_enriched_state, mocker):
    from src.nodes.draft_email import draft_email

    state = {**fully_enriched_state, "eval_feedback_history": ["Remove the em dash on line 2."]}
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="Fixed draft.")
    mocker.patch("src.nodes.draft_email.get_writer_llm", return_value=mock_llm)

    await draft_email(state)
    call_args = mock_llm.ainvoke.call_args[0][0]
    # The HumanMessage should contain the feedback
    human_msg = next(m for m in call_args if hasattr(m, "content") and "Remove the em dash" in m.content)
    assert human_msg is not None
