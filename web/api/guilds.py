"""API routes for guild metadata management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db import get_session
from ..auth import require_auth
from ..services.guild_service import GuildService
from ..models.guild import GuildCreate

router = APIRouter()
service = GuildService()


async def get_db():
    session = get_session()
    try:
        yield session
    finally:
        await session.close()


@router.get('/guilds', dependencies=[Depends(require_auth)])
async def list_guilds(session: AsyncSession = Depends(get_db)):
    return await service.list(session)


@router.post('/guilds', dependencies=[Depends(require_auth)])
async def create_or_update_guild(payload: GuildCreate, session: AsyncSession = Depends(get_db)):
    return await service.create_or_update(session, payload.dict())


@router.get('/guilds/{guild_id}', dependencies=[Depends(require_auth)])
async def get_guild(guild_id: str, session: AsyncSession = Depends(get_db)):
    guild = await service.get_by_guild_id(session, guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail='Guild not found')
    return guild
