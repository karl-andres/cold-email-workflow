from langgraph.graph import END, START, StateGraph

from src.config import settings
from src.nodes.dedupe_check import dedupe_check
from src.nodes.draft_email import draft_email
from src.nodes.evaluate import evaluate
from src.nodes.extract_hooks import extract_hooks
from src.nodes.find_contact import find_contact
from src.nodes.gather_signals import gather_signals
from src.nodes.human_review import human_review
from src.nodes.intake import intake
from src.nodes.load_memory import load_memory
from src.nodes.persist_episodic import persist_episodic
from src.nodes.qualify_company import qualify_company
from src.nodes.reflect_on_failure import reflect_on_failure
from src.state import AgentState


def _route_after_dedupe(state: AgentState) -> str:
    # dedupe_check sets qualification_passed=False and out_of_range_reason when it's a duplicate
    if state.get("qualification_passed") is False:
        return "persist_episodic"
    return "qualify_company"


def _route_after_qualify(state: AgentState) -> str:
    return "find_contact" if state.get("qualification_passed") else "persist_episodic"


def _route_after_eval(state: AgentState) -> str:
    if state.get("eval_passed"):
        return "human_review"
    if state.get("attempt_count", 0) >= settings.max_draft_attempts:
        return "human_review"  # surface to user even after max retries
    return "reflect_on_failure"


def _route_after_review(state: AgentState) -> str:
    return "draft_email" if state.get("user_action") == "regenerate" else "persist_episodic"


def _build_builder() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("intake", intake)
    builder.add_node("dedupe_check", dedupe_check)
    builder.add_node("qualify_company", qualify_company)
    builder.add_node("find_contact", find_contact)
    builder.add_node("gather_signals", gather_signals)
    builder.add_node("extract_hooks", extract_hooks)
    builder.add_node("load_memory", load_memory)
    builder.add_node("draft_email", draft_email)
    builder.add_node("evaluate", evaluate)
    builder.add_node("reflect_on_failure", reflect_on_failure)
    builder.add_node("human_review", human_review)
    builder.add_node("persist_episodic", persist_episodic)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "dedupe_check")
    builder.add_conditional_edges(
        "dedupe_check", _route_after_dedupe,
        {"qualify_company": "qualify_company", "persist_episodic": "persist_episodic"},
    )
    builder.add_conditional_edges(
        "qualify_company", _route_after_qualify,
        {"find_contact": "find_contact", "persist_episodic": "persist_episodic"},
    )
    builder.add_edge("find_contact", "gather_signals")
    builder.add_edge("gather_signals", "extract_hooks")
    builder.add_edge("extract_hooks", "load_memory")
    builder.add_edge("load_memory", "draft_email")
    builder.add_edge("draft_email", "evaluate")
    builder.add_conditional_edges(
        "evaluate", _route_after_eval,
        {"human_review": "human_review", "reflect_on_failure": "reflect_on_failure"},
    )
    builder.add_edge("reflect_on_failure", "draft_email")
    builder.add_conditional_edges(
        "human_review", _route_after_review,
        {"draft_email": "draft_email", "persist_episodic": "persist_episodic"},
    )
    builder.add_edge("persist_episodic", END)

    return builder


def build_graph():
    return _build_builder().compile()


from contextlib import asynccontextmanager


@asynccontextmanager
async def postgres_graph():
    """
    Async context manager that yields a compiled graph with a live PostgresSaver.

    Usage:
        async with postgres_graph() as graph:
            result = await graph.ainvoke(...)
    """
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # type: ignore[import-untyped]

    # AsyncPostgresSaver uses psycopg3 directly — needs plain postgresql:// not postgresql+psycopg://
    dsn = settings.database_url_sync.replace("postgresql+psycopg://", "postgresql://")
    async with await AsyncPostgresSaver.from_conn_string(dsn) as saver:
        await saver.setup()
        yield _build_builder().compile(checkpointer=saver)
