"""Shared service and validation logic for dashboard modules."""
from typing import Type
from pydantic import BaseModel, ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

class ModuleServiceError(Exception):
    pass

class ModuleService:
    """Base service to manage module CRUD and validation."""
    def __init__(self, repository, schema_create: Type[BaseModel], schema_update: Type[BaseModel] | None = None):
        self.repository = repository
        self.schema_create = schema_create
        self.schema_update = schema_update or schema_create

    async def list(self, session: AsyncSession, guild_id: str):
        return await self.repository.list(session, guild_id)

    async def get(self, session: AsyncSession, item_id: int):
        return await self.repository.get(session, item_id)

    async def create(self, session: AsyncSession, payload: dict):
        try:
            data = self.schema_create(**payload)
        except ValidationError as exc:
            raise ModuleServiceError(exc.json()) from exc
        return await self.repository.create(session, data)

    async def update(self, session: AsyncSession, item_id: int, payload: dict):
        existing = await self.repository.get(session, item_id)
        if not existing:
            raise ModuleServiceError("Item not found")
        try:
            data = self.schema_update(**{**existing.dict(), **payload})
        except ValidationError as exc:
            raise ModuleServiceError(exc.json()) from exc
        for key, value in data.dict().items():
            setattr(existing, key, value)
        return await self.repository.update(session, existing)

    async def delete(self, session: AsyncSession, item_id: int):
        existing = await self.repository.get(session, item_id)
        if not existing:
            raise ModuleServiceError("Item not found")
        await self.repository.delete(session, existing)
        return None
