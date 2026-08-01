"""Generic API router for module CRUD operations.

This router exposes reusable CRUD endpoints for any registered module. Each
module defines its own model, schema and service.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db import get_session
from ..auth import require_auth
from ..modules import list_modules, get_module
from ..services.module_service import ModuleServiceError

router = APIRouter()


async def get_db():
    session = get_session()
    try:
        yield session
    finally:
        await session.close()


@router.get('/modules')
async def modules_list():
    return [{"name": module.name, "title": module.title} for module in list_modules()]


@router.get('/modules/{module_name}')
async def module_info(module_name: str):
    module_cls = get_module(module_name)
    if not module_cls:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"name": module_cls.name, "title": module_cls.title}


@router.get('/modules/{module_name}/guilds/{guild_id}', dependencies=[Depends(require_auth)])
async def list_module_items(module_name: str, guild_id: str, session: AsyncSession = Depends(get_db)):
    module_cls = get_module(module_name)
    if not module_cls:
        raise HTTPException(status_code=404, detail="Module not found")
    service = module_cls.get_service()
    return await service.list(session, guild_id)


@router.post('/modules/{module_name}/guilds/{guild_id}', dependencies=[Depends(require_auth)])
async def create_module_item(
    module_name: str,
    guild_id: str,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
):
    module_cls = get_module(module_name)
    if not module_cls:
        raise HTTPException(status_code=404, detail="Module not found")
    service = module_cls.get_service()
    payload['guild_id'] = guild_id
    try:
        return await service.create(session, payload)
    except ModuleServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put('/modules/{module_name}/guilds/{guild_id}/{item_id}', dependencies=[Depends(require_auth)])
async def update_module_item(
    module_name: str,
    guild_id: str,
    item_id: int,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
):
    module_cls = get_module(module_name)
    if not module_cls:
        raise HTTPException(status_code=404, detail="Module not found")
    service = module_cls.get_service()
    payload['guild_id'] = guild_id
    try:
        return await service.update(session, item_id, payload)
    except ModuleServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete('/modules/{module_name}/guilds/{guild_id}/{item_id}', dependencies=[Depends(require_auth)])
async def delete_module_item(module_name: str, guild_id: str, item_id: int, session: AsyncSession = Depends(get_db)):
    module_cls = get_module(module_name)
    if not module_cls:
        raise HTTPException(status_code=404, detail="Module not found")
    service = module_cls.get_service()
    await service.delete(session, item_id)
    return {'ok': True}
