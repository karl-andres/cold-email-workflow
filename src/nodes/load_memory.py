from src.db import AsyncSessionLocal
from src.memory.procedural import load_procedural_doc
from src.memory.semantic import load_profile
from src.state import AgentState


async def load_memory(state: AgentState) -> dict:
    async with AsyncSessionLocal() as db:
        procedural_doc = await load_procedural_doc(db, state["user_id"])
        semantic_profile = await load_profile(db, state["user_id"])

    return {
        "procedural_doc": procedural_doc or None,
        "semantic_profile": semantic_profile or None,
    }
