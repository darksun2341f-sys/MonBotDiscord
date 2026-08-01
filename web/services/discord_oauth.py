"""Utilities for Discord OAuth2 and guild filtering.

Provides async helpers to build the authorize URL, exchange codes, fetch user
and guilds, and filter guilds where the bot is present and the user has the
required permissions (Administrator or Manage Guild).
"""
from typing import Dict, List, Optional
import os
import secrets
import asyncio
import httpx
from .. import config

DISCORD_API_BASE = "https://discord.com/api"
TOKEN_URL = f"{DISCORD_API_BASE}/oauth2/token"
USER_URL = f"{DISCORD_API_BASE}/users/@me"
USER_GUILDS_URL = f"{DISCORD_API_BASE}/users/@me/guilds"

ADMIN_BIT = 1 << 3  # 8
MANAGE_GUILD_BIT = 1 << 5  # 32


def generate_state() -> str:
    return secrets.token_urlsafe(16)


def build_authorize_url(state: str, prompt: Optional[str] = None) -> str:
    params = {
        "client_id": config.DISCORD_CLIENT_ID,
        "redirect_uri": config.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    }
    if prompt:
        params["prompt"] = prompt
    qs = "&".join(f"{k}={httpx.utils.quote(str(v))}" for k, v in params.items() if v)
    return f"https://discord.com/api/oauth2/authorize?{qs}"


async def exchange_code(code: str) -> Dict:
    """Exchange authorization code for access token (async HTTPX)."""
    data = {
        "client_id": config.DISCORD_CLIENT_ID,
        "client_secret": config.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def refresh_token(refresh_token: str) -> Dict:
    data = {
        "client_id": config.DISCORD_CLIENT_ID,
        "client_secret": config.DISCORD_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": config.DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_user(access_token: str) -> Dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(USER_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def get_user_guilds(access_token: str) -> List[Dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(USER_GUILDS_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def bot_is_in_guild(guild_id: str, client: httpx.AsyncClient) -> bool:
    """Check if the bot is present in a guild by querying the guild member endpoint.

    Requires `DISCORD_BOT_TOKEN` and `DISCORD_CLIENT_ID` to be set in config.
    Returns True if the bot is found (status 200), False otherwise.
    """
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    bot_id = config.DISCORD_BOT_ID
    if not bot_token or not bot_id:
        return False
    url = f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{bot_id}"
    headers = {"Authorization": f"Bot {bot_token}"}
    try:
        resp = await client.get(url, headers=headers, timeout=8.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def filter_guilds_with_bot_and_perms(access_token: str) -> List[Dict]:
    """Return guilds where the user has admin/manage permissions AND the bot is present.

    This performs the minimal required API calls and is safe for production with
    basic concurrency control.
    """
    guilds = await get_user_guilds(access_token)
    # Filter by permissions first (fast)
    eligible = []
    for g in guilds:
        try:
            perms = int(g.get("permissions", "0"))
        except (ValueError, TypeError):
            perms = 0
        if perms & (ADMIN_BIT | MANAGE_GUILD_BIT):
            eligible.append({"id": g["id"], "name": g["name"], "icon": g.get("icon"), "permissions": perms})

    # If no bot token, return none (we must ensure bot presence requirement)
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    bot_id = config.DISCORD_CLIENT_ID
    if not bot_token or not bot_id:
        # Can't verify bot presence; return empty list to be safe
        return []

    results = []
    sem = asyncio.Semaphore(10)
    async with httpx.AsyncClient() as client:
        async def check(g):
            async with sem:
                present = await bot_is_in_guild(g["id"], client)
                if present:
                    results.append(g)
        await asyncio.gather(*(check(g) for g in eligible))
    # Sort by name
    results.sort(key=lambda x: x["name"].lower())
    return results
