"""Sample plugin to demonstrate plugin registration."""
from .base import Plugin, register_plugin


@register_plugin(Plugin(
    name="sample-welcome-ext",
    version="0.1.0",
    description="Example plugin for the dashboard plugin system.",
    author="MonBotDiscord",
))
def plugin():
    return None
