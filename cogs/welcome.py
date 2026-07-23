import discord
from discord.ext import commands
from discord import app_commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Envoie un message de bienvenue quand quelqu'un rejoint"""
        welcome_channel = member.guild.system_channel
        
        if welcome_channel:
            embed = discord.Embed(
                title="🎉 Bienvenue!",
                description=f"Bienvenue à {member.mention}!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Membre #", value=member.guild.member_count, inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            
            await welcome_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Envoie un message quand quelqu'un quitte"""
        welcome_channel = member.guild.system_channel
        
        if welcome_channel:
            embed = discord.Embed(
                title="👋 Au Revoir",
                description=f"{member} a quitté le serveur",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Membres restants", value=member.guild.member_count, inline=False)
            
            await welcome_channel.send(embed=embed)

    @app_commands.command(name="welcome", description="Affiche le message de bienvenue du serveur")
    async def welcome_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 Bienvenue sur le serveur!",
            description=f"Nous sommes heureux de vous accueillir, {interaction.user.mention}!",
            color=discord.Color.green()
        )
        embed.add_field(name="📋 Règles", value="Lisez les règles du serveur", inline=False)
        embed.add_field(name="🎮 Channels", value="Explorez tous nos channels", inline=False)
        embed.add_field(name="👥 Communauté", value=f"Nous avons {interaction.guild.member_count} membres!", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
