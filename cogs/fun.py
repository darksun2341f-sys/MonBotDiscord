import discord
from discord.ext import commands
from discord import app_commands
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dice", description="Lance un dé")
    @app_commands.describe(sides="Nombre de faces (par défaut 6)")
    async def dice(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2:
            await interaction.response.send_message("❌ Le dé doit avoir au moins 2 faces!", ephemeral=True)
            return
        
        result = random.randint(1, sides)
        
        embed = discord.Embed(
            title="🎲 Dé",
            description=f"Vous avez obtenu: **{result}**",
            color=discord.Color.blurple()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coin", description="Pile ou face")
    async def coin(self, interaction: discord.Interaction):
        result = random.choice(["Pile", "Face"])
        
        embed = discord.Embed(
            title="🪙 Pile ou Face",
            description=f"Résultat: **{result}**",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Posez une question à la boule 8")
    @app_commands.describe(question="Votre question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Oui",
            "Non",
            "Peut-être",
            "Demande plus tard",
            "C'est certain",
            "Très probable",
            "Peu probable",
            "Le doute s'installe",
            "Impossible",
            "L'avenir est flou"
        ]
        
        result = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Boule 8",
            description=f"**Question:** {question}\n\n**Réponse:** {result}",
            color=discord.Color.purple()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Affiche l'avatar d'un utilisateur")
    @app_commands.describe(user="L'utilisateur (optionnel)")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        
        embed = discord.Embed(
            title=f"Avatar de {user.name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=user.avatar.url)
        embed.add_field(name="Lien", value=f"[Cliquez ici]({user.avatar.url})", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="random-user", description="Choisit un utilisateur aléatoire")
    async def random_user(self, interaction: discord.Interaction):
        members = [m for m in interaction.guild.members if not m.bot]
        
        if not members:
            await interaction.response.send_message("❌ Pas de membres disponibles!", ephemeral=True)
            return
        
        chosen = random.choice(members)
        
        embed = discord.Embed(
            title="🎲 Utilisateur Aléatoire",
            description=f"Élu: {chosen.mention}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=chosen.avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="joke", description="Affiche une blague")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant? Parce que sinon ils tombent dans le bateau!",
            "Qu'est-ce qu'un crocodile qui surveille la pharmacie? Un Lacoste-guard!",
            "Pourquoi les poissons n'aiment pas jouer au tennis? Parce qu'ils ont peur du filet!",
            "Comment appelle-t-on un chat tombé dans un pot de peinture le jour de Noël? Un chat-peint de Noël!",
            "Qu'est-ce qu'un cannibale végétarien? Un humain!",
        ]
        
        joke = random.choice(jokes)
        
        embed = discord.Embed(
            title="😂 Blague",
            description=joke,
            color=discord.Color.yellow()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roll", description="Lance un dé personnalisé")
    @app_commands.describe(
        min_value="Valeur minimale",
        max_value="Valeur maximale"
    )
    async def roll(self, interaction: discord.Interaction, min_value: int = 1, max_value: int = 100):
        if min_value >= max_value:
            await interaction.response.send_message("❌ Min doit être < Max!", ephemeral=True)
            return
        
        result = random.randint(min_value, max_value)
        
        embed = discord.Embed(
            title="🎲 Tirage Aléatoire",
            description=f"Nombre entre {min_value} et {max_value}: **{result}**",
            color=discord.Color.blurple()
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
