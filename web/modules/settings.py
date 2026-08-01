"""Shared settings models for feature modules."""
from pydantic import BaseModel, Field
from typing import Optional


class BaseModuleSettings(BaseModel):
    enabled: bool = Field(True, description="Whether the module is enabled")
    description: Optional[str] = Field(None, description="Human-readable description for the module")


class WelcomeModuleSettings(BaseModuleSettings):
    welcome_channel: Optional[str] = Field(None, description="Default welcome channel ID")
