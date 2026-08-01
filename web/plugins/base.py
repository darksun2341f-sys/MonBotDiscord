"""Plugin base types and registration helpers."""
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar, overload

plugins: list["Plugin"] = []

F = TypeVar("F", bound=Callable[..., object])


@dataclass
class Plugin:
    name: str
    version: str = "0.1.0"
    description: Optional[str] = None
    author: Optional[str] = None


@overload
def register_plugin(plugin: Plugin) -> Callable[[F], F]:
    ...

@overload
def register_plugin(plugin: F) -> F:
    ...


def register_plugin(plugin):
    """Register a plugin metadata object with the plugin manager.

    This helper supports both direct registration and decorator-style usage.
    """
    if isinstance(plugin, Plugin):
        def decorator(func: F) -> F:
            plugins.append(plugin)
            return func
        return decorator

    plugins.append(plugin)
    return plugin
