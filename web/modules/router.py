"""Generic module route builder for reusable feature modules."""
from typing import Any, Type
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from ..auth import require_auth
from ..db import get_session
from .base import ModuleConfig
from ..services.module_service import ModuleServiceError


async def get_db():
    async with get_session() as session:
        yield session


class ModuleRouter:
    """Builds a generic CRUD router for a feature module."""
    def __init__(self, module_cls: Type[ModuleConfig]):
        self.module_cls = module_cls
        self.router = APIRouter(tags=module_cls.get_tags(), dependencies=[Depends(require_auth)])
        self._register_routes()

    def _register_routes(self) -> None:
        schema_read = self.module_cls.schema_read
        schema_create = self.module_cls.schema_create
        schema_update = self.module_cls.schema_update

        self.router.add_api_route(
            '/guilds/{guild_id}',
            self._list_items,
            methods=['GET'],
            response_model=list[schema_read],
            name=f'{self.module_cls.name}_list',
        )
        self.router.add_api_route(
            '/guilds/{guild_id}/{item_id}',
            self._get_item,
            methods=['GET'],
            response_model=schema_read,
            name=f'{self.module_cls.name}_get',
        )
        self.router.add_api_route(
            '/guilds/{guild_id}',
            self._create_item(schema_create),
            methods=['POST'],
            response_model=schema_read,
            name=f'{self.module_cls.name}_create',
        )
        self.router.add_api_route(
            '/guilds/{guild_id}/{item_id}',
            self._update_item(schema_update),
            methods=['PUT'],
            response_model=schema_read,
            name=f'{self.module_cls.name}_update',
        )
        self.router.add_api_route(
            '/guilds/{guild_id}/{item_id}',
            self._delete_item,
            methods=['DELETE'],
            name=f'{self.module_cls.name}_delete',
        )

    def get_service(self):
        return self.module_cls.get_service()

    async def _list_items(self, guild_id: str, session: AsyncSession = Depends(get_db)):
        return await self.get_service().list(session, guild_id)

    async def _get_item(self, guild_id: str, item_id: int, session: AsyncSession = Depends(get_db)):
        item = await self.get_service().get(session, item_id)
        if not item or getattr(item, 'guild_id', None) != guild_id:
            raise HTTPException(status_code=404, detail='Item not found')
        return item

    def _create_item(self, schema_create: Type[Any]):
        async def endpoint(guild_id: str, payload: schema_create, session: AsyncSession = Depends(get_db)):
            data = payload.dict(exclude_unset=True)
            return await self.get_service().create(session, {**data, 'guild_id': guild_id})
        return endpoint

    def _update_item(self, schema_update: Type[Any]):
        async def endpoint(guild_id: str, item_id: int, payload: schema_update, session: AsyncSession = Depends(get_db)):
            data = payload.dict(exclude_unset=True)
            existing = await self.get_service().get(session, item_id)
            if not existing or getattr(existing, 'guild_id', None) != guild_id:
                raise HTTPException(status_code=404, detail='Item not found')
            try:
                return await self.get_service().update(session, item_id, {**data, 'guild_id': guild_id})
            except ModuleServiceError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        return endpoint

    async def _delete_item(self, guild_id: str, item_id: int, session: AsyncSession = Depends(get_db)):
        existing = await self.get_service().get(session, item_id)
        if not existing or getattr(existing, 'guild_id', None) != guild_id:
            raise HTTPException(status_code=404, detail='Item not found')
        await self.get_service().delete(session, item_id)
        return {'ok': True}
