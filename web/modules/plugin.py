"""Plugin loader for dashboard feature modules."""
import importlib
import pkgutil
from pathlib import Path
from typing import Iterator, List
from .base import ModuleConfig


def discover_plugins(package_name: str, package_path: Path) -> Iterator[str]:
    """Discover plugin module names inside a package."""
    for finder, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        if name.startswith("_"):
            continue
        yield f"{package_name}.{name}"


def load_plugins(package_name: str, package_path: Path) -> List[ModuleConfig]:
    """Import plugin modules and return registered module classes."""
    for module_name in discover_plugins(package_name, package_path):
        importlib.import_module(module_name)
    from .registry import list_modules
    return list_modules()
