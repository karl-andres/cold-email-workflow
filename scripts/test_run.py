"""
Terminal test runner. You provide the contact — workflow handles research + drafting.

Usage (minimal — just Firecrawl + LLM, no LinkedIn needed):
    uv run python scripts/test_run.py \
        --company "Acme" \
        --domain "acme.com" \
        --contact-name "Jane Doe" \
        --contact-role "CTO"

Usage (full — with LinkedIn URL for post scraping):
    uv run python scripts/test_run.py \
        --company "Acme" \
        --domain "acme.com" \
        --contact-name "Jane Doe" \
        --contact-role "CTO" \
        --contact-linkedin "https://linkedin.com/in/janedoe"
"""
import argparse
import asyncio

from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from src.config import settings
from src.graph import build_graph

console = Console()


async def run(args: argparse.Namespace) -> None:
    graph = build_graph()
    thread = {"configurable": {"thread_id": f"{settings.user_id}:{args.company}"}}

    initial_state = {
        "user_id": settings.user_id,
        "company_name": args.company,
        "company_domain": args.domain,
        "company_linkedin_url": args.company_linkedin or None,
        "company_size": args.size,
        "company_stage": args.stage,
        "contact_name": args.contact_name or None,
        "contact_role": args.contact_role or None,
        "contact_linkedin_url": args.contact_linkedin or None,
        "user_notes": args.notes,
        "attempt_count": 0,
        "eval_feedback_history": [],
        "errors": [],
    }

    console.print(f"\n[bold green]Starting run for:[/bold green] {args.company}\n")

    await graph.ainvoke(initial_state, config=thread)

    while True:
        state = await graph.aget_state(thread)
        if not state.next:
            break

        tasks_with_interrupts = [t for t in state.tasks if t.interrupts]
        if not tasks_with_interrupts:
            break

        interrupt_val = tasks_with_interrupts[0].interrupts[0].value
        interrupt_type = interrupt_val.get("type", "")

        if interrupt_type == "dedupe_warning":
            console.print(Panel(interrupt_val["message"], title="[yellow]Already contacted[/yellow]"))
            proceed = Confirm.ask("Proceed anyway?")
            await graph.ainvoke(Command(resume=proceed), config=thread)

        elif interrupt_type == "human_review":
            console.print(Panel(
                interrupt_val.get("draft_email", ""),
                title=f"[cyan]Draft Email[/cyan] — attempt {interrupt_val.get('attempt_count', 1)}"
            ))
            scores = interrupt_val.get("scores", {})
            if any(v for v in scores.values() if v):
                score_line = "  ".join(
                    f"{k.capitalize()}: {v}/5"
                    for k, v in scores.items()
                    if k != "violations" and v
                )
                console.print(f"  {score_line}")
                if scores.get("violations"):
                    console.print(f"  [red]Violations:[/red] {', '.join(scores['violations'])}")

            action = Prompt.ask(
                "\nWhat do you want to do?",
                choices=["approve", "edit", "regenerate"],
                default="approve",
            )

            if action == "approve":
                await graph.ainvoke(Command(resume={"action": "approve"}), config=thread)
            elif action == "edit":
                edited = Prompt.ask("Paste edited email")
                await graph.ainvoke(Command(resume={"action": "edit", "text": edited}), config=thread)
            else:
                feedback = Prompt.ask("Feedback for the rewrite")
                await graph.ainvoke(Command(resume={"action": "regenerate", "feedback": feedback}), config=thread)
        else:
            break

    final_state = await graph.aget_state(thread)
    final_email = final_state.values.get("final_email")
    if final_email:
        console.print(Panel(final_email, title="[bold green]Final Email[/bold green]"))
        console.print("[dim]Copy the email above, find the contact via RocketReach/Apollo, and send it yourself.[/dim]\n")
    else:
        reason = final_state.values.get("out_of_range_reason") or "Run ended without producing an email."
        console.print(f"\n[yellow]{reason}[/yellow]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--domain", default=None, help="e.g. acme.com")
    parser.add_argument("--contact-name", default=None, help="e.g. 'Jane Doe'")
    parser.add_argument("--contact-role", default=None, help="e.g. 'CTO'")
    parser.add_argument("--contact-linkedin", default=None, help="Contact's LinkedIn URL (optional, for post scraping)")
    parser.add_argument("--company-linkedin", default=None, help="Company LinkedIn URL")
    parser.add_argument("--size", type=int, default=None, help="Employee count (skips API lookup)")
    parser.add_argument("--stage", default=None, help="e.g. seed, series_a (skips API lookup)")
    parser.add_argument("--notes", default=None)
    args = parser.parse_args()
    asyncio.run(run(args))
