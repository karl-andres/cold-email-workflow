"""Seeds initial procedural doc and empty semantic profile for the configured user."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings

_SEED_PATH = Path(__file__).parent / "seeds" / "procedural_initial.md"


async def seed_initial_data(db: AsyncSession) -> None:
    from src.models import ProceduralMemory, SemanticProfile

    user_id = settings.user_id
    procedural_doc = _SEED_PATH.read_text(encoding="utf-8")

    result = await db.execute(
        select(ProceduralMemory).where(ProceduralMemory.user_id == user_id)
    )
    if result.scalar_one_or_none() is None:
        db.add(ProceduralMemory(user_id=user_id, current_doc=procedural_doc, version=1))

    result2 = await db.execute(
        select(SemanticProfile).where(SemanticProfile.user_id == user_id)
    )
    if result2.scalar_one_or_none() is None:
        db.add(SemanticProfile(user_id=user_id, profile_doc=""))

    await db.commit()
