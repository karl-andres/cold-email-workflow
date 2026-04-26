"""Run once after `alembic upgrade head` to seed initial data."""
import asyncio
from src.db import AsyncSessionLocal
from src.memory.seed import seed_initial_data

async def main():
    async with AsyncSessionLocal() as db:
        await seed_initial_data(db)
    print("Seeded procedural memory and empty profile.")

asyncio.run(main())
