"""FastAPI application entrypoint for the dashboard.

This module creates the FastAPI app, mounts static files, configures templates,
registers routers and sets up middleware. Keep this file small: app wiring only.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from . import config

# Create app
app = FastAPI(title="MonBotDiscord Dashboard", version="0.1.0")

# Sessions (used for OAuth and simple session auth)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

# Templates: simple Jinja environment wrapper (we'll use render helper in routers)
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# Mount static
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Include routers (health, auth, api)
from .api import health, base as api_base, guilds as api_guilds, plugins as api_plugins
from .api.modules import router as modules_router
from .auth import router as auth_router
from .db import init_db
from .modules.loader import load_modules
from pathlib import Path

app.include_router(health, prefix="/api")
app.include_router(api_base, prefix="/api")
app.include_router(api_guilds, prefix="/api")
app.include_router(api_plugins, prefix="/api")
app.include_router(modules_router, prefix="/api")
app.include_router(auth_router, prefix="")

# Load modules explicitly at import time so routers and models are registered.
loaded_modules = load_modules()
for module_cls in loaded_modules:
    router = module_cls.get_router()
    if router is not None:
        app.include_router(router, prefix=module_cls.get_api_prefix(), tags=module_cls.get_tags())

    if hasattr(module_cls, 'get_ui_router'):
        ui_router = module_cls.get_ui_router()
        if ui_router is not None:
            app.include_router(ui_router, prefix="", tags=module_cls.get_tags())

    if hasattr(module_cls, 'get_static_dir'):
        static_dir = module_cls.get_static_dir()
        if static_dir and Path(static_dir).exists():
            mount_path = f"/static/modules/{module_cls.name}"
            app.mount(mount_path, StaticFiles(directory=str(static_dir)), name=f"static_{module_cls.name}")


@app.on_event("startup")
async def on_startup():
    """Ensure database tables exist before serving requests."""
    await init_db()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Render a simple index page. Real pages will live in dedicated routers."""
    template = jinja_env.get_template("index.html")
    return template.render()
