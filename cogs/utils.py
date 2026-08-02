import discord
from discord.ext import commands
from discord import app_commands
import platform
import psutil

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Affiche l'aide du bot")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 Aide du Bot",
            description="Voici les catégories de commandes disponibles",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🔨 Modération",
            value="`/kick` - Expulser un utilisateur\n"
                  "`/ban` - Bannir un utilisateur\n"
                  "`/unban` - Débannir un utilisateur\n"
                  "`/mute` - Rendre muet un utilisateur\n"
                  "`/unmute` - Enlever le mute\n"
                  "`/warn` - Avertir un utilisateur\n"
                  "`/dewarn` - Retirer un avertissement\n"
                  "`/clear` - Supprimer des messages",
            inline=False
        )
        
        embed.add_field(
            name="🎉 Bienvenue",
            value="`/welcome` - Message de bienvenue",
            inline=False
        )
        
        embed.add_field(
            name="📊 XP",
            value="`/xp` - Voir votre profil XP\n"
                  "`/leaderboard` - Top 10 des meilleurs",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Utilitaires",
            value="`/help` - Cette commande\n"
                  "`/serverinfo` - Info du serveur\n"
                  "`/userinfo` - Info d'un utilisateur\n"
                  "`/botinfo` - Info du bot\n"
                  "`/roll` - Nombre aléatoire",
            inline=False
        )
        
        embed.set_footer(text=f"Bot {self.bot.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Affiche les infos du serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"ℹ️ Informations - {guild.name}",
            color=discord.Color.blurple()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Propriétaire", value=guild.owner.mention, inline=True)
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Rôles", value=len(guild.roles), inline=True)
        embed.add_field(name="Niveau Boost", value=guild.premium_tier, inline=True)
        embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Affiche les infos d'un utilisateur")
    @app_commands.describe(user="L'utilisateur (optionnel)")
    async def userinfo(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        
        embed = discord.Embed(
            title=f"👤 Informations - {user.name}",
            color=discord.Color.blurple()
        )
        
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Tag", value=user, inline=True)
        embed.add_field(name="Bot", value="✅ Oui" if user.bot else "❌ Non", inline=True)
        embed.add_field(name="Compte créé", value=user.created_at.strftime("%d/%m/%Y"), inline=False)
        
        if isinstance(user, discord.Member):
            embed.add_field(name="Rejoint le", value=user.joined_at.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="Rôles", value=f"{len(user.roles) - 1}", inline=True)
            if user.roles[-1] != interaction.guild.default_role:
                embed.add_field(name="Top Rôle", value=user.top_role.mention, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Affiche les infos du bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🤖 Informations - {self.bot.user.name}",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(name="ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Prefix", value="`!`", inline=True)
        embed.add_field(name="Serveurs", value=len(self.bot.guilds), inline=True)
        
        # Stats système
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        embed.add_field(name="CPU", value=f"{cpu_percent}%", inline=True)
        embed.add_field(name="RAM", value=f"{memory.percent}%", inline=True)
        
        embed.add_field(name="Discord.py", value=f"v{discord.__version__}", inline=True)
        embed.add_field(name="Python", value=f"v{platform.python_version()}", inline=True)
        embed.add_field(name="OS", value=platform.system(), inline=True)
        
        embed.set_footer(text=f"Crée avec ❤️")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utils(bot))
