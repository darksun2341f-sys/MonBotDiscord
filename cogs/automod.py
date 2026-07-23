import discord
from discord.ext import commands
from discord import app_commands
import re

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.profanity_filter = ["badword1", "badword2", "badword3"]  # À personnaliser
        self.spam_users = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        
        # ===== Anti CAPS =====
        caps_count = sum(1 for c in message.content if c.isupper())
        if len(message.content) > 10 and caps_count / len(message.content) > 0.8:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, trop de majuscules!", delete_after=5)
                return
            except:
                pass
        
        # ===== Anti Lien =====
        if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, les liens ne sont pas autorisés!", delete_after=5)
                return
            except:
                pass
        
        # ===== Anti Invitation =====
        if re.search(r'discord\.gg/\S+|discord\.com/invite/\S+', message.content):
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, les invitations ne sont pas autorisées!", delete_after=5)
                return
            except:
                pass
        
        # ===== Filtre de Mots =====
        for word in self.profanity_filter:
            if word.lower() in message.content.lower():
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, ce mot n'est pas autorisé!", delete_after=5)
                    return
                except:
                    pass
        
        # ===== Anti Flood =====
        user_id = message.author.id
        import time
        current_time = time.time()
        
        if user_id not in self.spam_users:
            self.spam_users[user_id] = []
        
        self.spam_users[user_id].append(current_time)
        self.spam_users[user_id] = [t for t in self.spam_users[user_id] if current_time - t < 5]
        
        if len(self.spam_users[user_id]) > 5:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, slow down!", delete_after=5)
                return
            except:
                pass
        
        # ===== Anti Ghost Ping =====
        if message.mentions:
            await asyncio.sleep(0.5)
            try:
                latest_message = await message.channel.fetch_message(message.id)
                if not latest_message.mentions:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, ghost ping détecté!", delete_after=5)
            except:
                pass

    @app_commands.command(name="add-filter", description="Ajouter un mot au filtre")
    @app_commands.describe(word="Le mot à filtrer")
    async def add_filter(self, interaction: discord.Interaction, word: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        if word not in self.profanity_filter:
            self.profanity_filter.append(word.lower())
            await interaction.response.send_message(f"✅ Mot '{word}' ajouté au filtre!")
        else:
            await interaction.response.send_message(f"⚠️ Le mot '{word}' est déjà filtré!", ephemeral=True)

    @app_commands.command(name="remove-filter", description="Retirer un mot du filtre")
    @app_commands.describe(word="Le mot à retirer")
    async def remove_filter(self, interaction: discord.Interaction, word: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        if word.lower() in self.profanity_filter:
            self.profanity_filter.remove(word.lower())
            await interaction.response.send_message(f"✅ Mot '{word}' retiré du filtre!")
        else:
            await interaction.response.send_message(f"⚠️ Le mot '{word}' n'est pas dans le filtre!", ephemeral=True)

    @app_commands.command(name="slowmode", description="Active le slowmode")
    @app_commands.describe(seconds="Durée en secondes (0 pour désactiver)")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Permission refusée!", ephemeral=True)
            return
        
        try:
            await interaction.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await interaction.response.send_message("✅ Slowmode désactivé!")
            else:
                await interaction.response.send_message(f"✅ Slowmode activé: {seconds}s entre les messages!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="lock", description="Verrouille le channel")
    async def lock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Permission refusée!", ephemeral=True)
            return
        
        try:
            await interaction.channel.set_permissions(
                interaction.guild.default_role,
                send_messages=False
            )
            await interaction.response.send_message("🔒 Channel verrouillé!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="unlock", description="Déverrouille le channel")
    async def unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Permission refusée!", ephemeral=True)
            return
        
        try:
            await interaction.channel.set_permissions(
                interaction.guild.default_role,
                send_messages=None
            )
            await interaction.response.send_message("🔓 Channel déverrouillé!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

import asyncio

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
