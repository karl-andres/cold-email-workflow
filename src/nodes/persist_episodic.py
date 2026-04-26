import logging

from src.db import AsyncSessionLocal
from src.memory.episodic import create_episode, update_episode
from src.state import AgentState

logger = logging.getLogger(__name__)


async def persist_episodic(state: AgentState) -> dict:
    user_action = state.get("user_action")
    qualification_passed = state.get("qualification_passed")

    if not qualification_passed:
        status = "abandoned"
    elif user_action == "approve":
        status = "sent"
    else:
        status = "drafted"

    async with AsyncSessionLocal() as db:
        existing_id = state.get("episode_id")

        if existing_id:
            await update_episode(
                db,
                existing_id,
                draft_email=state.get("draft_email"),
                final_email=state.get("final_email"),
                status=status,
                attempt_count=state.get("attempt_count", 1),
                eval_scores=state.get("eval_scores"),
            )
            return {}

        try:
            episode_id = await create_episode(
                db,
                user_id=state["user_id"],
                company_name=state["company_name"],
                company_domain=state.get("company_domain"),
                company_linkedin_url=state.get("company_linkedin_url"),
                contact_name=state.get("contact_name"),
                contact_linkedin_url=state.get("contact_linkedin_url"),
                contact_role=state.get("contact_role"),
            )
            await update_episode(
                db,
                episode_id,
                draft_email=state.get("draft_email"),
                final_email=state.get("final_email"),
                status=status,
                attempt_count=state.get("attempt_count", 1),
                eval_scores=state.get("eval_scores"),
            )
        except Exception as exc:
            logger.warning("persist_episodic: episode creation failed — %s", exc, exc_info=True)
            return {}

    return {"episode_id": episode_id}
