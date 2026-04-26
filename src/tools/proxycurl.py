"""Proxycurl API client with in-memory caching and tenacity retry."""

import time
from urllib.parse import urlparse

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.config import settings
from src.state import Post

_BASE_URL = "https://nubela.co/proxycurl/api"

# url → (response_dict, fetched_timestamp)
_cache: dict[str, tuple[dict, float]] = {}


def clear_proxycurl_cache() -> None:
    _cache.clear()


def normalize_domain(url_or_domain: str) -> str:
    """Strip scheme, www., path, and lowercase. 'https://www.Acme.com/' -> 'acme.com'"""
    s = url_or_domain.strip().lower()
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    parsed = urlparse(s)
    host = parsed.netloc or parsed.path
    host = host.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def _is_rate_limit_error(exc: Exception) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {429, 503}


def _is_cached(url: str) -> bool:
    if url not in _cache:
        return False
    _, ts = _cache[url]
    return (time.time() - ts) < settings.proxycurl_cache_ttl


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    stop=stop_after_attempt(settings.max_tool_retries),
    reraise=True,
)
async def _get(path: str, params: dict) -> dict | None:
    headers = {"Authorization": f"Bearer {settings.proxycurl_api_key}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_BASE_URL}{path}", params=params, headers=headers)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        return resp.json()


async def get_company(linkedin_url: str) -> dict | None:
    if _is_cached(linkedin_url):
        return _cache[linkedin_url][0]
    result = await _get("/v2/linkedin/company", {"url": linkedin_url})
    if result is not None:
        _cache[linkedin_url] = (result, time.time())
    return result


async def find_people(
    company_linkedin_url: str,
    role_filters: list[str] | None = None,
) -> list[dict]:
    cache_key = f"people:{company_linkedin_url}"
    if _is_cached(cache_key):
        return _cache[cache_key][0]  # type: ignore[return-value]

    params: dict = {"linkedin_company_profile_url": company_linkedin_url, "page_size": 10}
    if role_filters:
        params["keyword_regex"] = "|".join(role_filters)
    result = await _get("/v2/linkedin/company/employees", params)
    if result is None:
        return []
    employees: list[dict] = result.get("employees", [])
    people = [
        {
            "name": e.get("profile", {}).get("full_name", ""),
            "linkedin_url": e.get("profile_url", ""),
            "title": e.get("profile", {}).get("occupation", ""),
        }
        for e in employees
    ]
    _cache[cache_key] = (people, time.time())  # type: ignore[assignment]
    return people


async def get_person(linkedin_url: str) -> dict | None:
    if _is_cached(linkedin_url):
        return _cache[linkedin_url][0]
    result = await _get("/v2/linkedin", {"url": linkedin_url})
    if result is not None:
        _cache[linkedin_url] = (result, time.time())
    return result


async def get_recent_posts(linkedin_url: str, count: int = 5) -> list[Post]:
    cache_key = f"posts:{linkedin_url}"
    if _is_cached(cache_key):
        return _cache[cache_key][0]  # type: ignore[return-value]

    result = await _get(
        "/v2/linkedin/person/posts",
        {"linkedin_profile_url": linkedin_url, "post_count": count},
    )
    if not result:
        return []

    posts: list[Post] = []
    for p in result.get("posts", [])[:count]:
        date_obj = p.get("posted_on")
        date_str: str | None = None
        if date_obj and isinstance(date_obj, dict):
            y, m, d = date_obj.get("year"), date_obj.get("month"), date_obj.get("day")
            if y and m and d:
                date_str = f"{y}-{m:02d}-{d:02d}"
        posts.append(Post(text=p.get("text", ""), date=date_str, url=p.get("post_url")))

    _cache[cache_key] = (posts, time.time())  # type: ignore[assignment]
    return posts
