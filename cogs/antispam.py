import discord
from discord.ext import commands
from discord import app_commands
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_messages = defaultdict(list)
        self.muted_users = set()
        
        # Configuration
        self.max_messages = 5  # Maximum de messages
        self.time_window = 5   # Dans cette durée (en secondes)
        self.mute_duration = 60  # Mute de X secondes

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Détecte et prévient le spam + mentions massives"""
        if message.author.bot or not message.guild:
            return
        
        # ===== Détection des mentions massives =====
        if len(message.mentions) > 5:
            try:
                await message.delete()
            except:
                pass
            
            embed = discord.Embed(
                title="⚠️ Mentions Massives Bloquées",
                description=f"{message.author.mention}, les mentions massives sont interdites!",
                color=discord.Color.red()
            )
            
            await message.channel.send(embed=embed, delete_after=5)
            return
        
        # ===== Détection du spam =====
        user_id = message.author.id
        now = datetime.now()
        
        # Ajouter le message à l'historique
        self.user_messages[user_id].append(now)
        
        # Nettoyer les anciens messages (plus de X secondes)
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if now - msg_time < timedelta(seconds=self.time_window)
        ]
        
        # Vérifier si spam
        if len(self.user_messages[user_id]) > self.max_messages:
            # Spam détecté
            try:
                await message.delete()
            except:
                pass
            
            if user_id not in self.muted_users:
                self.muted_users.add(user_id)
                
                # Timeout temporaire
                try:
                    await message.author.timeout(
                        timedelta(seconds=self.mute_duration),
                        reason="Spam détecté"
                    )
                except:
                    pass
                
                # Envoyer un avertissement
                embed = discord.Embed(
                    title="⚠️ Spam Détecté",
                    description=f"{message.author.mention}, vous avez envoyé trop de messages trop vite!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Timeout",
                    value=f"Vous avez été rendu muet pendant {self.mute_duration} secondes",
                    inline=False
                )
                
                try:
                    await message.author.send(embed=embed)
                except:
                    pass
                
                # Afficher dans le channel
                embed.set_footer(text="Le timeout sera levé automatiquement")
                await message.channel.send(embed=embed, delete_after=10)
                
                # Retirer de muted_users après le timeout (en arrière-plan)
                asyncio.create_task(self._unmute_user(user_id))

    async def _unmute_user(self, user_id):
        """Retire un utilisateur de la liste des mutés après le timeout"""
        await asyncio.sleep(self.mute_duration)
        self.muted_users.discard(user_id)

    @app_commands.command(name="anti-spam", description="Configure l'anti-spam (admin only)")
    @app_commands.describe(
        max_messages="Nombre max de messages",
        time_window="Durée de la fenêtre (secondes)",
        mute_duration="Durée du timeout (secondes)"
    )
    async def anti_spam_config(
        self,
        interaction: discord.Interaction,
        max_messages: int = None,
        time_window: int = None,
        mute_duration: int = None
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        if max_messages:
            self.max_messages = max_messages
        if time_window:
            self.time_window = time_window
        if mute_duration:
            self.mute_duration = mute_duration
        
        embed = discord.Embed(
            title="⚙️ Anti-Spam Configuré",
            color=discord.Color.green()
        )
        embed.add_field(name="Max Messages", value=self.max_messages, inline=True)
        embed.add_field(name="Fenêtre Temps", value=f"{self.time_window}s", inline=True)
        embed.add_field(name="Timeout", value=f"{self.mute_duration}s", inline=True)
        
        await interaction.response.send_message(embed=embed)

import asyncio

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
