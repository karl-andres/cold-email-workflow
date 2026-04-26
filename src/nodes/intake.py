import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.state import AgentState
from src.tools.llm_factory import get_router_llm

_PARSE_PROMPT = """\
Extract company and contact details from the user's message. Return a JSON object with these keys \
(use null for anything not mentioned):

{
  "company_name": string,
  "company_domain": string | null,
  "company_linkedin_url": string | null,
  "company_size": integer | null,
  "company_stage": string | null,
  "contact_name": string | null,
  "contact_role": string | null,
  "contact_linkedin_url": string | null,
  "user_notes": string | null
}

For company_stage use one of: seed, pre_seed, series_a, series_b, or null.
Return only valid JSON, no explanation."""


def _normalize_company_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


async def intake(state: AgentState) -> dict:
    base = {
        "attempt_count": 0,
        "eval_feedback_history": [],
        "errors": [],
    }

    if state.get("input_mode") == "natural_language":
        message = state.get("human_message") or ""
        llm = get_router_llm()
        response = await llm.ainvoke([
            SystemMessage(content=_PARSE_PROMPT),
            HumanMessage(content=message),
        ])
        try:
            raw = response.content.strip()
            # Strip markdown code fences that some models prepend/append
            raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
            raw = re.sub(r"\n?```\s*$", "", raw)
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"company_name": message}

        updates = {k: v for k, v in parsed.items() if v is not None}
        if "company_name" in updates:
            updates["company_name"] = _normalize_company_name(updates["company_name"])
        return {**base, **updates}

    return {
        **base,
        "company_name": _normalize_company_name(state["company_name"]),
    }
