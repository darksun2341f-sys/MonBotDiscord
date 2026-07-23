import discord
from discord.ext import commands
import os
from pathlib import Path
import asyncio

# Charge le fichier .env manuellement (utf-8-sig enlève le BOM)
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERREUR: TOKEN non trouvé dans .env")
    exit(1)

print(f"✅ TOKEN chargé avec succès!")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Création du bot
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ {bot.user} est connecté !")
    print(f"ID : {bot.user.id}")
    print(f"Serveurs: {len(bot.guilds)}")
    for guild in bot.guilds:
        print(f"  - {guild.name} (ID: {guild.id})")
    print("=" * 50)

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commande(s) slash synchronisée(s).")
        print("💡 Les commandes peuvent mettre jusqu'à 1 heure à apparaître.")
        print("💡 Essayez: /panel, /admin-panel, /help, /xp, /leaderboard")
    except Exception as e:
        print(f"❌ Erreur: {e}")

# Charger les cogs
async def load_cogs():
    """Charge tous les cogs du dossier cogs"""
    cogs_dir = Path(__file__).parent / "cogs"
    
    if not cogs_dir.exists():
        cogs_dir.mkdir()
        print("⚠️ Dossier 'cogs' créé")
        return
    
    for file in cogs_dir.glob("*.py"):
        if file.name.startswith("_"):
            continue
        
        cog_name = file.stem
        try:
            await bot.load_extension(f"cogs.{cog_name}")
            print(f"✅ Cog chargé: {cog_name}")
        except Exception as e:
            print(f"❌ Erreur en chargeant {cog_name}: {e}")

@bot.event
async def setup_hook():
    """Appelé avant que le bot se connecte"""
    await load_cogs()

# Commande Slash /ping
@bot.tree.command(name="ping", description="Vérifie si le bot répond.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong !")

# Lancement du bot
bot.run(TOKEN)