import discord
from discord.ext import commands
from discord import app_commands, ui
import json
from pathlib import Path
from utils.authorization import has_bot_administrator_access, has_permission

# ==================== VIEWS ====================

class MainPanelView(ui.View):
    """Menu principal avec navigation"""
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @ui.button(label="👤 Profil", style=discord.ButtonStyle.blurple, emoji="👤")
    async def profile_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        # Récupérer les données XP
        xp_file = Path(__file__).parent.parent / "database" / "xp.json"
        if xp_file.exists():
            with open(xp_file, 'r', encoding='utf-8-sig') as f:
                xp_data = json.load(f)
        else:
            xp_data = {}
        
        user_data = xp_data.get(str(interaction.user.id), {"xp": 0, "level": 1})
        level_threshold = user_data["level"] * 100
        progress = int((user_data["xp"] / level_threshold) * 10)
        bar = "█" * progress + "░" * (10 - progress)
        
        embed = discord.Embed(
            title="👤 Profil Utilisateur",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url)
        embed.add_field(name="Nom", value=interaction.user.mention, inline=True)
        embed.add_field(name="Niveau", value=user_data["level"], inline=True)
        embed.add_field(name="Serveurs", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="XP", value=f"{user_data['xp']}/{level_threshold}", inline=False)
        embed.add_field(name="Progression", value=f"`{bar}`", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="🏆 Leaderboard", style=discord.ButtonStyle.green, emoji="🏆")
    async def leaderboard_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        xp_file = Path(__file__).parent.parent / "database" / "xp.json"
        
        if xp_file.exists():
            with open(xp_file, 'r', encoding='utf-8-sig') as f:
                xp_data = json.load(f)
        else:
            xp_data = {}
        
        sorted_users = sorted(
            xp_data.items(),
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
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="ℹ️ Serveur", style=discord.ButtonStyle.gray, emoji="ℹ️")
    async def server_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"ℹ️ Informations - {guild.name}",
            color=discord.Color.blurple()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Rôles", value=len(guild.roles), inline=True)
        embed.add_field(name="Propriétaire", value=guild.owner.mention, inline=False)
        embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="❌ Fermer", style=discord.ButtonStyle.red, emoji="❌")
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()


