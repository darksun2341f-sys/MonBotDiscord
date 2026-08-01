"""Generic repository helpers for SQLModel-based modules."""
from typing import Generic, TypeVar, Type
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)

class BaseRepository(Generic[ModelType]):
    """Minimal CRUD repository for SQLModel models."""
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: AsyncSession, item_id: int) -> ModelType | None:
        return await session.get(self.model, item_id)

    async def list(self, session: AsyncSession, guild_id: str) -> list[ModelType]:
        query = select(self.model).where(self.model.guild_id == guild_id)
        result = await session.exec(query)
        return result.all()

    async def create(self, session: AsyncSession, item: ModelType | dict) -> ModelType:
        if isinstance(item, dict):
            item = self.model(**item)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    async def update(self, session: AsyncSession, item: ModelType) -> ModelType:
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    async def delete(self, session: AsyncSession, item: ModelType) -> None:
        await session.delete(item)
        await session.commit()
