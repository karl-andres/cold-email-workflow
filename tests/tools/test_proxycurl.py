"""Tests for Proxycurl tool wrapper. All HTTP calls are mocked."""

import pytest

from src.tools.proxycurl import (
    clear_proxycurl_cache,
    get_company,
    get_person,
    get_recent_posts,
    normalize_domain,
)


# ── normalize_domain ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://www.acme.com/", "acme.com"),
        ("http://Acme.COM", "acme.com"),
        ("www.acme.com", "acme.com"),
        ("acme.com", "acme.com"),
        ("https://acme.com/about", "acme.com"),
        ("ACME.COM", "acme.com"),
    ],
)
def test_normalize_domain(raw: str, expected: str) -> None:
    assert normalize_domain(raw) == expected


# ── get_company ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_company_returns_dict_on_200(mocker):
    clear_proxycurl_cache()
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "Acme",
        "company_size": [11, 50],
        "funding_data": [{"funding_type": "series_a"}],
    }
    mock_response.raise_for_status = mocker.MagicMock()

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await get_company("https://linkedin.com/company/acme")
    assert result is not None
    assert result["name"] == "Acme"


@pytest.mark.asyncio
async def test_get_company_returns_none_on_404(mocker):
    clear_proxycurl_cache()
    import httpx

    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=mocker.MagicMock(), response=mock_response
    )

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await get_company("https://linkedin.com/company/nonexistent")
    assert result is None


# ── get_recent_posts ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_recent_posts_returns_post_typeddicts(mocker):
    clear_proxycurl_cache()
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.return_value = {
        "posts": [
            {"text": "Post one", "posted_on": {"year": 2026, "month": 4, "day": 20}, "post_url": "https://linkedin.com/p/1"},
            {"text": "Post two", "posted_on": None, "post_url": None},
        ]
    }
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    posts = await get_recent_posts("https://linkedin.com/in/janedoe", count=2)
    assert len(posts) == 2
    assert posts[0]["text"] == "Post one"
    assert posts[1]["date"] is None


@pytest.mark.asyncio
async def test_get_recent_posts_returns_empty_on_404(mocker):
    clear_proxycurl_cache()
    import httpx

    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=mocker.MagicMock(), response=mock_response
    )
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    posts = await get_recent_posts("https://linkedin.com/in/nobody")
    assert posts == []


@pytest.mark.asyncio
async def test_get_recent_posts_retries_on_429(mocker):
    """Function should retry on 429 and eventually succeed."""
    clear_proxycurl_cache()
    import httpx

    call_count = 0

    async def flaky_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        resp = mocker.MagicMock()
        if call_count < 3:
            resp.status_code = 429
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Too Many Requests", request=mocker.MagicMock(), response=resp
            )
        else:
            resp.status_code = 200
            resp.raise_for_status = mocker.MagicMock()
            resp.json.return_value = {"posts": [{"text": "Late post", "posted_on": None, "post_url": None}]}
        return resp

    mocker.patch("httpx.AsyncClient.get", side_effect=flaky_get)

    posts = await get_recent_posts("https://linkedin.com/in/janedoe")
    assert len(posts) == 1
    assert call_count == 3


@pytest.mark.asyncio
async def test_cache_hit_skips_http_call(mocker):
    """Second call with same URL should not make another HTTP request."""
    clear_proxycurl_cache()
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.return_value = {"name": "Acme", "company_size": [11, 50], "funding_data": []}
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await get_company("https://linkedin.com/company/acme-cached")
    await get_company("https://linkedin.com/company/acme-cached")

    assert mock_get.call_count == 1
