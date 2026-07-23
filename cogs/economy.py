import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path
from datetime import datetime, timedelta

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy_file = Path(__file__).parent.parent / "database" / "economy.json"
        self.economy_file.parent.mkdir(exist_ok=True)
        self.load_economy()

    def load_economy(self):
        if self.economy_file.exists():
            with open(self.economy_file, 'r', encoding='utf-8-sig') as f:
                self.economy_data = json.load(f)
        else:
            self.economy_data = {}

    def save_economy(self):
        with open(self.economy_file, 'w', encoding='utf-8-sig') as f:
            json.dump(self.economy_data, f, indent=2)

    def get_user_wallet(self, user_id: str):
        user_id = str(user_id)
        if user_id not in self.economy_data:
            self.economy_data[user_id] = {"wallet": 1000, "bank": 0, "last_salary": None, "items": {}}
        return self.economy_data[user_id]

    @app_commands.command(name="balance", description="Affiche votre solde")
    async def balance(self, interaction: discord.Interaction):
        user_data = self.get_user_wallet(interaction.user.id)
        total = user_data["wallet"] + user_data["bank"]
        
        embed = discord.Embed(
            title="💰 Solde",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.add_field(name="Portefeuille", value=f"{user_data['wallet']}💰", inline=True)
        embed.add_field(name="Banque", value=f"{user_data['bank']}💰", inline=True)
        embed.add_field(name="Total", value=f"{total}💰", inline=True)
        
        self.save_economy()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deposit", description="Déposer de l'argent à la banque")
    @app_commands.describe(amount="Montant à déposer")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        user_data = self.get_user_wallet(interaction.user.id)
        
        if amount <= 0:
            await interaction.response.send_message("❌ Montant invalide!", ephemeral=True)
            return
        
        if user_data["wallet"] < amount:
            await interaction.response.send_message(f"❌ Vous n'avez pas assez d'argent! (Vous avez {user_data['wallet']}💰)", ephemeral=True)
            return
        
        user_data["wallet"] -= amount
        user_data["bank"] += amount
        self.save_economy()
        
        await interaction.response.send_message(f"✅ Vous avez déposé {amount}💰 à la banque!")

    @app_commands.command(name="withdraw", description="Retirer de l'argent de la banque")
    @app_commands.describe(amount="Montant à retirer")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        user_data = self.get_user_wallet(interaction.user.id)
        
        if amount <= 0:
            await interaction.response.send_message("❌ Montant invalide!", ephemeral=True)
            return
        
        if user_data["bank"] < amount:
            await interaction.response.send_message(f"❌ Vous n'avez pas assez à la banque! (Vous avez {user_data['bank']}💰)", ephemeral=True)
            return
        
        user_data["bank"] -= amount
        user_data["wallet"] += amount
        self.save_economy()
        
        await interaction.response.send_message(f"✅ Vous avez retiré {amount}💰 de la banque!")

    @app_commands.command(name="daily", description="Récupérez votre salaire quotidien")
    async def daily(self, interaction: discord.Interaction):
        user_data = self.get_user_wallet(interaction.user.id)
        now = datetime.now()
        
        last_salary = user_data.get("last_salary")
        if last_salary:
            last_salary = datetime.fromisoformat(last_salary)
            if now - last_salary < timedelta(hours=24):
                time_left = timedelta(hours=24) - (now - last_salary)
                await interaction.response.send_message(f"⏰ Vous devez attendre {time_left.seconds // 3600}h pour le prochain salaire!", ephemeral=True)
                return
        
        reward = 500
        user_data["wallet"] += reward
        user_data["last_salary"] = now.isoformat()
        self.save_economy()
        
        embed = discord.Embed(
            title="💵 Salaire Quotidien",
            description=f"Vous avez reçu {reward}💰!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Travaillez pour gagner de l'argent")
    async def work(self, interaction: discord.Interaction):
        import random
        
        earning = random.randint(50, 200)
        user_data = self.get_user_wallet(interaction.user.id)
        user_data["wallet"] += earning
        self.save_economy()
        
        jobs = ["développeur", "pizzaiolo", "nettoyeur", "professeur", "médecin", "chauffeur"]
        job = random.choice(jobs)
        
        embed = discord.Embed(
            title="💼 Vous avez travaillé!",
            description=f"Vous avez travaillé comme {job} et gagné {earning}💰!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rob", description="Volez un utilisateur (risqué!)")
    @app_commands.describe(user="L'utilisateur à voler")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        import random
        
        if user.bot:
            await interaction.response.send_message("❌ Impossible de voler un bot!", ephemeral=True)
            return
        
        target_data = self.get_user_wallet(user.id)
        
        if target_data["wallet"] < 100:
            await interaction.response.send_message(f"❌ {user.mention} n'a pas assez d'argent!", ephemeral=True)
            return
        
        if random.random() < 0.5:
            stolen = random.randint(50, 200)
            target_data["wallet"] -= stolen
            
            user_data = self.get_user_wallet(interaction.user.id)
            user_data["wallet"] += stolen
            self.save_economy()
            
            await interaction.response.send_message(f"✅ Vous avez volé {stolen}💰 à {user.mention}!")
        else:
            await interaction.response.send_message(f"❌ Vous avez échoué à voler {user.mention}...")

    @app_commands.command(name="leaderboard-money", description="Classement de richesse")
    async def leaderboard_money(self, interaction: discord.Interaction):
        sorted_users = sorted(
            self.economy_data.items(),
            key=lambda x: (x[1]["wallet"] + x[1]["bank"]),
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="🏆 Classement de Richesse",
            color=discord.Color.gold()
        )
        
        for i, (user_id, data) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                total = data["wallet"] + data["bank"]
                embed.add_field(
                    name=f"#{i} {user.name}",
                    value=f"{total}💰",
                    inline=False
                )
            except:
                pass
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
