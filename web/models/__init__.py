"""Database models for dashboard.

Keep models small and focused; each module will add its own models under
`web/models/<module>_models.py` and import them here for migrations.
"""
from sqlmodel import SQLModel, Field
from typing import Optional

class GuildSettings(SQLModel, table=True):
    """Global per-guild settings used by modules (example)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: str
    module_name: str
    key: str
    value: str

# Future: add module-specific models in separate files and import them here.

__all__ = ["GuildSettings", "SQLModel"]
