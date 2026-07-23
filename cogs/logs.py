import discord
from discord.ext import commands
from discord import app_commands

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        
        # Envoyer dans le channel système ou le premier channel où le bot peut écrire
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
        
        # Envoyer dans le channel système
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
        
        # Envoyer dans le channel système
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
            
            # Envoyer dans le channel système
            for channel in after.guild.text_channels:
                if channel.permissions_for(after.guild.me).send_messages:
                    await channel.send(embed=embed)
                    break

async def setup(bot):
    await bot.add_cog(Logs(bot))
