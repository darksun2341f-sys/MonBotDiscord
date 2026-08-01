"""API package for the dashboard."""
from .health import router as health
from .base import router as base
from .guilds import router as guilds
from .modules import router as modules
from .plugins import router as plugins

__all__ = ["health", "base", "guilds", "modules", "plugins"]
