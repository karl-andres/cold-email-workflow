from operator import add
from typing import Annotated, Literal, TypedDict


class Post(TypedDict):
    text: str
    date: str | None
    url: str | None


class BlogPost(TypedDict):
    title: str
    content: str
    url: str | None


class EvalRubric(TypedDict):
    personalization_score: int  # 1–5: references specific signal from posts/blog/site
    tone_match_score: int  # 1–5: matches procedural doc style rules
    clarity_score: int  # 1–5: readable in 30 seconds
    length_score: int  # 1–5: 100–180 words ideal
    rule_violations: list[str]  # explicit procedural rules broken
    overall_pass: bool  # all scores >= 4 AND no rule_violations
    feedback: str  # actionable instructions for next draft


class ErrorRecord(TypedDict):
    node: str
    error: str
    timestamp: str


class AgentState(TypedDict):
    # ── Inputs ──────────────────────────────────────────────
    input_mode: Literal["explicit", "natural_language"]  # defaults to "explicit"
    human_message: str | None  # free-text input when input_mode == "natural_language"
    user_id: str
    company_name: str
    user_notes: str | None

    # ── Resolved company & contact ───────────────────────────
    company_domain: str | None
    company_linkedin_url: str | None
    company_size: int | None
    company_stage: str | None  # e.g. "seed", "series_a", "series_b"
    qualification_passed: bool | None
    out_of_range_reason: str | None

    contact_name: str | None
    contact_linkedin_url: str | None
    contact_role: str | None
    contact_recent_posts: list[Post] | None

    # ── Scraped content ──────────────────────────────────────
    blog_url: str | None  # optional manual override — skips blog discovery
    website_summary: str | None
    blog_posts: list[BlogPost] | None
    personalization_hooks: list[str] | None  # 5–8 atomic hooks

    # ── Memory loaded for this run ───────────────────────────
    procedural_doc: str | None  # full writing-rules document
    semantic_profile: str | None  # single user profile doc (MVP)

    # ── Generation ───────────────────────────────────────────
    draft_email: str | None
    eval_scores: EvalRubric | None
    eval_passed: bool | None
    attempt_count: int
    # append-only accumulator across retry attempts
    eval_feedback_history: Annotated[list[str], add]

    # ── Human-in-the-loop ────────────────────────────────────
    user_action: Literal["approve", "edit", "regenerate"] | None
    user_edit_text: str | None  # populated when user_action == "edit"
    user_regen_feedback: str | None  # populated when user_action == "regenerate"
    final_email: str | None

    # ── Bookkeeping ──────────────────────────────────────────
    episode_id: str | None
    errors: Annotated[list[ErrorRecord], add]