class AdminPanelView(ui.View):
    """Panel de contrôle admin"""
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @ui.button(label="🔨 Modération", style=discord.ButtonStyle.red, emoji="🔨")
    async def moderation_button(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="🔨 Commandes de Modération",
            description="Utilisez ces commandes pour modérer le serveur",
            color=discord.Color.red()
        )
        embed.add_field(name="/kick <user> [reason]", value="Expulser un utilisateur", inline=False)
        embed.add_field(name="/ban <user> [reason]", value="Bannir un utilisateur", inline=False)
        embed.add_field(name="/unban <user_id>", value="Débannir un utilisateur", inline=False)
        embed.add_field(name="/mute <user> <minutes> [reason]", value="Rendre muet un utilisateur", inline=False)
        embed.add_field(name="/unmute <user>", value="Enlever le mute", inline=False)
        embed.add_field(name="/warn <user> [reason]", value="Avertir un utilisateur", inline=False)
        embed.add_field(name="/clear <amount>", value="Supprimer des messages", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="📊 Statistiques", style=discord.ButtonStyle.blurple, emoji="📊")
    async def stats_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        
        # Compter les statistiques
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots
        
        embed = discord.Embed(
            title="📊 Statistiques du Serveur",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Membres Humains", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        embed.add_field(name="Total", value=guild.member_count, inline=True)
        embed.add_field(name="Channels Texte", value=text_channels, inline=True)
        embed.add_field(name="Channels Vocal", value=voice_channels, inline=True)
        embed.add_field(name="Rôles", value=len(guild.roles), inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="⚙️ Configuration", style=discord.ButtonStyle.gray, emoji="⚙️")
    async def config_button(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="⚙️ Configuration",
            description="Utilisez `/anti-spam` pour configurer l'anti-spam",
            color=discord.Color.gray()
        )
        embed.add_field(name="Anti-Spam", value="Configure le système anti-spam du bot", inline=False)
        embed.add_field(name="Logs", value="Les logs sont automatiques et s'affichent ici", inline=False)
        embed.add_field(name="Bienvenue", value="Les messages de bienvenue sont automatiques", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="❌ Fermer", style=discord.ButtonStyle.red, emoji="❌")
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()


class UserPanelView(ui.View):
    """Panel profil utilisateur"""
    def __init__(self, bot, user: discord.Member):
        super().__init__()
        self.bot = bot
        self.user = user

    @ui.button(label="👤 Profil", style=discord.ButtonStyle.blurple)
    async def profile_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title=f"👤 {self.user.name}",
            color=self.user.color
        )
        embed.set_thumbnail(url=self.user.avatar.url)
        embed.add_field(name="ID", value=self.user.id, inline=True)
        embed.add_field(name="Créé le", value=self.user.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Rejoint le", value=self.user.joined_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Top Rôle", value=self.user.top_role.mention, inline=False)
        embed.add_field(name="Rôles", value=f"{len(self.user.roles) - 1}", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="🔧 Actions", style=discord.ButtonStyle.red)
    async def actions_button(self, interaction: discord.Interaction, button: ui.Button):
        if not has_permission(interaction, "moderate_members"):
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔧 Actions Disponibles",
            description=f"Actions pour {self.user.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="/kick", value="Expulser", inline=True)
        embed.add_field(name="/ban", value="Bannir", inline=True)
        embed.add_field(name="/mute", value="Mute", inline=True)
        embed.add_field(name="/warn", value="Avertir", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ServerPanelView(ui.View):
    """Panel du serveur"""
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @ui.button(label="📋 Règles", style=discord.ButtonStyle.blurple)
    async def rules_button(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="📋 Règles du Serveur",
            description="Lisez attentivement les règles",
            color=discord.Color.blurple()
        )
        embed.add_field(name="1️⃣ Respect", value="Respectez tous les membres", inline=False)
        embed.add_field(name="2️⃣ Pas de Spam", value="Pas de spam ou de flood", inline=False)
        embed.add_field(name="3️⃣ Pas de Pub", value="Pas de publicités non autorisées", inline=False)
        embed.add_field(name="4️⃣ Contenu NSFW", value="Pas de contenu adulte dans les channels généraux", inline=False)
        embed.add_field(name="5️⃣ Obéir aux Modos", value="Écoutez et obéissez aux modérateurs", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="📞 Support", style=discord.ButtonStyle.green)
    async def support_button(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="📞 Support",
            description="Besoin d'aide? Contactez l'équipe de modération",
            color=discord.Color.green()
        )
        embed.add_field(name="Signaler un problème", value="Créez un ticket avec `/ticket`", inline=False)
        embed.add_field(name="Questions", value="Posez vos questions dans #questions", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="🎮 Channels", style=discord.ButtonStyle.gray)
    async def channels_button(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        text_channels = [c for c in guild.text_channels if c.permissions_for(interaction.user).view_channel][:10]
        
        embed = discord.Embed(
            title="🎮 Channels Disponibles",
            color=discord.Color.gray()
        )
        
        for channel in text_channels:
            embed.add_field(name=channel.name, value=channel.mention, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== MEGA PANEL DRAFTBOT STYLE ====================

class PremiumPanelView(ui.View):
    """Panel avec pagination style DraftBot"""
    def __init__(self):
        super().__init__()
        self.current_page = 0
        self.pages = [
            {
                "title": "🎛️ AOTR RF BOT - Centre de Commandes",
                "color": discord.Color.from_rgb(88, 101, 242),
                "description": "Bienvenue dans le centre de commandes! Naviguer pour découvrir toutes les fonctionnalités.",
                "fields": [
                    ("🔨 Modération", "Gestion complète du serveur", True),
                    ("💰 Économie", "Système de monnaie et banque", True),
                    ("🎮 Amusement", "Jeux et divertissement", True),
                    ("📊 Système", "Info serveur et utilisateur", True),
                    ("🎁 Giveaways", "Concours automatisés", True),
                    ("🛡️ Protection", "Sécurité et filtres", True),
                ]
            },
            {
                "title": "🔨 Modération - Gestion du Serveur",
                "color": discord.Color.from_rgb(237, 137, 96),
                "description": "Commandes pour maintenir l'ordre et la sécurité",
                "fields": [
                    ("**/kick** <user>", "Expulser un membre du serveur", False),
                    ("**/ban** <user>", "Bannir définitivement un utilisateur", False),
                    ("**/unban** <user>", "Débannir un utilisateur", False),
                    ("**/mute** <user>", "Empêcher un membre de parler", False),
                    ("**/unmute** <user>", "Retirer le silence", False),
                    ("**/warn** <user>", "Avertir un utilisateur", False),
                    ("**/clear** [nombre]", "Supprimer des messages (max 100)", False),
                    ("**/lock**", "Verrouiller le channel", False),
                    ("**/unlock**", "Déverrouiller le channel", False),
                    ("**/slowmode** <secondes>", "Activer le mode slow", False),
                ]
            },
            {
                "title": "💰 Économie - Système Financier",
                "color": discord.Color.from_rgb(71, 201, 124),
                "description": "Gagnez, dépensez et enrichissez-vous!",
                "fields": [
                    ("**/balance**", "Voir votre solde total", False),
                    ("**/deposit** <montant>", "Déposer argent à la banque", False),
                    ("**/withdraw** <montant>", "Retirer de la banque", False),
                    ("**/daily**", "Récompense quotidienne (500💰)", False),
                    ("**/work**", "Travailler pour gagner (50-200💰)", False),
                    ("**/rob** <@user>", "Voler quelqu'un (50% chance)", False),
                    ("**/leaderboard-money**", "Top 10 des plus riches", False),
                ]
            },
            {
                "title": "🎮 Amusement - Jeux & Divertissement",
                "color": discord.Color.from_rgb(108, 92, 231),
                "description": "Des commandes pour s'amuser seul ou en groupe!",
                "fields": [
                    ("**/dice** [côtés]", "Lancer un dé", False),
                    ("**/coin**", "Pile ou face (aléatoire)", False),
                    ("**/8ball** <question>", "Magic 8 ball - Demande une réponse", False),
                    ("**/joke**", "Obtenir une blague aléatoire", False),
                    ("**/roll** [min] [max]", "Nombre aléatoire (1-100 par défaut)", False),
                    ("**/avatar** [user]", "Voir l'avatar d'un utilisateur", False),
                ]
            },
            {
                "title": "📊 Système - Infos & Statistiques",
                "color": discord.Color.from_rgb(72, 219, 251),
                "description": "Informations sur le serveur et les utilisateurs",
                "fields": [
                    ("**/xp**", "Voir votre profil et vos stats XP", False),
                    ("**/leaderboard**", "Top 10 des utilisateurs (XP)", False),
                    ("**/serverinfo**", "Infos détaillées du serveur", False),
                    ("**/userinfo** [user]", "Profil d'un utilisateur", False),
                    ("**/botinfo**", "Stats du bot (CPU, RAM, etc)", False),
                    ("**/ping**", "Latence du bot en ms", False),
                    ("**/help**", "Afficher l'aide complète", False),
                ]
            },
            {
                "title": "🎁 Giveaways - Concours & Récompenses",
                "color": discord.Color.from_rgb(255, 159, 64),
                "description": "Organisez des concours automatisés!",
                "fields": [
                    ("**/giveaway** <prix> <durée> <winners>", "Créer un giveaway\n\n**Exemple:** `/giveaway Nitro 5 3`\n→ Crée un concours Nitro de 5 minutes avec 3 gagnants\n\n⏰ Les participants cliquent pour rejoindre\n🎯 Gagnants sélectionnés automatiquement", False),
                ]
            },
            {
                "title": "🛡️ Protection - Sécurité & Filtres",
                "color": discord.Color.from_rgb(255, 107, 107),
                "description": "Protégez votre serveur contre les abus",
                "fields": [
                    ("**/add-filter** <mot>", "Ajouter un mot interdit", False),
                    ("**/remove-filter** <mot>", "Retirer un mot du filtre", False),
                    ("**/role-button** <@rôle> [label]", "Créer un bouton pour obtenir un rôle", False),
                    ("**/role-menu**", "Créer un menu dropdown pour rôles", False),
                    ("🛡️ Anti-Spam", "Protection automatique contre le flood", False),
                    ("🛡️ Anti-Invite", "Supprime les invites Discord", False),
                    ("🛡️ Anti-Lien", "Bloque les liens (http/https)", False),
                ]
            },
            {
                "title": "🎟️ Support & Communauté",
                "color": discord.Color.from_rgb(156, 39, 176),
                "description": "Interagissez avec la communauté",
                "fields": [
                    ("**/ticket-setup**", "Créer le système de tickets [ADMIN]", False),
                    ("**/suggest** <texte>", "Faire une suggestion", False),
                    ("**/poll** <question> <opt1> <opt2> [opt3]", "Créer un sondage avec votes", False),
                    ("**/setup-suggestions**", "Configurer les suggestions [ADMIN]", False),
                ]
            },
        ]

    def create_embed(self):
        page = self.pages[self.current_page]
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=page["color"]
        )
        
        for field_name, field_value, inline in page["fields"]:
            embed.add_field(name=field_name, value=field_value, inline=inline)
        
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • AOTR RF BOT")
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        return embed

    @ui.button(label="◀️ Précédent", style=discord.ButtonStyle.gray, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page = (self.current_page - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.create_embed())

    @ui.button(label="Accueil", style=discord.ButtonStyle.blurple, emoji="🏠")
    async def home_button(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page = 0
        await interaction.response.edit_message(embed=self.create_embed())

    @ui.button(label="Suivant ▶️", style=discord.ButtonStyle.gray, emoji="▶️")
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page = (self.current_page + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.create_embed())

    @ui.button(label="❌ Fermer", style=discord.ButtonStyle.red, emoji="❌")
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()


# ==================== COGS ====================

class Panels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Affiche le panel principal")
    async def panel_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎛️ Panel Principal",
            description="Bienvenue! Utilisez les boutons ci-dessous pour naviguer",
            color=discord.Color.blurple()
        )
        embed.add_field(name="👤 Profil", value="Voir votre profil et vos stats", inline=False)
        embed.add_field(name="🏆 Leaderboard", value="Voir le top XP", inline=False)
        embed.add_field(name="ℹ️ Serveur", value="Infos du serveur", inline=False)
        
        await interaction.response.send_message(embed=embed, view=MainPanelView(self.bot))

    @app_commands.command(name="admin-panel", description="Panel administrateur (admin only)")
    async def admin_panel_cmd(self, interaction: discord.Interaction):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔐 Panel Administrateur",
            description="Accédez aux outils de modération et statistiques",
            color=discord.Color.red()
        )
        embed.add_field(name="🔨 Modération", value="Accès aux commandes de modération", inline=False)
        embed.add_field(name="📊 Statistiques", value="Stats du serveur", inline=False)
        embed.add_field(name="⚙️ Configuration", value="Configurer le bot", inline=False)
        
        await interaction.response.send_message(embed=embed, view=AdminPanelView(self.bot))

    @app_commands.command(name="userinfo-panel", description="Panel profil d'un utilisateur")
    @app_commands.describe(user="L'utilisateur à afficher")
    async def userinfo_panel_cmd(self, interaction: discord.Interaction, user: discord.Member):
        embed = discord.Embed(
            title=f"👤 {user.name}",
            description="Cliquez sur les boutons pour plus d'infos",
            color=user.color
        )
        embed.set_thumbnail(url=user.avatar.url)
        
        await interaction.response.send_message(embed=embed, view=UserPanelView(self.bot, user))

    @app_commands.command(name="server-panel", description="Panel du serveur")
    async def server_panel_cmd(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🎮 {guild.name}",
            description="Bienvenue! Utilisez les boutons pour explorer",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        
        await interaction.response.send_message(embed=embed, view=ServerPanelView(self.bot))

    @app_commands.command(name="commands-panel", description="📋 Panel avec TOUTES les commandes")
    async def commands_panel_cmd(self, interaction: discord.Interaction):
        view = PremiumPanelView()
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Panels(bot))
