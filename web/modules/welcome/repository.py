"""Repository for welcome module data access."""
from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import WelcomeConfig
from ...repositories.base import BaseRepository


class WelcomeRepository(BaseRepository[WelcomeConfig]):
    def __init__(self):
        super().__init__(WelcomeConfig)

    async def get_by_guild_id(self, session: AsyncSession, guild_id: str) -> Optional[WelcomeConfig]:
        query = select(WelcomeConfig).where(WelcomeConfig.guild_id == guild_id)
        result = await session.exec(query)
        return result.one_or_none()

    async def create_or_update(self, session: AsyncSession, guild_id: str, values: dict) -> WelcomeConfig:
        existing = await self.get_by_guild_id(session, guild_id)
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            return await self.update(session, existing)
        payload = {**values, "guild_id": guild_id}
        return await self.create(session, payload)

    async def delete_by_guild_id(self, session: AsyncSession, guild_id: str) -> None:
        existing = await self.get_by_guild_id(session, guild_id)
        if existing:
            await self.delete(session, existing)
