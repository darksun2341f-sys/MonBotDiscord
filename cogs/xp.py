import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_file = Path(__file__).parent.parent / "database" / "xp.json"
        self.xp_file.parent.mkdir(exist_ok=True)
        self.load_xp()

    def load_xp(self):
        """Charge les données XP"""
        if self.xp_file.exists():
            with open(self.xp_file, 'r', encoding='utf-8-sig') as f:
                self.xp_data = json.load(f)
        else:
            self.xp_data = {}

    def save_xp(self):
        """Sauvegarde les données XP"""
        with open(self.xp_file, 'w', encoding='utf-8-sig') as f:
            json.dump(self.xp_data, f, indent=2)

    def get_user_xp(self, user_id: str):
        """Récupère l'XP d'un utilisateur"""
        return self.xp_data.get(str(user_id), {"xp": 0, "level": 1})

    def add_xp(self, user_id: str, amount: int = 10):
        """Ajoute de l'XP à un utilisateur"""
        user_id = str(user_id)
        if user_id not in self.xp_data:
            self.xp_data[user_id] = {"xp": 0, "level": 1}

        self.xp_data[user_id]["xp"] += amount
        leveled_up = False

        # Calcul du niveau: XP nécessaire = niveau * 100
        while True:
            level_threshold = self.xp_data[user_id]["level"] * 100
            if self.xp_data[user_id]["xp"] >= level_threshold:
                self.xp_data[user_id]["xp"] -= level_threshold
                self.xp_data[user_id]["level"] += 1
                leveled_up = True
            else:
                break

        self.save_xp()
        return leveled_up

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Ajoute de l'XP à chaque message"""
        if message.author.bot or not message.guild:
            return
        
        leveled_up = self.add_xp(message.author.id)
        
        if leveled_up:
            user_data = self.get_user_xp(message.author.id)
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{message.author.mention} est passé au niveau **{user_data['level']}**!",
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed, delete_after=5)

    @app_commands.command(name="xp", description="Voir votre XP et votre niveau")
    async def xp_cmd(self, interaction: discord.Interaction):
        user_data = self.get_user_xp(interaction.user.id)
        level_threshold = user_data["level"] * 100
        
        embed = discord.Embed(
            title="📊 Votre Profil XP",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.add_field(name="Niveau", value=user_data["level"], inline=True)
        embed.add_field(name="XP", value=f"{user_data['xp']}/{level_threshold}", inline=True)
        
        # Barre de progression
        progress = int((user_data["xp"] / level_threshold) * 10)
        bar = "█" * progress + "░" * (10 - progress)
        embed.add_field(name="Progression", value=f"`{bar}`", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Voir le top XP du serveur")
    async def leaderboard(self, interaction: discord.Interaction):
        # Trier par niveau puis par XP
        sorted_users = sorted(
            self.xp_data.items(),
            key=lambda x: (x[1]["level"], x[1]["xp"]),
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="🏆 Leaderboard XP",
            color=discord.Color.gold()
        )
        
        for i, (user_id, data) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(
                    name=f"#{i} {user.name}",
                    value=f"Niveau {data['level']} - {data['xp']} XP",
                    inline=False
                )
            except:
                pass
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))
