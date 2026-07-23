import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Expulse un utilisateur du serveur")
    @app_commands.describe(
        member="L'utilisateur à expulser",
        reason="Raison de l'expulsion"
    )
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
        if interaction.user.guild_permissions.kick_members:
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
        if interaction.user.guild_permissions.ban_members:
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
        if interaction.user.guild_permissions.ban_members:
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
        if interaction.user.guild_permissions.moderate_members:
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
        if interaction.user.guild_permissions.moderate_members:
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
        if interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="⚠️ Avertissement",
                description=f"{member.mention} a reçu un avertissement",
                color=discord.Color.orange()
            )
            embed.add_field(name="Raison", value=reason, inline=False)
            embed.add_field(name="Par", value=interaction.user.mention, inline=False)
            
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
        if interaction.user.guild_permissions.manage_messages:
            if amount > 100:
                amount = 100
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.response.send_message(f"✅ {len(deleted)} messages supprimés!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
