from datetime import UTC, datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession


async def load_procedural_doc(db: AsyncSession, user_id: str) -> str:
    from src.models import ProceduralMemory

    result = await db.execute(
        select(ProceduralMemory).where(ProceduralMemory.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    return row.current_doc if row else ""


async def save_procedural_doc(
    db: AsyncSession,
    user_id: str,
    new_doc: str,
    change_reason: str | None = None,
) -> int:
    from src.models import ProceduralMemory, ProceduralMemoryHistory

    result = await db.execute(
        select(ProceduralMemory).where(ProceduralMemory.user_id == user_id)
    )
    row = result.scalar_one_or_none()

    if row is None:
        new_version = 1
        db.add(ProceduralMemory(user_id=user_id, current_doc=new_doc, version=new_version))
    else:
        new_version = row.version + 1
        db.add(
            ProceduralMemoryHistory(
                user_id=user_id,
                doc=row.current_doc,
                version=row.version,
                change_reason=change_reason,
            )
        )
        row.current_doc = new_doc
        row.version = new_version
        row.updated_at = datetime.now(UTC)

    await db.commit()
    return new_version


async def get_procedural_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 10,
) -> list[dict]:
    from src.models import ProceduralMemoryHistory

    result = await db.execute(
        select(ProceduralMemoryHistory)
        .where(ProceduralMemoryHistory.user_id == user_id)
        .order_by(desc(ProceduralMemoryHistory.created_at))
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "version": r.version,
            "doc": r.doc,
            "change_reason": r.change_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
