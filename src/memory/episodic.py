import uuid

from rapidfuzz import fuzz
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.tools.proxycurl import normalize_domain

_FUZZY_THRESHOLD = 90
_ALLOWED_UPDATE_FIELDS = {"draft_email", "final_email", "status", "attempt_count", "eval_scores"}


async def find_duplicate(
    db: AsyncSession,
    user_id: str,
    company_name: str,
    company_domain: str | None = None,
    company_linkedin_url: str | None = None,
) -> dict | None:
    from src.models import Episode

    normalized_input_domain = normalize_domain(company_domain) if company_domain else None

    result = await db.execute(
        select(Episode)
        .where(Episode.user_id == user_id)
        .order_by(desc(Episode.created_at))
        .limit(200)
    )
    episodes = result.scalars().all()

    for ep in episodes:
        # Tier 1: exact domain match
        if normalized_input_domain and ep.company_domain:
            if normalize_domain(ep.company_domain) == normalized_input_domain:
                return _ep_to_dict(ep)
        # Tier 2: exact LinkedIn URL match
        if company_linkedin_url and ep.company_linkedin_url:
            if ep.company_linkedin_url.rstrip("/") == company_linkedin_url.rstrip("/"):
                return _ep_to_dict(ep)
        # Tier 3: fuzzy name match
        ratio = fuzz.token_set_ratio(company_name.lower(), ep.company_name.lower())
        if ratio > _FUZZY_THRESHOLD:
            return _ep_to_dict(ep)

    return None


async def create_episode(
    db: AsyncSession,
    user_id: str,
    company_name: str,
    company_domain: str | None = None,
    company_linkedin_url: str | None = None,
    contact_name: str | None = None,
    contact_linkedin_url: str | None = None,
    contact_role: str | None = None,
) -> str:
    from src.models import Episode

    episode_id = uuid.uuid4()
    db.add(
        Episode(
            id=episode_id,
            user_id=user_id,
            company_name=company_name,
            company_domain=normalize_domain(company_domain) if company_domain else None,
            company_linkedin_url=company_linkedin_url,
            contact_name=contact_name,
            contact_linkedin_url=contact_linkedin_url,
            contact_role=contact_role,
        )
    )
    await db.commit()
    return str(episode_id)


async def update_episode(db: AsyncSession, episode_id: str, **kwargs) -> None:
    from src.models import Episode

    unknown = set(kwargs) - _ALLOWED_UPDATE_FIELDS
    if unknown:
        raise ValueError(f"Cannot update fields: {unknown}")

    result = await db.execute(select(Episode).where(Episode.id == uuid.UUID(episode_id)))
    ep = result.scalar_one_or_none()
    if ep is None:
        return

    for field, value in kwargs.items():
        setattr(ep, field, value)

    await db.commit()


async def get_episode(db: AsyncSession, episode_id: str) -> dict | None:
    from src.models import Episode

    result = await db.execute(select(Episode).where(Episode.id == uuid.UUID(episode_id)))
    ep = result.scalar_one_or_none()
    return _ep_to_dict(ep) if ep else None


async def list_episodes(
    db: AsyncSession,
    user_id: str,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    from src.models import Episode

    query = select(Episode).where(Episode.user_id == user_id).order_by(desc(Episode.created_at)).limit(limit)
    if status:
        query = query.where(Episode.status == status)

    result = await db.execute(query)
    return [_ep_to_dict(ep) for ep in result.scalars().all()]


def _ep_to_dict(ep) -> dict:
    return {
        "id": str(ep.id),
        "user_id": ep.user_id,
        "company_name": ep.company_name,
        "company_domain": ep.company_domain,
        "company_linkedin_url": ep.company_linkedin_url,
        "contact_name": ep.contact_name,
        "contact_linkedin_url": ep.contact_linkedin_url,
        "contact_role": ep.contact_role,
        "draft_email": ep.draft_email,
        "final_email": ep.final_email,
        "status": ep.status,
        "attempt_count": ep.attempt_count,
        "eval_scores": ep.eval_scores,
        "created_at": ep.created_at.isoformat() if ep.created_at else None,
    }
