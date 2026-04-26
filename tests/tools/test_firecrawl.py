"""Tests for Firecrawl tool wrapper. All SDK calls are mocked."""

import pytest

from src.tools.firecrawl import (
    clear_firecrawl_cache,
    discover_blog,
    scrape_url,
)


@pytest.mark.asyncio
async def test_scrape_url_returns_markdown(mocker):
    clear_firecrawl_cache()
    mock_app = mocker.MagicMock()
    mock_app.scrape_url.return_value = {"markdown": "# Acme\nWe build AI tools."}
    mocker.patch("src.tools.firecrawl._get_client", return_value=mock_app)

    result = await scrape_url("https://acme.com")
    assert "Acme" in result


@pytest.mark.asyncio
async def test_scrape_url_returns_empty_on_exception(mocker):
    clear_firecrawl_cache()
    mock_app = mocker.MagicMock()
    mock_app.scrape_url.side_effect = Exception("rate limit")
    mocker.patch("src.tools.firecrawl._get_client", return_value=mock_app)

    result = await scrape_url("https://acme.com/bad")
    assert result == ""


@pytest.mark.asyncio
async def test_scrape_url_cache_hit_skips_sdk(mocker):
    clear_firecrawl_cache()
    mock_app = mocker.MagicMock()
    mock_app.scrape_url.return_value = {"markdown": "# Cached"}
    mocker.patch("src.tools.firecrawl._get_client", return_value=mock_app)

    await scrape_url("https://acme.com/cached")
    await scrape_url("https://acme.com/cached")

    assert mock_app.scrape_url.call_count == 1


@pytest.mark.asyncio
async def test_discover_blog_returns_url_when_blog_exists(mocker):
    async def mock_head(url, **kwargs):
        resp = mocker.MagicMock()
        if "/blog" in url:
            resp.status_code = 200
        else:
            resp.status_code = 404
        return resp

    mocker.patch("httpx.AsyncClient.head", side_effect=mock_head)

    result = await discover_blog("acme.com")
    assert result is not None
    assert "blog" in result


@pytest.mark.asyncio
async def test_discover_blog_returns_none_when_all_paths_404(mocker):
    async def mock_head(url, **kwargs):
        resp = mocker.MagicMock()
        resp.status_code = 404
        return resp

    mocker.patch("httpx.AsyncClient.head", side_effect=mock_head)

    result = await discover_blog("noBlogHere.com")
    assert result is None
