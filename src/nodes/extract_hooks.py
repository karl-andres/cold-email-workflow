import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from src.state import AgentState, BlogPost
from src.tools.firecrawl import scrape_url
from src.tools.llm_factory import get_router_llm

_SYSTEM = """\
You extract personalization hooks from company research for use in cold emails.

Prioritize hooks about the company's core mission and technical vision. \
Discard hooks about changelog updates, community events, or awards. \
A good hook connects directly to why an engineer would want to work on this problem.

DISCARD these hook types — do not include them:
- Changelog or feature release announcements (new dashboards, OTP fields, badge systems, API updates)
- Community events (Hackathons, open source recaps, sponsor announcements)
- Generic company values or culture posts ("we value transparency", "we're hiring")
- Awards, press mentions, or fundraising announcements

KEEP these hook types:
- The core technical problem the company is solving
- Their product vision or architectural direction
- A specific insight or take from a blog post about their domain
- A stated belief about where their industry is going

Write each hook in third person about the company. \
Never fabricate a connection. Only extract what is explicitly stated in the research."""

_PROMPT = """\
Extract 3-6 personalization hooks from the research below. Each hook must be a single sentence \
answering "why is this company's core technical problem interesting?" — NOT "what did they ship last month?"

These hooks will be used to open or anchor a cold email. Return only a numbered list, nothing else.
Write each hook as an observation ABOUT the company (e.g. "Chimoney is building X for Y").

HOOK QUALITY EXAMPLES:
BAD: "Chimoney released OTP on Payouts and User Achievement Badges in April 2024"
BAD: "Chimoney participated in Hacktoberfest 2023"
BAD: "Chimoney was featured in TechCrunch"
GOOD: "Chimoney is building identity and wallet infrastructure for AI agents, treating them as first-class financial participants alongside humans"
GOOD: "Chimoney wrote about the gap between global payment infrastructure and what AI agents actually need to transact autonomously"

LINKEDIN POSTS:
{posts}

WEBSITE SUMMARY:
{site}

BLOG POSTS:
{blog}"""

_MAX_BLOG_CHARS = 2000  # per post


async def _enrich_blog_post(post: BlogPost) -> str:
    """Scrape the full post content from its URL; fall back to stored content."""
    url = post.get("url")
    if url:
        full = await scrape_url(url)
        if full:
            return f"### {post['title']}\n{full[:_MAX_BLOG_CHARS]}"
    return f"### {post['title']}\n{post.get('content', '')}"


async def extract_hooks(state: AgentState) -> dict:
    posts = state.get("contact_recent_posts") or []
    posts_text = "\n".join(f"- {p['text'][:200]}" for p in posts) if posts else "None"

    site_text = (state.get("website_summary") or "")[:1500]

    blog_posts = state.get("blog_posts") or []

    if not posts and not site_text and not blog_posts:
        return {"personalization_hooks": []}

    if blog_posts:
        enriched = await asyncio.gather(*[_enrich_blog_post(b) for b in blog_posts])
        blog_text = "\n\n".join(enriched)
    else:
        blog_text = "None"

    llm = get_router_llm()  # Haiku — extraction doesn't need Sonnet
    response = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=_PROMPT.format(posts=posts_text, site=site_text, blog=blog_text)),
    ])

    lines = [ln.strip() for ln in response.content.strip().splitlines() if ln.strip()]
    # Strip leading numbering (e.g. "1. " or "- ")
    hooks = [ln.lstrip("0123456789.-) ").strip() for ln in lines if ln]

    return {"personalization_hooks": hooks[:6]}
