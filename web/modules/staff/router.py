from pathlib import Path
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from web.auth import require_auth
from web.db import get_session
from .service import StaffService
from .notifier import staff_notifier

router = APIRouter(tags=['modules', 'staff'], dependencies=[Depends(require_auth)])
ui_router = APIRouter()

base_dir = Path(__file__).resolve().parent
shared_templates = base_dir.parent.parent / 'templates'
templates = Jinja2Templates(directory=[str(base_dir / 'templates'), str(shared_templates)])
service = StaffService()


async def get_db():
    session = get_session()
    try:
        yield session
    finally:
        await session.close()


from .schemas import (
    StaffMemberRead,
    StaffOverviewRead,
    StaffNotificationSettingsRead,
    StaffNotificationSettingsCreate,
    StaffNotificationSettingsUpdate,
    StaffEventRead,
)


@router.get('/guilds/{guild_id}', response_model=list[StaffMemberRead])
async def list_staff_members(guild_id: str, session: AsyncSession = Depends(get_db)):
    return await service.list_members(session, guild_id)


@router.get('/guilds/{guild_id}/overview', response_model=StaffOverviewRead)
async def get_staff_overview(guild_id: str, session: AsyncSession = Depends(get_db)):
    return await service.get_overview(session, guild_id)


@router.get('/guilds/{guild_id}/settings', response_model=StaffNotificationSettingsRead)
async def get_staff_settings(guild_id: str, session: AsyncSession = Depends(get_db)):
    settings = await service.get_settings(session, guild_id)
    if settings is None:
        raise HTTPException(status_code=404, detail='Staff notification settings not found')
    return settings


@router.post('/guilds/{guild_id}/settings', response_model=StaffNotificationSettingsRead)
async def create_staff_settings(guild_id: str, payload: StaffNotificationSettingsCreate, session: AsyncSession = Depends(get_db)):
    return await service.create_or_update_settings(session, guild_id, payload.dict(exclude_unset=True))


@router.put('/guilds/{guild_id}/settings/{item_id}', response_model=StaffNotificationSettingsRead)
async def update_staff_settings(guild_id: str, item_id: int, payload: StaffNotificationSettingsUpdate, session: AsyncSession = Depends(get_db)):
    existing = await service.get_settings(session, guild_id)
    if existing is None or existing.id != item_id:
        raise HTTPException(status_code=404, detail='Staff notification settings not found')
    return await service.update_settings(session, item_id, payload.dict(exclude_unset=True))


@router.get('/guilds/{guild_id}/events', response_model=list[StaffEventRead])
async def list_staff_events(guild_id: str, session: AsyncSession = Depends(get_db)):
    return await service.list_events(session, guild_id)


@router.post('/guilds/{guild_id}/broadcast')
async def broadcast_staff_update(guild_id: str, session: AsyncSession = Depends(get_db)):
    members = await service.list_members(session, guild_id)
    overview = await service.get_overview(session, guild_id)
    await staff_notifier.broadcast(guild_id, {
        'type': 'staff.update',
        'members': [member.dict() for member in members],
        'overview': overview.dict(),
    })
    return {'ok': True}


@ui_router.get('/dashboard/staff/{guild_id}', response_class=HTMLResponse)
async def staff_dashboard(request: Request, guild_id: str):
    if not request.session.get('authed'):
        return RedirectResponse(url='/auth/login')
    return templates.TemplateResponse('staff.html', {'request': request, 'guild_id': guild_id})


@ui_router.websocket('/ws/modules/staff/{guild_id}')
async def staff_dashboard_ws(websocket: WebSocket, guild_id: str):
    await websocket.accept()
    session = websocket.scope.get('session', {})
    if not session or not session.get('authed'):
        await websocket.close(code=4401)
        return

    await staff_notifier.connect(guild_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await staff_notifier.disconnect(guild_id, websocket)
