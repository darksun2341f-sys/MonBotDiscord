"""API router for the welcome module."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel.ext.asyncio.session import AsyncSession
from ...auth import require_auth
from ...db import get_session
from .service import WelcomeService
from .schemas import WelcomeConfigCreate, WelcomeConfigUpdate, WelcomeConfigRead

router = APIRouter(tags=['modules', 'welcome'], dependencies=[Depends(require_auth)])
service = WelcomeService()


async def get_db():
    session = get_session()
    try:
        yield session
    finally:
        await session.close()


@router.get('/guilds/{guild_id}', response_model=List[WelcomeConfigRead])
async def list_welcome_settings(guild_id: str, session: AsyncSession = Depends(get_db)):
    return await service.list(session, guild_id)


@router.post('/guilds/{guild_id}', response_model=WelcomeConfigRead)
async def create_welcome_settings(
    guild_id: str,
    payload: WelcomeConfigCreate,
    session: AsyncSession = Depends(get_db),
):
    return await service.create_or_update(session, guild_id, payload.dict(exclude_unset=True))


@router.put('/guilds/{guild_id}/{item_id}', response_model=WelcomeConfigRead)
async def update_welcome_settings(
    guild_id: str,
    item_id: int,
    payload: WelcomeConfigUpdate,
    session: AsyncSession = Depends(get_db),
):
    payload_data = payload.dict(exclude_unset=True)
    existing = await service.get(session, item_id)
    if not existing or existing.guild_id != guild_id:
        raise HTTPException(status_code=404, detail='Welcome settings not found')
    return await service.update(session, item_id, {**payload_data, 'guild_id': guild_id})


@router.delete('/guilds/{guild_id}/{item_id}')
async def delete_welcome_settings(guild_id: str, item_id: int, session: AsyncSession = Depends(get_db)):
    existing = await service.get(session, item_id)
    if not existing or existing.guild_id != guild_id:
        raise HTTPException(status_code=404, detail='Welcome settings not found')
    await service.delete(session, item_id)
    return {'ok': True}
