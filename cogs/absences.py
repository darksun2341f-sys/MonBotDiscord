import discord
from discord.ext import commands
from discord import app_commands, ui
import json
from pathlib import Path
from datetime import datetime, timedelta

class AbsenceModal(ui.Modal, title="📋 Déclarer une Absence"):
    """Modal pour déclarer une absence"""
    
    days = ui.TextInput(label="Nombre de jours", placeholder="Ex: 10", required=True)
    return_date = ui.TextInput(label="Date de retour (JJ/MM/YYYY)", placeholder="Ex: 25/07/2026", required=True)
    reason = ui.TextInput(label="Raison de l'absence", placeholder="Vacances, congé, etc", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Valider les entrées
            num_days = int(self.days.value)
            if num_days < 1:
                await interaction.response.send_message("❌ Le nombre de jours doit être ≥ 1", ephemeral=True)
                return
            
            # Parser la date
            return_date = datetime.strptime(self.return_date.value, "%d/%m/%Y")
            today = datetime.now()
            
            if return_date < today:
                await interaction.response.send_message("❌ La date de retour doit être dans le futur!", ephemeral=True)
                return
            
            # Sauvegarder l'absence
            absences_file = Path(__file__).parent.parent / "database" / "absences.json"
            absences_file.parent.mkdir(parents=True, exist_ok=True)
            
            if absences_file.exists():
                with open(absences_file, 'r', encoding='utf-8-sig') as f:
                    absences_data = json.load(f)
            else:
                absences_data = {"absences": []}
            
            absence_entry = {
                "user_id": interaction.user.id,
                "username": interaction.user.name,
                "days": num_days,
                "return_date": return_date.strftime("%d/%m/%Y"),
                "reason": self.reason.value or "Non spécifiée",
                "start_date": today.strftime("%d/%m/%Y"),
                "timestamp": datetime.now().isoformat()
            }
            
            absences_data["absences"].append(absence_entry)
            
            with open(absences_file, 'w', encoding='utf-8-sig') as f:
                json.dump(absences_data, f, ensure_ascii=False, indent=2)
            
            # Réponse
            embed = discord.Embed(
                title="✅ Absence Déclarée",
                description="Votre absence a été enregistrée!",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Membre", value=interaction.user.mention, inline=True)
            embed.add_field(name="📅 Durée", value=f"{num_days} jours", inline=True)
            embed.add_field(name="🗓️ Retour prévu", value=return_date.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="📝 Raison", value=self.reason.value or "Non spécifiée", inline=False)
            embed.add_field(name="⏰ Date de départ", value=today.strftime("%d/%m/%Y à %H:%M"), inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=False)
        
        except ValueError:
            await interaction.response.send_message("❌ Format de date invalide! Utilisez JJ/MM/YYYY", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)


class ReturnButton(ui.View):
    """Bouton pour marquer le retour"""
    
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
    
    @ui.button(label="✅ Marqué comme Retour", style=discord.ButtonStyle.green, emoji="✅")
    async def return_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous ne pouvez marquer que votre propre retour!", ephemeral=True)
            return
        
        # Charger les absences
        absences_file = Path(__file__).parent.parent / "database" / "absences.json"
        
        if not absences_file.exists():
            await interaction.response.send_message("❌ Aucune absence trouvée!", ephemeral=True)
            return
        
        with open(absences_file, 'r', encoding='utf-8-sig') as f:
            absences_data = json.load(f)
        
        # Trouver et supprimer l'absence
        removed = False
        for i, absence in enumerate(absences_data["absences"]):
            if absence["user_id"] == self.user_id:
                removed_absence = absences_data["absences"].pop(i)
                removed = True
                break
        
        if not removed:
            await interaction.response.send_message("❌ Aucune absence active pour cet utilisateur!", ephemeral=True)
            return
        
        # Sauvegarder
        with open(absences_file, 'w', encoding='utf-8-sig') as f:
            json.dump(absences_data, f, ensure_ascii=False, indent=2)
        
        embed = discord.Embed(
            title="✅ Retour Enregistré",
            description="Bienvenue de retour!",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Membre", value=f"<@{self.user_id}>", inline=True)
        embed.add_field(name="📝 Raison d'absence", value=removed_absence.get("reason", "Non spécifiée"), inline=True)
        embed.add_field(name="📅 Durée totale", value=f"{removed_absence['days']} jours", inline=True)
        embed.add_field(name="📅 Départ", value=removed_absence["start_date"], inline=True)
        embed.add_field(name="🔙 Retour anticipé", value=datetime.now().strftime("%d/%m/%Y à %H:%M"), inline=True)
        
        await interaction.response.send_message(embed=embed)
        await interaction.message.edit(view=None)


class Absences(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.absences_file = Path(__file__).parent.parent / "database" / "absences.json"

    def load_absences(self):
        """Charge les absences depuis le fichier"""
        if self.absences_file.exists():
            with open(self.absences_file, 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        return {"absences": []}

    @app_commands.command(name="absence-declare", description="📋 Déclarer une absence")
    async def absence_declare(self, interaction: discord.Interaction):
        """Ouvre le modal pour déclarer une absence"""
        await interaction.response.send_modal(AbsenceModal())

    @app_commands.command(name="absence-list", description="📋 Voir les absences actuelles")
    async def absence_list(self, interaction: discord.Interaction):
        """Affiche toutes les absences actuelles"""
        absences_data = self.load_absences()
        
        if not absences_data["absences"]:
            embed = discord.Embed(
                title="📋 Absences Actuelles",
                description="Aucune absence déclarée",
                color=discord.Color.greyple()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Absences Actuelles",
            description=f"Total: {len(absences_data['absences'])} absence(s)",
            color=discord.Color.blue()
        )
        
        for absence in absences_data["absences"]:
            emoji = "⏰" if datetime.strptime(absence["start_date"], "%d/%m/%Y") == datetime.now().date() else "📅"
            
            embed.add_field(
                name=f"{emoji} {absence['username']} ({absence['user_id']})",
                value=f"🗓️ Départ: {absence['start_date']}\n"
                      f"🔙 Retour: {absence['return_date']}\n"
                      f"⏱️ Durée: {absence['days']} jours\n"
                      f"📝 Raison: {absence['reason']}",
                inline=False
            )
        
        embed.set_footer(text="Utilisez /absence-panel pour gérer les absences")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="absence-panel", description="🎛️ Panel de gestion des absences [ADMIN]")
    async def absence_panel(self, interaction: discord.Interaction):
        """Affiche le panel de gestion des absences"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        absences_data = self.load_absences()
        
        embed = discord.Embed(
            title="🎛️ Panel de Gestion des Absences",
            description="Gérez les absences des membres",
            color=discord.Color.blue()
        )
        
        if not absences_data["absences"]:
            embed.add_field(
                name="📭 Aucune absence",
                value="Il n'y a actuellement aucune absence déclarée",
                inline=False
            )
        else:
            for absence in absences_data["absences"]:
                return_dt = datetime.strptime(absence["return_date"], "%d/%m/%Y")
                days_left = (return_dt - datetime.now()).days
                
                status = "🟢 En cours" if days_left > 0 else "🔴 Expiré"
                
                embed.add_field(
                    name=f"👤 {absence['username']} {status}",
                    value=f"🗓️ Dates: {absence['start_date']} → {absence['return_date']}\n"
                          f"⏱️ Jours restants: {max(0, days_left)}\n"
                          f"📝 Raison: {absence['reason']}",
                    inline=False
                )
        
        embed.set_footer(text="📋 Panel d'administration des absences")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="absence-remove", description="❌ Retirer une absence [ADMIN]")
    @app_commands.describe(user="Le membre concerné")
    async def absence_remove(self, interaction: discord.Interaction, user: discord.User):
        """Retire l'absence d'un utilisateur"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)
            return
        
        absences_data = self.load_absences()
        
        removed = False
        removed_absence = None
        for i, absence in enumerate(absences_data["absences"]):
            if absence["user_id"] == user.id:
                removed_absence = absences_data["absences"].pop(i)
                removed = True
                break
        
        if not removed:
            await interaction.response.send_message(f"❌ Aucune absence trouvée pour {user.mention}!", ephemeral=True)
            return
        
        with open(self.absences_file, 'w', encoding='utf-8-sig') as f:
            json.dump(absences_data, f, ensure_ascii=False, indent=2)
        
        embed = discord.Embed(
            title="✅ Absence Supprimée",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Membre", value=user.mention, inline=True)
        embed.add_field(name="📅 Durée", value=f"{removed_absence['days']} jours", inline=True)
        embed.add_field(name="📝 Raison", value=removed_absence['reason'], inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="my-absence", description="📋 Voir ma propre absence")
    async def my_absence(self, interaction: discord.Interaction):
        """Affiche l'absence personnelle de l'utilisateur"""
        absences_data = self.load_absences()
        
        user_absence = None
        for absence in absences_data["absences"]:
            if absence["user_id"] == interaction.user.id:
                user_absence = absence
                break
        
        if not user_absence:
            embed = discord.Embed(
                title="📋 Ma Absence",
                description="Vous n'avez aucune absence déclarée",
                color=discord.Color.greyple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        return_dt = datetime.strptime(user_absence["return_date"], "%d/%m/%Y")
        days_left = (return_dt - datetime.now()).days
        
        embed = discord.Embed(
            title="📋 Mon Absence",
            color=discord.Color.blue()
        )
        embed.add_field(name="📅 Départ", value=user_absence["start_date"], inline=True)
        embed.add_field(name="🔙 Retour prévu", value=user_absence["return_date"], inline=True)
        embed.add_field(name="⏱️ Jours restants", value=str(max(0, days_left)), inline=True)
        embed.add_field(name="📝 Raison", value=user_absence["reason"], inline=False)
        
        # Ajouter le bouton de retour
        view = ReturnButton(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Absences(bot))
