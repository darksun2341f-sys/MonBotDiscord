import json
from pathlib import Path

import discord
from discord.ext import commands
from discord import app_commands

CONFIG_PATH = Path(__file__).resolve().parent.parent / "database" / "logs_config.json"


def load_logs_config(config_path: Path = CONFIG_PATH):
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_logs_config(config, config_path: Path = CONFIG_PATH):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_configured_log_channel_id(guild_id, config_path: Path = CONFIG_PATH):
    config = load_logs_config(config_path)
    return config.get(str(guild_id))


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _get_log_channel(self, guild: discord.Guild):
        channel_id = get_configured_log_channel_id(guild.id)
        if not channel_id:
            return None
        return guild.get_channel(int(channel_id))

    async def _send_log_embed(self, guild: discord.Guild, embed: discord.Embed):
        channel = await self._get_log_channel(guild)
        if not channel:
            return False
        if not channel.permissions_for(guild.me).send_messages:
            return False
        await channel.send(embed=embed)
        return True

    @app_commands.command(name="set-logs-channel", description="Choisir le salon où seront envoyés les logs")
    @app_commands.describe(channel="Salon où envoyer les logs")
    async def set_logs_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return

        config = load_logs_config()
        config[str(interaction.guild.id)] = str(channel.id)
        save_logs_config(config)
        await interaction.response.send_message(f"✅ Les logs seront envoyés dans {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Log quand un utilisateur est banni"""
        embed = discord.Embed(
            title="🔨 Utilisateur Banni",
            description=f"{user.mention} ({user}) a été banni",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        if await self._send_log_embed(guild, embed):
            return

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log quand un message est supprimé"""
        if message.author.bot:
            return
        
        embed = discord.Embed(
            title="🗑️ Message Supprimé",
            description=message.content or "[Pas de contenu]",
            color=discord.Color.orange()
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar.url)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        if await self._send_log_embed(message.guild, embed):
            return

        for channel in message.guild.text_channels:
            if channel.permissions_for(message.guild.me).send_messages and channel != message.channel:
                await channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log quand un message est édité"""
        if before.author.bot or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Message Édité",
            color=discord.Color.blue()
        )
        embed.set_author(name=before.author, icon_url=before.author.avatar.url)
        embed.add_field(name="Avant", value=before.content[:1024] or "[Pas de contenu]", inline=False)
        embed.add_field(name="Après", value=after.content[:1024] or "[Pas de contenu]", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        if await self._send_log_embed(before.guild, embed):
            return

        for channel in before.guild.text_channels:
            if channel.permissions_for(before.guild.me).send_messages and channel != before.channel:
                await channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log les changements de rôles"""
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]
            
            embed = discord.Embed(
                title="👥 Rôles Modifiés",
                color=discord.Color.blurple()
            )
            embed.set_author(name=after, icon_url=after.avatar.url)
            
            if added_roles:
                embed.add_field(name="Ajoutés", value=", ".join([r.mention for r in added_roles]), inline=False)
            if removed_roles:
                embed.add_field(name="Supprimés", value=", ".join([r.mention for r in removed_roles]), inline=False)
            
            embed.timestamp = discord.utils.utcnow()
            
            if await self._send_log_embed(after.guild, embed):
                return

            for channel in after.guild.text_channels:
                if channel.permissions_for(after.guild.me).send_messages:
                    await channel.send(embed=embed)
                    break

async def setup(bot):
    await bot.add_cog(Logs(bot))
