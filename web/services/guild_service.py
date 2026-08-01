"""Service layer for guild operations."""
from .module_service import ModuleService, ModuleServiceError
from ..repositories.guild_repository import GuildRepository
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

class GuildService:
    def __init__(self):
        self.repository = GuildRepository()

    async def get_by_guild_id(self, session: AsyncSession, guild_id: str):
        return await self.repository.get_by_guild_id(session, guild_id)

    async def create_or_update(self, session: AsyncSession, guild_data: dict):
        return await self.repository.create_or_update(session, guild_data)

    async def list(self, session: AsyncSession):
        query = select(self.repository.model)
        result = await session.exec(query)
        return result.all()
