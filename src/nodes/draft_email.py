from langchain_core.messages import HumanMessage, SystemMessage

from src.state import AgentState
from src.tools.llm_factory import get_writer_llm

_FALLBACK_SYSTEM = """\
You write cold emails for Karl, a software engineer seeking internships at early-stage startups.

HARD RULES — never break these:
- Salutation: always "Hey [first name]," — never "Dear"
- Max 4 short paragraphs
- Sign off with only "Karl" on its own line — no "Best regards", "Thanks", "Sincerely", or any word before the name
- Never start a sentence with "I"
- No em dashes — use regular dashes or restructure
- Never mention a project unless it directly addresses the company's specific problem — no generic project dumping
- Never identify yourself by job title or school mid-email — just describe what you built
- Closing line must be exactly or very close to: "Would love to contribute if there's a fit with the team!"
- Never explicitly ask for an internship — end with possibility
- Under 150 words
- Lead with their world, not your resume"""

_FEW_SHOT_EXAMPLE = """\
THESE EXAMPLES SHOW FORMAT AND STRUCTURE ONLY.
Never copy, paraphrase, or reference any content from them.
Every word in the actual email must come from the SENDER PROFILE, HOOKS, and COMPANY CONTEXT above — not from these examples.

---

## Format Example 1

Hey Alex,

[Open with one specific thing from the company's blog or posts that connects to their core mission — not a changelog item or event. One or two sentences max.]

[Describe 1-2 things you built that directly address that same problem. Include a concrete metric if you have one. Do not name-drop technologies for their own sake.]

[One sentence on why this specific problem space is what you want to work on.]

Would love to contribute if there's a fit with the team!

Karl

---

## Format Example 2

Hey Sam,

[Open with a specific insight from their blog or LinkedIn that made you reach out. Name the idea, not just the post.]

[Connect your own work to their architecture or problem. Show pattern recognition — "same problem, different domain" is a strong move when true.]

Would love to contribute if there's a fit with the team!

Karl"""

_DRAFT_INSTRUCTION = """\
Write a cold email to {contact_name} ({contact_role}) at {company_name}.

ABOUT THE SENDER:
{profile}

PERSONALIZATION HOOKS (use at least one):
{hooks}

COMPANY CONTEXT:
{site_summary}

PREVIOUS EVAL FEEDBACK (if any — fix these issues):
{feedback}

{example}

IMPORTANT: The format examples above contain placeholder text only. Do not copy any content, \
names, metrics, technologies, or phrases from them into the email. \
Use ONLY the hooks, sender profile, and company context provided above. \
If any content from the examples appears in the email, you have failed.

Write only the email body. No subject line. No placeholder brackets."""


async def draft_email(state: AgentState) -> dict:
    hooks = state.get("personalization_hooks") or []
    hooks_text = "\n".join(f"- {h}" for h in hooks) if hooks else "None available."

    feedback_history = state.get("eval_feedback_history") or []
    feedback_text = feedback_history[-1] if feedback_history else "None — first attempt."

    profile = state.get("semantic_profile") or "No profile loaded."
    site_summary = (state.get("website_summary") or "")[:800]

    procedural_doc = state.get("procedural_doc") or ""

    prompt = _DRAFT_INSTRUCTION.format(
        contact_name=state.get("contact_name") or "the founder",
        contact_role=state.get("contact_role") or "founder",
        company_name=state["company_name"],
        profile=profile,
        hooks=hooks_text,
        site_summary=site_summary or "Not available.",
        feedback=feedback_text,
        example=_FEW_SHOT_EXAMPLE,
    )

    llm = get_writer_llm()
    response = await llm.ainvoke([
        SystemMessage(content=procedural_doc or _FALLBACK_SYSTEM),
        HumanMessage(content=prompt),
    ])

    return {
        "draft_email": response.content.strip(),
        "attempt_count": state.get("attempt_count", 0) + 1,
    }
