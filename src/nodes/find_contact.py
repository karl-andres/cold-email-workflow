import logging
from datetime import UTC, datetime

from langchain_core.messages import HumanMessage, SystemMessage

from src.state import AgentState
from src.tools.llm_factory import get_router_llm
from src.tools.proxycurl import find_people

logger = logging.getLogger(__name__)

_TARGET_ROLES = ["CEO", "CTO", "Co-founder", "Founder", "President", "VP Engineering", "VP Product", "Head of Engineering"]

_RANK_PROMPT = """\
Given these people at a startup, pick the single best person to cold email for a software engineering \
contribution/internship opportunity. Prefer technical leaders (CTO, VP Engineering) or founders at small \
companies. Reply with only the LinkedIn URL of the best contact, nothing else.

Candidates:
{candidates}"""


async def find_contact(state: AgentState) -> dict:
    # If user already provided contact info, skip the API call entirely
    if state.get("contact_name") and state.get("contact_role"):
        return {}

    linkedin_url = state.get("company_linkedin_url") or ""
    if not linkedin_url:
        return {}  # no LinkedIn URL, no way to search — proceed without contact

    people = await find_people(linkedin_url, role_filters=_TARGET_ROLES)

    if not people:
        return {
            "errors": [{"node": "find_contact", "error": "No matching contacts found.", "timestamp": _now()}],
        }

    if len(people) == 1:
        p = people[0]
        return {
            "contact_name": p["name"],
            "contact_linkedin_url": p["linkedin_url"],
            "contact_role": p["title"],
        }

    # Multiple candidates — use Haiku to rank (cheap)
    candidates_text = "\n".join(f"- {p['name']} ({p['title']}): {p['linkedin_url']}" for p in people[:5])
    llm = get_router_llm()
    response = await llm.ainvoke([
        SystemMessage(content="You are a concise assistant."),
        HumanMessage(content=_RANK_PROMPT.format(candidates=candidates_text)),
    ])
    chosen_url = response.content.strip().rstrip("/")

    match = next((p for p in people if p["linkedin_url"].rstrip("/") == chosen_url), None)
    if match is None:
        logger.warning("LLM returned unrecognised URL %r — falling back to first candidate", chosen_url)
        match = people[0]

    return {
        "contact_name": match["name"],
        "contact_linkedin_url": match["linkedin_url"],
        "contact_role": match["title"],
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()
