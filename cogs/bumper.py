import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from pathlib import Path
from datetime import datetime

class Bumper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = Path(__file__).parent.parent / "database" / "bump_config.json"
        self.load_config()
        self.bump_reminder.start()

    def load_config(self):
        """Charge la configuration du bump"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8-sig') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "enabled": True,
                "interval_hours": 2,
                "last_bump": None,
                "bump_count": 0,
                "bump_channel_id": None
            }
            self.save_config()

    def save_config(self):
        """Sauvegarde la configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8-sig') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_bump_channel(self, guild: discord.Guild):
        """Retourne le channel configuré pour les rappels de bump."""
        channel_id = self.config.get("bump_channel_id")
        if not channel_id:
            return None
        return guild.get_channel(channel_id)

    def get_reminder_channel(self, guild: discord.Guild):
        """Retourne le channel principal où envoyer le ping owner pour le bump."""
        channel = self.get_bump_channel(guild)
        if channel and channel.permissions_for(guild.me).send_messages:
            return channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            return guild.system_channel
        for text_channel in guild.text_channels:
            if text_channel.permissions_for(guild.me).send_messages:
                return text_channel
        return None

    @tasks.loop(hours=2)
    async def bump_reminder(self):
        """Envoie un reminder bump toutes les 2 heures"""
        try:
            if not self.config["enabled"]:
                return

            # Pour chaque serveur où le bot est
            for guild in self.bot.guilds:
                owner = guild.owner
                
                if not owner:
                    continue
                
                # Créer l'embed de rappel
                embed = discord.Embed(
                    title="🔔 Rappel de BUMP",
                    description="Il est temps de bumper le serveur!",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 Serveur",
                    value=f"**{guild.name}** ({guild.id})",
                    inline=False
                )
                
                embed.add_field(
                    name="👥 Membres",
                    value=f"{guild.member_count} membres",
                    inline=True
                )
                
                embed.add_field(
                    name="📍 Région",
                    value=f"{guild.region if hasattr(guild, 'region') else 'Discord'}",
                    inline=True
                )
                
                embed.add_field(
                    name="💡 Commande",
                    value="Utilisez `/bump` sur **Disboard** ou **TopGG** pour bumper le serveur!",
                    inline=False
                )
                
                embed.set_footer(
                    text=f"Prochain rappel dans {self.config['interval_hours']} heures • {datetime.now().strftime('%H:%M:%S')}"
                )

                bump_channel = self.get_bump_channel(guild)
                reminder_channel = bump_channel or self.get_reminder_channel(guild)

                # Envoi prioritaire dans le salon bump s'il est configuré
                if bump_channel:
                    try:
                        await bump_channel.send(content=owner.mention, embed=embed)
                        print(f"✅ Reminder bump ping envoyé à {owner.name} dans {bump_channel.name}")
                    except Exception as e:
                        print(f"❌ Erreur lors de l'envoi du ping dans le salon bump: {e}")
                elif reminder_channel:
                    try:
                        await reminder_channel.send(content=owner.mention, embed=embed)
                        print(f"✅ Reminder bump ping envoyé à {owner.name} dans {reminder_channel.name}")
                    except Exception as e:
                        print(f"❌ Erreur lors de l'envoi du ping dans le channel: {e}")
                else:
                    print(f"⚠️ Aucun channel valide pour envoyer le ping owner dans {guild.name}")

                # Si aucun channel n'a fonctionné, tente un DM en fallback
                if not reminder_channel and not bump_channel:
                    try:
                        await owner.send(embed=embed)
                        print(f"✅ Reminder bump DM envoyé à {owner.name} pour {guild.name}")
                    except discord.Forbidden:
                        print(f"⚠️ Impossible d'envoyer un DM à {owner.name}")
                    except Exception as e:
                        print(f"❌ Erreur lors de l'envoi du DM au owner: {e}")

                # Incrémenter le compteur même si le ping a été tenté
                self.config["bump_count"] = self.config.get("bump_count", 0) + 1
                self.config["last_bump"] = datetime.now().isoformat()
                self.save_config()
        
        except Exception as e:
            print(f"❌ Erreur dans bump_reminder: {e}")

    @bump_reminder.before_loop
    async def before_bump_reminder(self):
        """Attendre que le bot soit prêt avant de démarrer la boucle"""
        await self.bot.wait_until_ready()
        print("🔔 Système de reminder bump activé (toutes les 2 heures)")

    @app_commands.command(name="bump-status", description="📊 Voir le status du système de bump")
    async def bump_status(self, interaction: discord.Interaction):
        """Affiche le status du système de bump"""
        embed = discord.Embed(
            title="📊 Status du Système de Bump",
            color=discord.Color.gold()
        )
        
        status = "✅ Activé" if self.config["enabled"] else "❌ Désactivé"
        embed.add_field(name="🔔 Status", value=status, inline=True)
        embed.add_field(name="⏰ Intervalle", value=f"{self.config['interval_hours']} heures", inline=True)
        embed.add_field(name="📈 Bumps effectués", value=str(self.config.get("bump_count", 0)), inline=True)
        
        if self.config.get("last_bump"):
            embed.add_field(
                name="🕐 Dernier bump",
                value=self.config["last_bump"],
                inline=False
            )
        
        bump_channel = self.get_bump_channel(interaction.guild)
        channel_value = bump_channel.mention if bump_channel else "Aucun canal configuré"

        embed.add_field(
            name="💡 Info",
            value="Le owner reçoit un DM toutes les 2 heures pour bumper le serveur",
            inline=False
        )
        embed.add_field(
            name="📌 Canal de rappel",
            value=channel_value,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bump-toggle", description="🔔 Activer/Désactiver le système de bump [ADMIN]")
    async def bump_toggle(self, interaction: discord.Interaction):
        """Active ou désactive le système de bump"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        self.config["enabled"] = not self.config["enabled"]
        self.save_config()
        
        status = "✅ Activé" if self.config["enabled"] else "❌ Désactivé"
        
        embed = discord.Embed(
            title="🔔 Système de Bump",
            description=f"Système {status}",
            color=discord.Color.green() if self.config["enabled"] else discord.Color.red()
        )
        embed.add_field(
            name="Status",
            value=status,
            inline=False
        )

        bump_channel = self.get_bump_channel(interaction.guild)
        channel_value = bump_channel.mention if bump_channel else "Aucun canal configuré"
        embed.add_field(
            name="📌 Canal de rappel",
            value=channel_value,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bump-channel", description="📌 Définir le canal où les rappels de bump sont annoncés [ADMIN]")
    async def bump_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return

        self.config["bump_channel_id"] = channel.id
        self.save_config()

        await interaction.response.send_message(f"✅ Canal de rappel défini sur {channel.mention}")

    @app_commands.command(name="manual-bump-reminder", description="🔔 Envoyer un reminder bump maintenant [ADMIN]")
    async def manual_bump_reminder(self, interaction: discord.Interaction):
        """Envoie manuellement un reminder au owner"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        guild = interaction.guild
        owner = guild.owner
        
        if not owner:
            await interaction.followup.send("❌ Impossible de trouver le owner du serveur!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔔 Rappel de BUMP",
            description="Il est temps de bumper le serveur!",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Serveur",
            value=f"**{guild.name}** ({guild.id})",
            inline=False
        )
        
        embed.add_field(
            name="👥 Membres",
            value=f"{guild.member_count} membres",
            inline=True
        )
        
        bump_channel = self.get_bump_channel(guild)
        if bump_channel:
            embed.add_field(
                name="📌 Canal de rappel",
                value=bump_channel.mention,
                inline=False
            )

        embed.add_field(
            name="💡 Commande",
            value="Utilisez `/bump` sur **Disboard** ou **TopGG** pour bumper le serveur!",
            inline=False
        )

        reminder_channel = self.get_reminder_channel(guild)
        try:
            await owner.send(embed=embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False
        except Exception:
            dm_sent = False

        if reminder_channel:
            try:
                await reminder_channel.send(content=owner.mention, embed=embed)
                await interaction.followup.send(f"✅ Reminder envoyé à {owner.mention} dans {reminder_channel.mention}!")
                return
            except Exception as e:
                print(f"❌ Erreur lors de l'envoi du ping dans le channel: {e}")

        if dm_sent:
            await interaction.followup.send(f"✅ Reminder DM envoyé à {owner.mention}!")
        else:
            await interaction.followup.send(f"❌ Impossible d'envoyer le reminder au owner. Vérifiez les permissions et le canal de rappel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Bumper(bot))
