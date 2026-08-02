from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from .. import config
from ..database import get_db
from ..services.dashboard_service import DashboardService
from ..services.discord_oauth import DiscordOAuthError, build_authorize_url, exchange_code, fetch_user_data, fetch_user_guilds, generate_state

router = APIRouter(tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    if not config.DISCORD_CLIENT_ID:
        raise RuntimeError("DISCORD_CLIENT_ID is not configured.")

    state = generate_state()
    request.session["oauth_state"] = state
    authorize_url = build_authorize_url(state)
    return RedirectResponse(authorize_url, status_code=302)


@router.get("/auth/callback")
async def auth_callback(request: Request, code: str | None = None, state: str | None = None) -> RedirectResponse:
    if code is None or state is None:
        return RedirectResponse("/", status_code=302)

    session_state = request.session.get("oauth_state")
    if session_state != state:
        raise RuntimeError("Invalid OAuth state")

    try:
        token_payload = await exchange_code(code)
        access_token = token_payload.get("access_token")
        if not access_token:
            raise DiscordOAuthError("No access token returned by Discord")

        user_payload = await fetch_user_data(access_token)
        guild_payload = await fetch_user_guilds(access_token)

        with next(get_db()) as db:
            user = DashboardService.upsert_user(db, user_payload)
            request.session["user_id"] = user.discord_id
            request.session["user_name"] = user.username
            request.session["avatar"] = user.avatar
            request.session["guilds"] = [{"id": guild["id"], "name": guild["name"], "icon": guild.get("icon")} for guild in guild_payload]
            request.session["selected_guild_id"] = guild_payload[0]["id"] if guild_payload else None

        request.session.pop("oauth_state", None)
    except Exception:
        request.session.clear()
        return RedirectResponse("/", status_code=302)

    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/", status_code=302)
