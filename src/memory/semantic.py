from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def load_profile(db: AsyncSession, user_id: str) -> str:
    from src.models import SemanticProfile

    result = await db.execute(
        select(SemanticProfile).where(SemanticProfile.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    return row.profile_doc if row else ""


async def save_profile(db: AsyncSession, user_id: str, profile_doc: str) -> None:
    from src.models import SemanticProfile

    result = await db.execute(
        select(SemanticProfile).where(SemanticProfile.user_id == user_id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        db.add(SemanticProfile(user_id=user_id, profile_doc=profile_doc))
    else:
        row.profile_doc = profile_doc
        row.updated_at = datetime.now(UTC)

    await db.commit()


async def append_fact(db: AsyncSession, user_id: str, fact: str) -> str:
    current = await load_profile(db, user_id)
    if current:
        updated = current.rstrip() + f"\n- {fact}"
    else:
        updated = f"- {fact}"
    await save_profile(db, user_id, updated)
    return updated
