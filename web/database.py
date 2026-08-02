from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from . import config

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(config.DATABASE_URL.replace("sqlite:///", "", 1)) if config.DATABASE_URL.startswith("sqlite:///") else None
if DB_PATH is not None and not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH
if DB_PATH is not None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
