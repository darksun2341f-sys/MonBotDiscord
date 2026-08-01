"""Core guild model and general metadata for server configuration."""
from typing import Optional
from sqlmodel import SQLModel, Field

class Guild(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: str = Field(index=True, unique=True)
    name: str
    icon: Optional[str] = None
    locale: Optional[str] = None
    created_at: Optional[str] = None


class GuildCreate(SQLModel):
    guild_id: str
    name: str
    icon: Optional[str] = None
    locale: Optional[str] = None
