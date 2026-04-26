import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from src.eval.rubric import JUDGE_SYSTEM_PROMPT, PASS_THRESHOLD, EvalRubric
from src.state import AgentState
from src.tools.llm_factory import get_router_llm

logger = logging.getLogger(__name__)

_EVAL_PROMPT = """\
Email to evaluate:
---
{email}
---

Respond with valid JSON matching this schema exactly:
{{
  "personalization_score": <1-5>,
  "tone_match_score": <1-5>,
  "clarity_score": <1-5>,
  "length_score": <1-5>,
  "rule_violations": ["<violation>" ...],
  "overall_pass": <true|false>,
  "feedback": "<actionable fix instructions>"
}}"""


async def evaluate(state: AgentState) -> dict:
    draft = state.get("draft_email") or ""
    if not draft:
        return {
            "eval_passed": False,
            "eval_scores": None,
            "eval_feedback_history": ["No draft to evaluate."],
        }

    llm = get_router_llm()  # Haiku — deterministic scoring, doesn't need Sonnet
    response = await llm.ainvoke([
        SystemMessage(content=JUDGE_SYSTEM_PROMPT),
        HumanMessage(content=_EVAL_PROMPT.format(email=draft)),
    ])

    try:
        parser = JsonOutputParser()
        scores: EvalRubric = parser.parse(response.content)
    except Exception as exc:
        logger.warning("evaluate: JSON parse failed — %s\nRaw response: %s", exc, response.content)
        return {
            "eval_passed": False,
            "eval_scores": None,
            "eval_feedback_history": ["Eval parse failed — retry."],
        }

    # Enforce the pass rule: all scores >= threshold AND no violations
    all_pass = all(
        scores.get(k, 0) >= PASS_THRESHOLD
        for k in ("personalization_score", "tone_match_score", "clarity_score", "length_score")
    )
    passed = all_pass and not scores.get("rule_violations")
    scores["overall_pass"] = passed

    return {
        "eval_scores": scores,
        "eval_passed": passed,
        "eval_feedback_history": [scores["feedback"]] if not passed else [],
    }
