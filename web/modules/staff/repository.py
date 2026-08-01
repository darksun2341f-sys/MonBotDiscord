from typing import Optional, Sequence
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import StaffMember, StaffStats, StaffNotificationSettings, StaffEvent
from ...repositories.base import BaseRepository


class StaffRepository(BaseRepository[StaffMember]):
    def __init__(self):
        super().__init__(StaffMember)

    async def get_by_discord_id(self, session: AsyncSession, guild_id: str, discord_id: str) -> Optional[StaffMember]:
        query = select(StaffMember).where(StaffMember.guild_id == guild_id, StaffMember.discord_id == discord_id)
        result = await session.exec(query)
        return result.one_or_none()

    async def list_by_guild(self, session: AsyncSession, guild_id: str) -> Sequence[StaffMember]:
        query = select(StaffMember).where(StaffMember.guild_id == guild_id)
        result = await session.exec(query)
        return result.all()


class StaffStatsRepository(BaseRepository[StaffStats]):
    def __init__(self):
        super().__init__(StaffStats)

    async def get_by_member(self, session: AsyncSession, member_id: int) -> Optional[StaffStats]:
        query = select(StaffStats).where(StaffStats.member_id == member_id)
        result = await session.exec(query)
        return result.one_or_none()

    async def list_by_member_ids(self, session: AsyncSession, member_ids: Sequence[int]) -> Sequence[StaffStats]:
        query = select(StaffStats).where(StaffStats.member_id.in_(member_ids))
        result = await session.exec(query)
        return result.all()


class StaffNotificationSettingsRepository(BaseRepository[StaffNotificationSettings]):
    def __init__(self):
        super().__init__(StaffNotificationSettings)

    async def get_by_guild_id(self, session: AsyncSession, guild_id: str) -> Optional[StaffNotificationSettings]:
        query = select(StaffNotificationSettings).where(StaffNotificationSettings.guild_id == guild_id)
        result = await session.exec(query)
        return result.one_or_none()

    async def create_or_update(self, session: AsyncSession, guild_id: str, values: dict) -> StaffNotificationSettings:
        existing = await self.get_by_guild_id(session, guild_id)
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            return await self.update(session, existing)
        payload = {**values, 'guild_id': guild_id}
        return await self.create(session, payload)


class StaffEventRepository(BaseRepository[StaffEvent]):
    def __init__(self):
        super().__init__(StaffEvent)

    async def list_by_guild_id(self, session: AsyncSession, guild_id: str, limit: int = 50) -> Sequence[StaffEvent]:
        query = select(StaffEvent).where(StaffEvent.guild_id == guild_id).order_by(StaffEvent.created_at.desc()).limit(limit)
        result = await session.exec(query)
        return result.all()
