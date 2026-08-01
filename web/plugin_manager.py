"""Simple plugin manager for loading extension packages at runtime."""
import importlib
import pkgutil
from pathlib import Path
from typing import Iterable

PLUGIN_FOLDER = Path(__file__).parent / 'plugins'


def _iter_plugin_modules() -> Iterable[str]:
    if not PLUGIN_FOLDER.exists():
        return []
    for finder, name, is_pkg in pkgutil.iter_modules([str(PLUGIN_FOLDER)]):
        if name.startswith('_'):
            continue
        yield f'web.plugins.{name}'


def load_plugins() -> None:
    """Load all plugins from the web/plugins folder."""
    for module_name in _iter_plugin_modules():
        importlib.import_module(module_name)
