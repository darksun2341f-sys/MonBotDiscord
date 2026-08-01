"""Service layer for welcome module business logic."""
from typing import Optional
from pydantic import ValidationError
from .repository import WelcomeRepository
from .models import WelcomeConfig
from .schemas import WelcomeConfigCreate, WelcomeConfigUpdate
from ...services.module_service import ModuleService, ModuleServiceError
from sqlmodel.ext.asyncio.session import AsyncSession


class WelcomeService(ModuleService):
    def __init__(self):
        super().__init__(WelcomeRepository(), WelcomeConfigCreate)

    async def get_by_guild_id(self, session: AsyncSession, guild_id: str) -> Optional[WelcomeConfig]:
        return await self.repository.get_by_guild_id(session, guild_id)

    async def create(self, session: AsyncSession, payload: dict) -> WelcomeConfig:
        try:
            data = WelcomeConfigCreate(**payload)
        except ValidationError as exc:
            raise ModuleServiceError(exc.json()) from exc
        return await self.repository.create_or_update(session, payload['guild_id'], data.dict(exclude_unset=True))

    async def update_by_guild_id(self, session: AsyncSession, guild_id: str, payload: dict) -> WelcomeConfig:
        existing = await self.get_by_guild_id(session, guild_id)
        if not existing:
            raise ModuleServiceError("Welcome settings not found")
        try:
            data = WelcomeConfigUpdate(**payload)
        except ValidationError as exc:
            raise ModuleServiceError(exc.json()) from exc
        for key, value in data.dict(exclude_unset=True).items():
            setattr(existing, key, value)
        return await self.repository.update(session, existing)

    async def delete_by_guild_id(self, session: AsyncSession, guild_id: str) -> None:
        existing = await self.get_by_guild_id(session, guild_id)
        if not existing:
            raise ModuleServiceError("Welcome settings not found")
        await self.repository.delete(session, existing)
