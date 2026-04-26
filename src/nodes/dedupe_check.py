from langgraph.types import interrupt

from src.db import AsyncSessionLocal
from src.memory.episodic import find_duplicate
from src.state import AgentState


async def dedupe_check(state: AgentState) -> dict:
    async with AsyncSessionLocal() as db:
        dup = await find_duplicate(
            db,
            user_id=state["user_id"],
            company_name=state["company_name"],
            company_domain=state.get("company_domain"),
            company_linkedin_url=state.get("company_linkedin_url"),
        )

    if dup is None:
        return {}

    proceed = interrupt({
        "type": "dedupe_warning",
        "message": f"Already contacted {dup['company_name']} (status: {dup['status']}). Proceed anyway?",
        "existing_episode": dup,
    })

    if not proceed:
        return {
            "qualification_passed": False,
            "out_of_range_reason": "Skipped — already contacted this company.",
        }

    return {}
