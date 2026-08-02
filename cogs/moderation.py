import json
from pathlib import Path

import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from utils.authorization import has_permission

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = Path(__file__).parent.parent / "database" / "warnings.json"
        self.warnings_data = self.load_warnings()

    def load_warnings(self) -> dict:
        self.warnings_file.parent.mkdir(parents=True, exist_ok=True)
        if self.warnings_file.exists():
            try:
                with self.warnings_file.open("r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_warnings(self) -> None:
        with self.warnings_file.open("w", encoding="utf-8") as f:
            json.dump(self.warnings_data, f, ensure_ascii=False, indent=2)

    def get_warn_record(self, guild_id: int, member_id: int) -> dict:
        guild_data = self.warnings_data.setdefault(str(guild_id), {})
        return guild_data.setdefault(str(member_id), {"count": 0, "reasons": []})

    def add_warning(self, guild_id: int, member_id: int, reason: str) -> dict:
        record = self.get_warn_record(guild_id, member_id)
        record["count"] += 1
        record["reasons"].append(reason)
        self.save_warnings()
        return record

    def remove_warning(self, guild_id: int, member_id: int, reason: str | None = None) -> dict | None:
        guild_data = self.warnings_data.get(str(guild_id), {})
        member_record = guild_data.get(str(member_id))
        if not member_record or member_record.get("count", 0) == 0:
            return None

        if reason and reason in member_record.get("reasons", []):
            member_record["reasons"].remove(reason)
        elif member_record.get("reasons"):
            member_record["reasons"].pop()

        member_record["count"] = max(0, len(member_record.get("reasons", [])))

        if member_record["count"] == 0:
            guild_data.pop(str(member_id), None)
            if not guild_data:
                self.warnings_data.pop(str(guild_id), None)
        self.save_warnings()
        return member_record

    def format_warning_list(self, record: dict) -> str:
        lines = []
        for idx, reason in enumerate(record.get("reasons", []), start=1):
            lines.append(f"{idx}. {reason}")
        return "\n".join(lines)

    @app_commands.command(name="kick", description="Expulse un utilisateur du serveur")
    @app_commands.describe(
        member="L'utilisateur à expulser",
        reason="Raison de l'expulsion"
    )
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if has_permission(interaction, "kick_members"):
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="⚠️ Utilisateur Expulsé",
                description=f"{member.mention} a été expulsé du serveur",
                color=discord.Color.orange()
            )
            embed.add_field(name="Raison", value=reason, inline=False)
            embed.add_field(name="Par", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="ban", description="Bannit un utilisateur du serveur")
    @app_commands.describe(
        member="L'utilisateur à bannir",
        reason="Raison du ban"
    )
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if has_permission(interaction, "ban_members"):
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 Utilisateur Banni",
                description=f"{member.mention} a été banni du serveur",
                color=discord.Color.red()
            )
            embed.add_field(name="Raison", value=reason, inline=False)
            embed.add_field(name="Par", value=interaction.user.mention, inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="unban", description="Débannit un utilisateur")
    @app_commands.describe(user="L'utilisateur à débannir (ID ou nom)")
    async def unban(self, interaction: discord.Interaction, user: str):
        if has_permission(interaction, "ban_members"):
            try:
                user_id = int(user)
                banned_users = [entry async for entry in interaction.guild.bans()]
                for ban_entry in banned_users:
                    if ban_entry.user.id == user_id:
                        await interaction.guild.unban(ban_entry.user)
                        await interaction.response.send_message(f"✅ {ban_entry.user.mention} a été débanni!")
                        return
                await interaction.response.send_message("❌ Utilisateur non trouvé dans les bans!", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("❌ ID utilisateur invalide!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="mute", description="Rend un utilisateur muet (timeout)")
    @app_commands.describe(
        member="L'utilisateur à mute",
        duration="Durée en minutes",
        reason="Raison du mute"
    )
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "Aucune raison"):
        if has_permission(interaction, "moderate_members"):
            try:
                timeout = timedelta(minutes=duration)
                await member.timeout(timeout, reason=reason)
                embed = discord.Embed(
                    title="🔇 Utilisateur Muet",
                    description=f"{member.mention} a été rendu muet pour {duration} minutes",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Raison", value=reason, inline=False)
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="unmute", description="Enlève le mute d'un utilisateur")
    @app_commands.describe(member="L'utilisateur à unmute")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if has_permission(interaction, "moderate_members"):
            try:
                await member.timeout(None)
                await interaction.response.send_message(f"✅ {member.mention} a été unmute!")
            except Exception as e:
                await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="warn", description="Avertit un utilisateur")
    @app_commands.describe(
        member="L'utilisateur à avertir",
        reason="Raison de l'avertissement"
    )
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if has_permission(interaction, "moderate_members"):
            record = self.add_warning(interaction.guild.id, member.id, reason)
            embed = discord.Embed(
                title="⚠️ Avertissement",
                description=f"{member.mention} a reçu un avertissement",
                color=discord.Color.orange()
            )
            embed.add_field(name="Raison", value=reason, inline=False)
            embed.add_field(name="Par", value=interaction.user.mention, inline=False)
            embed.add_field(name="Total d'avertissements", value=str(record["count"]), inline=False)
            if record.get("reasons"):
                embed.add_field(name="Historique des avertissements", value=self.format_warning_list(record), inline=False)

            await interaction.response.send_message(embed=embed)
            try:
                await member.send(embed=embed)
            except:
                pass
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="dewarn", description="Retire un avertissement d'un utilisateur")
    @app_commands.describe(
        member="L'utilisateur à qui retirer l'avertissement",
        reason="Raison de la suppression de l'avertissement"
    )
    async def dewarn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if has_permission(interaction, "moderate_members"):
            record = self.remove_warning(interaction.guild.id, member.id, reason if reason != "Aucune raison" else None)
            if not record:
                return await interaction.response.send_message("❌ Aucun avertissement à retirer pour cet utilisateur.", ephemeral=True)

            embed = discord.Embed(
                title="✔️ Avertissement retiré",
                description=f"{member.mention} a un avertissement retiré",
                color=discord.Color.green()
            )
            embed.add_field(name="Raison", value=reason, inline=False)
            embed.add_field(name="Par", value=interaction.user.mention, inline=False)
            embed.add_field(name="Avertissements restants", value=str(record.get("count", 0)), inline=False)
            if record.get("reasons"):
                embed.add_field(name="Historique des avertissements", value=self.format_warning_list(record), inline=False)

            await interaction.response.send_message(embed=embed)
            try:
                await member.send(embed=embed)
            except:
                pass
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

    @app_commands.command(name="clear", description="Supprime des messages")
    @app_commands.describe(amount="Nombre de messages à supprimer (max 100)")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if has_permission(interaction, "manage_messages"):
            if amount > 100:
                amount = 100
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.response.send_message(f"✅ {len(deleted)} messages supprimés!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
