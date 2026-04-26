import asyncio

from src.state import AgentState, BlogPost, Post
from src.tools.firecrawl import discover_blog, scrape_blog_posts, scrape_url
from src.tools.proxycurl import get_recent_posts


async def _fetch_posts(state: AgentState) -> list[Post]:
    url = state.get("contact_linkedin_url") or ""
    if not url:
        return []
    return await get_recent_posts(url, count=5)


async def _fetch_site(state: AgentState) -> str:
    domain = state.get("company_domain") or ""
    if not domain:
        return ""
    return await scrape_url(f"https://{domain}")


async def _fetch_blog(state: AgentState) -> list[BlogPost]:
    domain = state.get("company_domain") or ""
    if not domain:
        return []
    blog_url = await discover_blog(domain)
    if not blog_url:
        return []
    return await scrape_blog_posts(blog_url, max_posts=3)


async def gather_signals(state: AgentState) -> dict:
    posts, site_summary, blog_posts = await asyncio.gather(
        _fetch_posts(state),
        _fetch_site(state),
        _fetch_blog(state),
    )
    return {
        "contact_recent_posts": posts or None,
        "website_summary": site_summary or None,
        "blog_posts": blog_posts or None,
    }
