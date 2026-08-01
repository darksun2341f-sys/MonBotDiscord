"""Pydantic schemas for the Welcome module."""
from typing import Optional
from pydantic import BaseModel, Field


class WelcomeConfigCreate(BaseModel):
    """Payload used to create welcome settings for a guild."""
    channel_id: Optional[str] = Field(None, description="Discord channel ID used for welcome messages")
    message: Optional[str] = Field(None, description="Message sent when a new user joins")
    enabled: bool = Field(True, description="Whether welcome messages are enabled")


class WelcomeConfigUpdate(BaseModel):
    """Payload used to update existing welcome settings."""
    channel_id: Optional[str] = Field(None, description="Discord channel ID used for welcome messages")
    message: Optional[str] = Field(None, description="Message sent when a new user joins")
    enabled: Optional[bool] = Field(None, description="Whether welcome messages are enabled")


class WelcomeConfigRead(BaseModel):
    """Response model returned to clients for welcome settings."""
    id: int
    guild_id: str
    channel_id: Optional[str]
    message: Optional[str]
    enabled: bool

    class Config:
        orm_mode = True
