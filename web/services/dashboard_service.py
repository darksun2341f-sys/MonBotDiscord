from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from ..models import DashboardUser, GuildSetting


class DashboardService:
    @staticmethod
    def upsert_user(db: Session, payload: dict[str, Any]) -> DashboardUser:
        user = db.query(DashboardUser).filter(DashboardUser.discord_id == str(payload["id"])).first()
        if user is None:
            user = DashboardUser(discord_id=str(payload["id"]), username=payload.get("username", "Unknown"))
            db.add(user)
        user.username = payload.get("username", user.username)
        user.avatar = payload.get("avatar")
        user.email = payload.get("email")
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def upsert_guild(db: Session, guild_payload: dict[str, Any], config: dict[str, Any] | None = None) -> GuildSetting:
        guild_id = str(guild_payload["id"])
        guild = db.query(GuildSetting).filter(GuildSetting.guild_id == guild_id).first()
        if guild is None:
            guild = GuildSetting(guild_id=guild_id)
            db.add(guild)
        guild.guild_name = guild_payload.get("name", guild.guild_name)
        guild.icon = guild_payload.get("icon")
        if config is not None:
            guild.config_json = json.dumps(config)
        db.commit()
        db.refresh(guild)
        return guild

    @staticmethod
    def get_guild_config(db: Session, guild_id: str) -> dict[str, Any]:
        guild = db.query(GuildSetting).filter(GuildSetting.guild_id == str(guild_id)).first()
        if not guild:
            return {}
        try:
            return json.loads(guild.config_json or "{}")
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def save_guild_config(db: Session, guild_id: str, config: dict[str, Any]) -> GuildSetting:
        guild = db.query(GuildSetting).filter(GuildSetting.guild_id == str(guild_id)).first()
        if guild is None:
            guild = GuildSetting(guild_id=str(guild_id))
            db.add(guild)
        guild.config_json = json.dumps(config)
        db.commit()
        db.refresh(guild)
        return guild
