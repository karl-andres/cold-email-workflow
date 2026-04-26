from src.state import AgentState


async def reflect_on_failure(state: AgentState) -> dict:
    """Passes through — feedback already in eval_feedback_history for draft_email to consume."""
    # No LLM call needed: eval.py already wrote structured feedback into eval_feedback_history.
    # draft_email reads the last entry on the next attempt.
    return {}
