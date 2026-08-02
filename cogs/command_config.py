import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands, tasks
from discord import app_commands
import gspread
from google.oauth2.service_account import Credentials
from utils.authorization import has_bot_administrator_access

class CommandConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = Path(__file__).parent.parent / "database" / "command_config.json"
        self.load_config()

        self.google_service_account_file = self.get_google_service_account_file()
        self.google_sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.google_sheet_name = os.getenv("GOOGLE_COMMAND_CONFIG_SHEET", "CommandConfig")
        self.google_sync_interval = int(os.getenv("GOOGLE_SYNC_INTERVAL", "0") or 0)

        self.google_client = None
        self.google_worksheet = None
        self.last_google_sync = None
        self.load_google_settings()

        # interaction_check is an async registration method in discord.py 2.x
        self.bot.tree.interaction_check = self.command_check
        self.patch_interaction_send_message()

        if self.google_sync_interval > 0:
            self.google_auto_sync.start()

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8-sig') as f:
                self.config = json.load(f)
        else:
            self.config = {"guilds": {}}
            self.save_config()

    def save_config(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8-sig') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_google_service_account_file(self):
        path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
        if not path:
            return None
        return Path(path).expanduser()

    def load_google_settings(self):
        if not self.google_service_account_file or not self.google_sheet_id:
            return

        if not self.google_service_account_file.exists():
            print(f"⚠️ Fichier de service Google introuvable: {self.google_service_account_file}")
            return

        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            credentials = Credentials.from_service_account_file(str(self.google_service_account_file), scopes=scopes)
            self.google_client = gspread.authorize(credentials)
            self.google_worksheet = self.google_client.open_by_key(self.google_sheet_id).worksheet(self.google_sheet_name)
            print(f"✅ Google Sheets connecté: {self.google_sheet_id} / {self.google_sheet_name}")
        except Exception as e:
            print(f"⚠️ Impossible de charger Google Sheets: {e}")
            self.google_client = None
            self.google_worksheet = None

    def get_guild_config_by_id(self, guild_id: str):
        return self.config.setdefault("guilds", {}).setdefault(str(guild_id), {"commands": {}})

    def get_guild_config(self, guild: discord.Guild):
        if guild is None:
            return {}
        return self.get_guild_config_by_id(str(guild.id))

    def get_command_settings_by_guild_config(self, guild_config: dict, command_name: str):
        return guild_config["commands"].setdefault(command_name, {
            "enabled": True,
            "required_role": None,
            "required_channel": None,
            "visibility": "public"
        })

    def get_command_settings(self, guild: discord.Guild, command_name: str):
        guild_config = self.get_guild_config(guild)
        return self.get_command_settings_by_guild_config(guild_config, command_name)

    def get_command_settings_by_guild_id(self, guild_id: str, command_name: str):
        guild_config = self.get_guild_config_by_id(guild_id)
        return self.get_command_settings_by_guild_config(guild_config, command_name)

    def parse_google_bool(self, value):
        return str(value).strip().lower() in ("1", "true", "oui", "yes")

    def parse_google_int(self, value):
        try:
            return int(str(value).strip())
        except (ValueError, TypeError):
            return None

    async def sync_from_google(self):
        if not self.google_worksheet:
            return False

        try:
            rows = await asyncio.to_thread(self.google_worksheet.get_all_values)
            if not rows or len(rows) < 2:
                return False

            header = [cell.strip().lower() for cell in rows[0]]
            expected = ["guild_id", "command_name", "enabled", "required_role", "required_channel", "visibility"]
            if not all(column in header for column in expected):
                return False

            changed = False
            for row in rows[1:]:
                data = {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
                guild_id = str(data.get("guild_id", "")).strip()
                command_name = str(data.get("command_name", "")).strip()
                if not guild_id or not command_name:
                    continue

                enabled = self.parse_google_bool(data.get("enabled", "true"))
                required_role = self.parse_google_int(data.get("required_role", ""))
                required_channel = self.parse_google_int(data.get("required_channel", ""))

                settings = self.get_command_settings_by_guild_id(guild_id, command_name)
                if (settings.get("enabled", True) != enabled or
                    settings.get("required_role") != required_role or
                    settings.get("required_channel") != required_channel):
                    settings["enabled"] = enabled
                    settings["required_role"] = required_role
                    settings["required_channel"] = required_channel
                    changed = True

            if changed:
                self.save_config()
                self.last_google_sync = datetime.utcnow()
            return changed
        except Exception as e:
            print(f"⚠️ Échec de la synchronisation Google: {e}")
            return False

    async def sync_to_google(self):
        if not self.google_worksheet:
            return False

        try:
            header = [["guild_id", "command_name", "enabled", "required_role", "required_channel", "visibility"]]
            rows = []
            for guild_id, guild_config in self.config.get("guilds", {}).items():
                for command_name, settings in guild_config.get("commands", {}).items():
                    rows.append([
                        guild_id,
                        command_name,
                        "TRUE" if settings.get("enabled", True) else "FALSE",
                        settings.get("required_role") or "",
                        settings.get("required_channel") or "",
                        settings.get("visibility", "public")
                    ])

            await asyncio.to_thread(self.google_worksheet.clear)
            await asyncio.to_thread(self.google_worksheet.update, "A1", header + rows)
            self.last_google_sync = datetime.utcnow()
            return True
        except Exception as e:
            print(f"⚠️ Échec de l'export Google: {e}")
            return False

    @tasks.loop(minutes=1.0)
    async def google_auto_sync(self):
        if self.google_sync_interval <= 0:
            return

        self.google_auto_sync.change_interval(minutes=self.google_sync_interval)
        await self.sync_from_google()

    @google_auto_sync.before_loop
    async def before_google_auto_sync(self):
        await self.bot.wait_until_ready()

    def set_command_setting(self, guild: discord.Guild, command_name: str, key: str, value):
        settings = self.get_command_settings(guild, command_name)
        settings[key] = value
        self.save_config()

    def is_private_command(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not interaction.command:
            return False
        settings = self.get_command_settings(interaction.guild, interaction.command.name)
        return settings.get("visibility", "public") == "private"

    async def register_interaction_check(self):
        try:
            await self.bot.tree.interaction_check(self.command_check)
        except Exception as e:
            print(f"⚠️ Impossible d'enregistrer interaction_check: {e}")

    async def command_name_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        query = current.casefold().lstrip("/")
        command_names = sorted(
            {command.name for command in self.bot.tree.get_commands()}
        )
        return [
            app_commands.Choice(name=f"/{name}", value=name)
            for name in command_names
            if query in name.casefold()
        ][:25]

    def patch_interaction_send_message(self):
        if getattr(CommandConfig, "_interaction_response_patched", False):
            return

        original_send_message = discord.InteractionResponse.send_message

        async def patched_send_message(response, *args, **kwargs):
            interaction = getattr(response, "interaction", None)
            if interaction and self.is_private_command(interaction):
                kwargs.setdefault("ephemeral", True)
            return await original_send_message(response, *args, **kwargs)

        discord.InteractionResponse.send_message = patched_send_message
        CommandConfig._interaction_response_patched = True

    async def command_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return True

        if not interaction.command:
            return True

        if has_bot_administrator_access(interaction):
            return True

        command_name = interaction.command.name
        settings = self.get_command_settings(interaction.guild, command_name)

        if not settings.get("enabled", True):
            raise app_commands.CheckFailure("Cette commande est désactivée sur ce serveur.")

        required_role_id = settings.get("required_role")
        if required_role_id:
            if not interaction.user.get_role(required_role_id):
                raise app_commands.CheckFailure("Vous n'avez pas le rôle requis pour utiliser cette commande.")

        required_channel_id = settings.get("required_channel")
        if required_channel_id:
            if interaction.channel.id != required_channel_id:
                raise app_commands.CheckFailure("Cette commande ne peut être utilisée que dans le canal configuré.")

        return True

    async def send_status_embed(self, interaction: discord.Interaction, command_name: str):
        settings = self.get_command_settings(interaction.guild, command_name)
        embed = discord.Embed(
            title=f"⚙️ Configuration de la commande /{command_name}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Activée", value="✅ Oui" if settings.get("enabled", True) else "❌ Non", inline=True)
        role = settings.get("required_role")
        channel = settings.get("required_channel")
        visibility = settings.get("visibility", "public")
        embed.add_field(name="Rôle requis", value=f"<@&{role}>" if role else "Aucun", inline=True)
        embed.add_field(name="Canal requis", value=f"<#{channel}>" if channel else "Aucun", inline=True)
        embed.add_field(name="Visibilité", value="Public" if visibility == "public" else "Privé", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="command-config", description="⚙️ Configurer une commande")
    @app_commands.describe(command="La commande à configurer")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_config(self, interaction: discord.Interaction, command: str):
        await self.send_status_embed(interaction, command)

    @app_commands.command(name="command-sync-google", description="🔄 Synchroniser les commandes depuis Google Sheets")
    async def command_sync_google(self, interaction: discord.Interaction):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        if not self.google_worksheet:
            await interaction.response.send_message("⚠️ Google Sheets non configuré.", ephemeral=True)
            return
        changed = await self.sync_from_google()
        message = "✅ Synchronisation Google effectuée."
        if changed:
            message += " Des modifications ont été appliquées."
        else:
            message += " Aucun changement détecté."
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name="command-export-google", description="⬆️ Exporter les commandes vers Google Sheets")
    async def command_export_google(self, interaction: discord.Interaction):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        if not self.google_worksheet:
            await interaction.response.send_message("⚠️ Google Sheets non configuré.", ephemeral=True)
            return
        success = await self.sync_to_google()
        if success:
            await interaction.response.send_message("✅ Export vers Google Sheets terminé.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Échec de l'export vers Google Sheets.", ephemeral=True)

    @app_commands.command(name="command-disable", description="❌ Désactiver une commande")
    @app_commands.describe(command="La commande à désactiver")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_disable(self, interaction: discord.Interaction, command: str):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "enabled", False)
        await interaction.response.send_message(f"✅ Commande `/{command}` désactivée.")

    @app_commands.command(name="command-enable", description="✅ Réactiver une commande")
    @app_commands.describe(command="La commande à réactiver")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_enable(self, interaction: discord.Interaction, command: str):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "enabled", True)
        await interaction.response.send_message(f"✅ Commande `/{command}` activée.")

    @app_commands.command(name="command-set-role", description="🔒 Restreindre une commande à un rôle")
    @app_commands.describe(command="La commande à configurer", role="Le rôle requis")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_set_role(self, interaction: discord.Interaction, command: str, role: discord.Role):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "required_role", role.id)
        await interaction.response.send_message(f"✅ Commande `/{command}` limitée au rôle {role.mention}.")

    @app_commands.command(name="command-clear-role", description="🧹 Retirer la restriction de rôle d'une commande")
    @app_commands.describe(command="La commande à configurer")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_clear_role(self, interaction: discord.Interaction, command: str):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "required_role", None)
        await interaction.response.send_message(f"✅ Rôle requis retiré pour la commande `/{command}`.")

    @app_commands.command(name="command-set-channel", description="📍 Restreindre une commande à un canal")
    @app_commands.describe(command="La commande à configurer", channel="Le canal autorisé")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_set_channel(self, interaction: discord.Interaction, command: str, channel: discord.TextChannel):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "required_channel", channel.id)
        await interaction.response.send_message(f"✅ Commande `/{command}` limitée au canal {channel.mention}.")

    @app_commands.command(name="command-clear-channel", description="🧹 Retirer la restriction de canal d'une commande")
    @app_commands.describe(command="La commande à configurer")
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_clear_channel(self, interaction: discord.Interaction, command: str):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "required_channel", None)
        await interaction.response.send_message(f"✅ Canal requis retiré pour la commande `/{command}`.")

    @app_commands.command(name="command-set-visibility", description="👁️ Choisir si les autres voient la commande")
    @app_commands.describe(command="La commande à configurer", visibility="Public ou privé")
    @app_commands.choices(visibility=[
        app_commands.Choice(name="Public", value="public"),
        app_commands.Choice(name="Privé", value="private")
    ])
    @app_commands.autocomplete(command=command_name_autocomplete)
    async def command_set_visibility(self, interaction: discord.Interaction, command: str, visibility: app_commands.Choice[str]):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous devez être administrateur.", ephemeral=True)
            return
        self.set_command_setting(interaction.guild, command, "visibility", visibility.value)
        await interaction.response.send_message(f"✅ Visibilité de la commande `/{command}` définie sur **{visibility.name}**.")

    @app_commands.command(name="command-list", description="📋 Lister toutes les configurations de commandes")
    async def command_list(self, interaction: discord.Interaction):
        guild_config = self.get_guild_config(interaction.guild)
        commands_config = guild_config.get("commands", {})
        if not commands_config:
            await interaction.response.send_message("Aucune commande configurée pour ce serveur.", ephemeral=True)
            return
        embed = discord.Embed(
            title="📋 Configuration des commandes",
            color=discord.Color.blue()
        )
        for command_name, settings in commands_config.items():
            enabled = "✅" if settings.get("enabled", True) else "❌"
            role = f"<@&{settings['required_role']}>" if settings.get("required_role") else "Aucun"
            channel = f"<#{settings['required_channel']}>" if settings.get("required_channel") else "Aucun"
            visibility = settings.get("visibility", "public")
            embed.add_field(
                name=f"/{command_name}",
                value=(f"Activée: {enabled}\n"
                       f"Rôle: {role}\n"
                       f"Canal: {channel}\n"
                       f"Visibilité: {'Public' if visibility == 'public' else 'Privé'}"),
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandConfig(bot))
