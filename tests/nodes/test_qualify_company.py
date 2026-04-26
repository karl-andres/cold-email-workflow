import pytest
from tests.conftest import *  # noqa: F401,F403


@pytest.mark.asyncio
async def test_qualify_fails_with_no_url_or_domain(base_state):
    from src.nodes.qualify_company import qualify_company

    result = await qualify_company(base_state)
    assert result["qualification_passed"] is False
    assert "No LinkedIn URL or domain" in result["out_of_range_reason"]


@pytest.mark.asyncio
async def test_qualify_fails_when_company_not_found(base_state, mocker):
    from src.nodes.qualify_company import qualify_company

    mocker.patch("src.nodes.qualify_company.get_company", return_value=None)
    state = {**base_state, "company_linkedin_url": "https://linkedin.com/company/x"}
    result = await qualify_company(state)
    assert result["qualification_passed"] is False
    assert "not found" in result["out_of_range_reason"].lower()


@pytest.mark.asyncio
async def test_qualify_fails_when_company_too_large(base_state, mocker):
    from src.nodes.qualify_company import qualify_company

    mocker.patch("src.nodes.qualify_company.get_company", return_value={
        "company_size": [201, 500],
        "funding_data": [{"funding_type": "series_a"}],
    })
    state = {**base_state, "company_linkedin_url": "https://linkedin.com/company/bigcorp"}
    result = await qualify_company(state)
    assert result["qualification_passed"] is False


@pytest.mark.asyncio
async def test_qualify_passes_for_valid_company(base_state, mocker):
    from src.nodes.qualify_company import qualify_company

    mocker.patch("src.nodes.qualify_company.get_company", return_value={
        "company_size": [11, 50],
        "funding_data": [{"funding_type": "series_a"}],
    })
    state = {**base_state, "company_linkedin_url": "https://linkedin.com/company/acme"}
    result = await qualify_company(state)
    assert result["qualification_passed"] is True
    assert result["company_size"] == 50
