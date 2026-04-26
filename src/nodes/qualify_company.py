from src.config import settings
from src.state import AgentState
from src.tools.proxycurl import get_company, normalize_domain

# Proxycurl returns company_size as a range tuple or int depending on the endpoint.
# We take the upper bound of the range to be conservative.
_STAGE_ALIASES: dict[str, str] = {
    "seed": "seed",
    "pre-seed": "pre_seed",
    "pre_seed": "pre_seed",
    "series a": "series_a",
    "series_a": "series_a",
}


def _parse_size(raw) -> int | None:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        return raw[1]  # upper bound
    return None


def _parse_stage(funding_data: list | None) -> str | None:
    if not funding_data:
        return None
    latest = funding_data[-1] if isinstance(funding_data, list) else None
    if not latest:
        return None
    raw = (latest.get("funding_type") or "").lower().replace(" ", "_")
    return _STAGE_ALIASES.get(raw, raw)


async def qualify_company(state: AgentState) -> dict:
    # If user already provided size + stage, trust them and skip the API call
    if state.get("company_size") is not None and state.get("company_stage"):
        size = state["company_size"]
        stage = state["company_stage"]
        if not (settings.min_company_size <= size <= settings.max_company_size):
            return {
                "qualification_passed": False,
                "out_of_range_reason": f"Company size {size} outside range {settings.min_company_size}–{settings.max_company_size}.",
            }
        if stage not in settings.allowed_stage_list:
            return {
                "qualification_passed": False,
                "out_of_range_reason": f"Stage '{stage}' not in allowed list.",
            }
        return {"qualification_passed": True}

    linkedin_url = state.get("company_linkedin_url") or ""
    domain = state.get("company_domain") or ""

    lookup_key = linkedin_url or (f"https://{domain}" if domain else "")
    if not lookup_key or not settings.proxycurl_api_key:
        # No lookup key or no API key — pass through so user can still get an email
        return {"qualification_passed": True, "out_of_range_reason": None}

    company = await get_company(lookup_key)

    if company is None:
        return {
            "qualification_passed": False,
            "out_of_range_reason": "Company not found on LinkedIn.",
        }

    size = _parse_size(company.get("company_size"))
    stage = _parse_stage(company.get("funding_data"))
    linkedin_url_resolved = company.get("linkedin_internal_id") or linkedin_url

    if size is not None and not (settings.min_company_size <= size <= settings.max_company_size):
        return {
            "qualification_passed": False,
            "company_size": size,
            "company_stage": stage,
            "out_of_range_reason": f"Company size {size} outside range {settings.min_company_size}–{settings.max_company_size}.",
        }

    if stage and stage not in settings.allowed_stage_list:
        return {
            "qualification_passed": False,
            "company_size": size,
            "company_stage": stage,
            "out_of_range_reason": f"Stage '{stage}' not in allowed list: {settings.allowed_stage_list}.",
        }

    return {
        "qualification_passed": True,
        "company_size": size,
        "company_stage": stage,
        "company_domain": normalize_domain(domain),
        "company_linkedin_url": linkedin_url_resolved or linkedin_url,
    }
