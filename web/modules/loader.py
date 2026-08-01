"""Explicit module discovery and loader for dashboard feature modules."""
import importlib
import pkgutil
from pathlib import Path
from typing import Iterator, List, Type

from .base import ModuleConfig
from .registry import list_modules
from ..plugin_manager import load_plugins as load_dashboard_plugins


def discover_modules(package_name: str, package_path: Path) -> Iterator[str]:
    """Discover module packages inside the web.modules package."""
    for finder, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        if name.startswith("_") or name in {"base", "registry", "loader", "settings"}:
            continue
        yield f"{package_name}.{name}"


_loaded = False


def load_modules() -> List[Type[ModuleConfig]]:
    """Load all feature modules and return the registered module classes."""
    global _loaded
    if _loaded:
        return list_modules()

    package_name = __package__
    package_path = Path(__file__).parent

    for module_name in discover_modules(package_name, package_path):
        importlib.import_module(module_name)

    # Load dashboard plugins as part of startup to keep plugin discovery deterministic.
    load_dashboard_plugins()

    _loaded = True
    return list_modules()
