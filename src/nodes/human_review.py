from langgraph.types import interrupt

from src.state import AgentState


async def human_review(state: AgentState) -> dict:
    eval_scores = state.get("eval_scores") or {}
    eval_passed = state.get("eval_passed", False)
    attempt_count = state.get("attempt_count", 0)

    response = interrupt({
        "type": "human_review",
        "draft_email": state.get("draft_email"),
        "eval_passed": eval_passed,
        "attempt_count": attempt_count,
        "scores": {
            "personalization": eval_scores.get("personalization_score"),
            "tone": eval_scores.get("tone_match_score"),
            "clarity": eval_scores.get("clarity_score"),
            "length": eval_scores.get("length_score"),
            "violations": eval_scores.get("rule_violations", []),
        },
        "message": "Review the email above. Reply with: {'action': 'approve'|'edit'|'regenerate', 'text': '<edited email if edit>', 'feedback': '<notes if regenerate>'}",
    })

    action = response.get("action", "approve")

    if action == "edit":
        final = response.get("text") or state.get("draft_email")
        return {"user_action": "edit", "final_email": final, "user_edit_text": final}

    if action == "regenerate":
        return {
            "user_action": "regenerate",
            "user_regen_feedback": response.get("feedback", ""),
            "eval_feedback_history": [response.get("feedback", "User requested regeneration.")],
        }

    # approve
    return {"user_action": "approve", "final_email": state.get("draft_email")}
