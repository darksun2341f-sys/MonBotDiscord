"""Base abstractions for dashboard modules.

Every feature module should implement a ModuleConfig that exposes:
- a unique module name
- a Pydantic settings schema
- SQLModel tables for persistence
- a CRUD service for read/write operations
- API routers for its domain
"""
from abc import ABC, abstractmethod
from sqlmodel import SQLModel
from pydantic import BaseModel
from fastapi import APIRouter
from typing import Type

class ModuleSettings(BaseModel):
    """Common shared settings for module configuration."""
    enabled: bool = True

class ModuleConfig(ABC):
    name: str
    title: str
    model: Type[SQLModel]
    schema_create: Type[BaseModel] | None = None
    schema_update: Type[BaseModel] | None = None
    schema_read: Type[BaseModel] | None = None

    @classmethod
    def get_router(cls) -> APIRouter:
        """Return a generic router for this module.

        Subclasses can override this if they need custom routes.
        """
        from .router import ModuleRouter

        return ModuleRouter(cls).router

    @classmethod
    @abstractmethod
    def get_service(cls):
        raise NotImplementedError

    @classmethod
    def get_models(cls) -> list[Type[SQLModel]]:
        """Return the SQLModel classes required by this module."""
        return [cls.model]

    @classmethod
    def get_api_prefix(cls) -> str:
        """Return the API prefix used by the module router."""
        return f"/api/modules/{cls.name}"

    @classmethod
    def get_tags(cls) -> list[str]:
        return ["modules", cls.name]

    @classmethod
    def register(cls):
        from . import register_module
        return register_module(cls)


ModuleBase = ModuleConfig
