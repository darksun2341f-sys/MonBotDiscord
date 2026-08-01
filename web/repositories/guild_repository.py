"""Repository for guild data access."""
from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ..models.guild import Guild
from .base import BaseRepository

class GuildRepository(BaseRepository[Guild]):
    def __init__(self):
        super().__init__(Guild)

    async def get_by_guild_id(self, session: AsyncSession, guild_id: str) -> Optional[Guild]:
        query = select(Guild).where(Guild.guild_id == guild_id)
        result = await session.exec(query)
        return result.one_or_none()

    async def create_or_update(self, session: AsyncSession, guild_data: dict) -> Guild:
        existing = await self.get_by_guild_id(session, guild_data["guild_id"])
        if existing:
            for key, value in guild_data.items():
                setattr(existing, key, value)
            return await self.update(session, existing)
        guild = Guild(**guild_data)
        return await self.create(session, guild)
