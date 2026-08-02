"""Utilities for Discord OAuth2 and guild filtering."""
from __future__ import annotations

import base64
import secrets
from typing import Any

import httpx

from .. import config


class DiscordOAuthError(RuntimeError):
    pass


def generate_state() -> str:
    return secrets.token_urlsafe(16)


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": config.DISCORD_CLIENT_ID,
        "redirect_uri": config.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    }
    return "https://discord.com/api/oauth2/authorize?" + "&".join(f"{k}={v}" for k, v in params.items())


async def exchange_code(code: str) -> dict[str, Any]:
    if not config.DISCORD_CLIENT_ID or not config.DISCORD_CLIENT_SECRET:
        raise DiscordOAuthError("Discord OAuth is not configured.")

    auth_header = base64.b64encode(f"{config.DISCORD_CLIENT_ID}:{config.DISCORD_CLIENT_SECRET}".encode()).decode()
    data = {
        "client_id": config.DISCORD_CLIENT_ID,
        "client_secret": config.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.DISCORD_REDIRECT_URI,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://discord.com/api/oauth2/token",
            data=data,
            headers={"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_user_data(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_user_guilds(access_token: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        guilds = response.json()

    admin_guilds = []
    for guild in guilds:
        permissions = int(guild.get("permissions", 0))
        if permissions & 0x8:
            admin_guilds.append(guild)
    return admin_guilds
