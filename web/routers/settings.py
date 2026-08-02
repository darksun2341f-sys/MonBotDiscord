from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..database import get_db
from ..services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/{guild_id}/{section}")
async def save_settings(request: Request, guild_id: str, section: str) -> JSONResponse:
    payload = await request.json()
    if not payload:
        payload = {}

    with next(get_db()) as db:
        config = DashboardService.get_guild_config(db, guild_id)
        config[section] = payload
        DashboardService.save_guild_config(db, guild_id, config)

    return JSONResponse({"ok": True, "guild_id": guild_id, "section": section})
