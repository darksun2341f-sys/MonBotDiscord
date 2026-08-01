"""Asynchronous database setup using SQLModel (SQLAlchemy 2.0 style)

We use SQLModel for a developer-friendly declarative approach. Keep DB wiring
separate so migrations and engine configuration remain centralized.
"""
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from typing import Optional
from . import config
from . import models as _models
from .modules.loader import load_modules
DATABASE_URL = config.DATABASE_URL

# If using sqlite file path, convert to aiosqlite URL
if DATABASE_URL.startswith('sqlite:') and not DATABASE_URL.startswith('sqlite+aiosqlite'):
    DATABASE_URL = DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///')

engine: Optional[AsyncEngine] = None
_async_session = None


def set_database_url(database_url: str) -> None:
    """Set a new DATABASE_URL and reset the engine.

    Use this only at startup or in tests before creating sessions.
    """
    global DATABASE_URL
    DATABASE_URL = database_url
    reset_engine()


def reset_engine() -> None:
    """Reset the SQLAlchemy engine and session factory for testing or configuration reload."""
    global engine, _async_session
    engine = None
    _async_session = None


def get_engine() -> AsyncEngine:
    global engine
    if engine is None:
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    return engine


def get_session() -> AsyncSession:
    global _async_session
    if _async_session is None:
        _async_session = sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False, future=True)
    return _async_session()


async def init_db():
    """Create database tables. Call this once at startup or during migrations."""
    load_modules()
    from .modules import list_module_models

    list_module_models()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
