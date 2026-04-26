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
  "blog_url": string | null,
  "user_notes": string | null
}

For company_stage use one of: seed, pre_seed, series_a, series_b, or null.
For blog_url: extract any explicit blog or news URL the user provides (e.g. "their blog is at acme.com/blog"). \
  Do not infer a blog URL from the company domain.
For user_notes: capture any additional context, observations, or instructions the user mentions that \
  don't fit the other fields (e.g. "they're hiring ML engineers", "focus on their RAG work", "avoid mentioning X").
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
