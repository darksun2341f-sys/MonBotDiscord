"""Welcome module persistence models."""
from typing import Optional
from sqlmodel import SQLModel, Field


class WelcomeConfig(SQLModel, table=True):
    """Persistent welcome settings for a single guild."""
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: str = Field(index=True, unique=True, description="Guild ID for this welcome configuration")
    channel_id: Optional[str] = Field(None, description="Discord channel ID used for welcome messages")
    message: Optional[str] = Field(None, description="Welcome message text")
    enabled: bool = Field(True, description="Whether welcome messages are enabled")
