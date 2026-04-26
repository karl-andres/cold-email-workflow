from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.memory import episodic, procedural, semantic


@dataclass
class MemoryStore:
    db: AsyncSession

    async def get_procedural(self, user_id: str) -> str:
        return await procedural.load_procedural_doc(self.db, user_id)

    async def get_profile(self, user_id: str) -> str:
        return await semantic.load_profile(self.db, user_id)

    async def find_duplicate(
        self,
        user_id: str,
        company_name: str,
        company_domain: str | None = None,
        company_linkedin_url: str | None = None,
    ) -> dict | None:
        return await episodic.find_duplicate(
            self.db, user_id, company_name, company_domain, company_linkedin_url
        )

    async def create_episode(
        self,
        user_id: str,
        company_name: str,
        company_domain: str | None = None,
        company_linkedin_url: str | None = None,
        contact_name: str | None = None,
        contact_linkedin_url: str | None = None,
        contact_role: str | None = None,
    ) -> str:
        return await episodic.create_episode(
            self.db, user_id, company_name, company_domain,
            company_linkedin_url, contact_name, contact_linkedin_url, contact_role,
        )

    async def update_episode(self, episode_id: str, **kwargs) -> None:
        await episodic.update_episode(self.db, episode_id, **kwargs)
