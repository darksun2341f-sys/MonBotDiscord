from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from . import config
from .database import init_db
from .routers import auth, settings

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MonBotDiscord Dashboard", version="1.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(auth.router)
app.include_router(settings.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    user = request.session.get("user_name")
    guilds = request.session.get("guilds", [])
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "user": user,
            "guilds": guilds,
            "oauth_enabled": bool(config.DISCORD_CLIENT_ID and config.DISCORD_CLIENT_SECRET),
            "admin_login_enabled": bool(config.ADMIN_LOGIN_ENABLED),
        },
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, guild: str | None = None) -> HTMLResponse:
    if not request.session.get("user_name"):
        return RedirectResponse(url="/", status_code=302)

    if guild:
        request.session["selected_guild_id"] = guild

    guilds = request.session.get("guilds", [])
    selected_guild_id = request.session.get("selected_guild_id")
    selected_guild = next((guild for guild in guilds if str(guild.get("id")) == str(selected_guild_id)), guilds[0] if guilds else None)
    return TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "user": request.session.get("user_name"),
            "guilds": guilds,
            "selected_guild": selected_guild,
        },
    )
