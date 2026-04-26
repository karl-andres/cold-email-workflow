"""Firecrawl SDK wrapper with in-memory caching and retry."""

import asyncio
import logging
import re
import time

import httpx
from firecrawl import AsyncFirecrawl, Firecrawl
from firecrawl.v2.types import ScrapeOptions

from src.config import settings
from src.state import BlogPost

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[str, float]] = {}
_blog_cache: dict[str, tuple[str | None, float]] = {}  # domain → (blog_url, ts)

_async_client: AsyncFirecrawl | None = None
_sync_client: Firecrawl | None = None


def _get_async_client() -> AsyncFirecrawl:
    global _async_client
    if _async_client is None:
        _async_client = AsyncFirecrawl(api_key=settings.firecrawl_api_key)
    return _async_client


def _get_sync_client() -> Firecrawl:
    global _sync_client
    if _sync_client is None:
        _sync_client = Firecrawl(api_key=settings.firecrawl_api_key)
    return _sync_client


def clear_firecrawl_cache() -> None:
    _cache.clear()
    _blog_cache.clear()


def _is_cached(url: str) -> bool:
    if url not in _cache:
        return False
    _, ts = _cache[url]
    return (time.time() - ts) < settings.firecrawl_cache_ttl


def _blog_is_cached(domain: str) -> bool:
    if domain not in _blog_cache:
        return False
    _, ts = _blog_cache[domain]
    return (time.time() - ts) < settings.firecrawl_cache_ttl


_BLOG_PATHS = ["/blogs", "/blog", "/news", "/insights", "/articles", "/posts"]

# URL patterns that indicate index/navigation pages rather than post content
_NON_POST_PATTERNS = re.compile(
    r"/(tags?|categories|category|authors?|page|pages|sitemap|feed|rss|search)"
    r"(/|$)|[?#]|\.(xml|json|rss)$",
    re.IGNORECASE,
)


async def scrape_url(url: str) -> str:
    if _is_cached(url):
        return _cache[url][0]
    try:
        app = _get_async_client()
        result = await app.scrape(url, formats=["markdown"])  # type: ignore[arg-type]
        # result is a firecrawl.v2.types.Document (Pydantic model), not a dict
        markdown: str = result.markdown or "" if result else ""
        _cache[url] = (markdown, time.time())
        return markdown
    except Exception as exc:
        logger.warning("Firecrawl scrape failed for %s: %s", url, exc)
        return ""


async def crawl_site(url: str, max_pages: int = 10) -> str:
    cache_key = f"crawl:{url}"
    if _is_cached(cache_key):
        return _cache[cache_key][0]
    try:
        app = _get_sync_client()
        opts = ScrapeOptions(formats=["markdown"])
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: app.crawl(url, limit=max_pages, scrape_options=opts)
        )
        # result is a firecrawl.v2.types.CrawlJob; pages are Document models
        pages = result.data or [] if result else []
        combined = "\n\n---\n\n".join(
            p.markdown for p in pages if p.markdown
        )
        _cache[cache_key] = (combined, time.time())
        return combined
    except Exception as exc:
        logger.warning("Firecrawl crawl failed for %s: %s", url, exc)
        return ""


async def discover_blog(domain: str) -> str | None:
    if _blog_is_cached(domain):
        return _blog_cache[domain][0]

    base = domain.rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = f"https://{base}"

    # Check all paths in parallel — follow redirects to get final URL, accept any 2xx/3xx
    async def check(path: str) -> tuple[str | None, int]:
        candidate = f"{base}{path}"
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                resp = await client.head(candidate)
                # Return the final URL after redirects
                return str(resp.url), resp.status_code
        except Exception:
            return None, 0

    results = await asyncio.gather(*[check(p) for p in _BLOG_PATHS])
    found = next((url for url, code in results if url and 200 <= code < 400), None)

    _blog_cache[domain] = (found, time.time())
    return found


async def scrape_blog_posts(blog_url: str, max_posts: int = 3) -> list[BlogPost]:
    # Step 1: map the blog to discover individual post URLs
    try:
        app = _get_async_client()
        map_result = await app.map(blog_url, limit=5000, sitemap="include")
        links = map_result.links or []
    except Exception as exc:
        logger.warning("Firecrawl map failed for %s: %s", blog_url, exc)
        return []

    # Keep only child post URLs — exclude the index itself and non-post pages
    blog_base = blog_url.rstrip("/")
    post_urls = [
        link.url
        for link in links
        if link.url
        and link.url.rstrip("/") != blog_base
        and not _NON_POST_PATTERNS.search(link.url)
    ][:max_posts]

    if not post_urls:
        return []

    # Step 2: scrape all post URLs in parallel
    markdowns = await asyncio.gather(*[scrape_url(u) for u in post_urls])

    posts: list[BlogPost] = []
    for post_url, markdown in zip(post_urls, markdowns):
        if not markdown:
            continue
        title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE) or \
                      re.search(r"^(.+)$", markdown.strip(), re.MULTILINE)
        title = title_match.group(1).strip()[:120] if title_match else "Untitled"
        posts.append(BlogPost(title=title, content=markdown[:1000], url=post_url))

    return posts
