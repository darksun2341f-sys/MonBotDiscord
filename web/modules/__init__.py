"""Module registry for dashboard features.

Each module package registers itself in the `registry` list. The registry is
populated when `load_modules()` is called, keeping discovery explicit and
repeatable.
"""
from typing import List, Type
from sqlmodel import SQLModel
from .base import ModuleConfig

_module_registry: List[Type[ModuleConfig]] = []
_registered_names: set[str] = set()


def register_module(module_cls: Type[ModuleConfig]) -> Type[ModuleConfig]:
    if module_cls.name in _registered_names:
        existing = get_module(module_cls.name)
        if existing is module_cls:
            return module_cls
        raise ValueError(f"Module with name '{module_cls.name}' is already registered")
    _module_registry.append(module_cls)
    _registered_names.add(module_cls.name)
    return module_cls


def get_module(name: str) -> Type[ModuleConfig] | None:
    for module_cls in _module_registry:
        if module_cls.name == name:
            return module_cls
    return None


def list_modules() -> List[Type[ModuleConfig]]:
    return list(_module_registry)


def list_module_models() -> List[Type[SQLModel]]:
    """Return all SQLModel classes registered by modules."""
    models: list[Type[SQLModel]] = []
    for module_cls in list_modules():
        models.extend(module_cls.get_models())
    return models
