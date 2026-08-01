from datetime import datetime
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from .repository import (
    StaffRepository,
    StaffStatsRepository,
    StaffNotificationSettingsRepository,
    StaffEventRepository,
)
from .schemas import (
    StaffMemberCreate,
    StaffMemberRead,
    StaffMemberUpdate,
    StaffOverviewRead,
    StaffStatsRead,
    StaffNotificationSettingsCreate,
    StaffNotificationSettingsUpdate,
    StaffNotificationSettingsRead,
    StaffEventRead,
)
from .models import StaffMember, StaffStats, StaffNotificationSettings, StaffEvent
from ..base import ModuleConfig


class StaffService:
    def __init__(self):
        self.repository = StaffRepository()
        self.stats_repository = StaffStatsRepository()
        self.settings_repository = StaffNotificationSettingsRepository()
        self.event_repository = StaffEventRepository()

    async def list_members(self, session: AsyncSession, guild_id: str) -> list[StaffMemberRead]:
        members = await self.repository.list_by_guild(session, guild_id)
        member_ids = [member.id for member in members if member.id is not None]
        stats = await self.stats_repository.list_by_member_ids(session, member_ids)
        stats_by_member = {stat.member_id: stat for stat in stats}

        results: list[StaffMemberRead] = []
        for member in members:
            stats_item = stats_by_member.get(member.id)
            stats_dict = StaffStatsRead(
                voice_minutes=stats_item.voice_minutes if stats_item else 0,
                tickets_handled=stats_item.tickets_handled if stats_item else 0,
                moderation_actions=stats_item.moderation_actions if stats_item else 0,
                warns=stats_item.warns if stats_item else 0,
                messages_sent=stats_item.messages_sent if stats_item else 0,
                xp=stats_item.xp if stats_item else 0,
                level=stats_item.level if stats_item else 1,
                ratings_total=stats_item.ratings_total if stats_item else 0,
                ratings_count=stats_item.ratings_count if stats_item else 0,
                average_rating=stats_item.average_rating if stats_item else 0.0,
            )
            results.append(StaffMemberRead.from_orm(member).copy(update={'stats': stats_dict}))
        return results

    async def get_overview(self, session: AsyncSession, guild_id: str) -> StaffOverviewRead:
        members = await self.repository.list_by_guild(session, guild_id)
        member_ids = [member.id for member in members if member.id is not None]
        stats = await self.stats_repository.list_by_member_ids(session, member_ids)

        overview = StaffOverviewRead()
        overview.total_members = len(members)
        total_rating = 0
        total_count = 0
        for member in members:
            if member.category:
                overview.categories[member.category] = overview.categories.get(member.category, 0) + 1

        for stat in stats:
            overview.total_voice_minutes += stat.voice_minutes
            overview.total_tickets += stat.tickets_handled
            overview.total_moderation_actions += stat.moderation_actions
            overview.total_warns += stat.warns
            overview.total_messages += stat.messages_sent
            total_rating += stat.ratings_total
            total_count += stat.ratings_count

        overview.average_rating = round(total_rating / total_count, 2) if total_count > 0 else 0.0
        return overview

    async def get_settings(self, session: AsyncSession, guild_id: str) -> Optional[StaffNotificationSettingsRead]:
        settings = await self.settings_repository.get_by_guild_id(session, guild_id)
        if not settings:
            return None
        return StaffNotificationSettingsRead.from_orm(settings)

    async def create_or_update_settings(
        self,
        session: AsyncSession,
        guild_id: str,
        payload: dict,
    ) -> StaffNotificationSettingsRead:
        data = StaffNotificationSettingsCreate(**payload)
        settings = await self.settings_repository.create_or_update(session, guild_id, data.dict(exclude_unset=True))
        return StaffNotificationSettingsRead.from_orm(settings)

    async def update_settings(
        self,
        session: AsyncSession,
        item_id: int,
        payload: dict,
    ) -> StaffNotificationSettingsRead:
        existing = await self.settings_repository.get(session, item_id)
        if not existing:
            return None
        data = StaffNotificationSettingsUpdate(**{**existing.dict(), **payload})
        for key, value in data.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        settings = await self.settings_repository.update(session, existing)
        return StaffNotificationSettingsRead.from_orm(settings)

    async def list_events(self, session: AsyncSession, guild_id: str, limit: int = 50) -> list[StaffEventRead]:
        events = await self.event_repository.list_by_guild_id(session, guild_id, limit=limit)
        return [StaffEventRead.from_orm(event) for event in events]

    async def log_event(self, session: AsyncSession, payload: dict) -> StaffEventRead:
        event = await self.event_repository.create(session, payload)
        return StaffEventRead.from_orm(event)

    async def get_member(self, session: AsyncSession, member_id: int) -> Optional[StaffMemberRead]:
        member = await self.repository.get(session, member_id)
        if not member:
            return None
        stats = await self.stats_repository.get_by_member(session, member.id)
        stats_item = StaffStatsRead(
            voice_minutes=stats.voice_minutes if stats else 0,
            tickets_handled=stats.tickets_handled if stats else 0,
            moderation_actions=stats.moderation_actions if stats else 0,
            warns=stats.warns if stats else 0,
            messages_sent=stats.messages_sent if stats else 0,
            xp=stats.xp if stats else 0,
            level=stats.level if stats else 1,
            ratings_total=stats.ratings_total if stats else 0,
            ratings_count=stats.ratings_count if stats else 0,
            average_rating=stats.average_rating if stats else 0.0,
        )
        return StaffMemberRead.from_orm(member).copy(update={'stats': stats_item})
