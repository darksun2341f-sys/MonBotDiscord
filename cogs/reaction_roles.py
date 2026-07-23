import discord
from discord.ext import commands
from discord import app_commands, ui
import json
from pathlib import Path

class RoleView(ui.View):
    def __init__(self, bot, roles_dict):
        super().__init__()
        self.bot = bot
        self.roles_dict = roles_dict

    @ui.select(
        placeholder="Choisissez un rôle",
        min_values=0,
        max_values=5,
        options=[
            discord.SelectOption(label="Option 1", value="role_1"),
            discord.SelectOption(label="Option 2", value="role_2"),
        ]
    )
    async def select_roles(self, interaction: discord.Interaction, select: ui.Select):
        selected_values = select.values
        member = interaction.user
        
        for role_id in self.roles_dict.values():
            role = interaction.guild.get_role(role_id)
            if role:
                await member.remove_roles(role)
        
        for value in selected_values:
            role_id = self.roles_dict.get(value)
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
        
        await interaction.response.send_message(f"✅ Rôles mis à jour!", ephemeral=True)

class ButtonRoleView(ui.View):
    def __init__(self, bot, role_id):
        super().__init__()
        self.bot = bot
        self.role_id = role_id

    @ui.button(label="Obtenir le Rôle", style=discord.ButtonStyle.blurple)
    async def get_role(self, interaction: discord.Interaction, button: ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if role:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"✅ Rôle {role.mention} supprimé!", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Rôle {role.mention} ajouté!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Rôle introuvable!", ephemeral=True)

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="role-button", description="Crée un bouton pour un rôle")
    @app_commands.describe(
        role="Le rôle à assigner",
        label="Label du bouton"
    )
    async def role_button(self, interaction: discord.Interaction, role: discord.Role, label: str = "Obtenir Rôle"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="👥 Sélecteur de Rôles",
            description=f"Cliquez pour obtenir le rôle {role.mention}",
            color=role.color
        )
        
        view = ButtonRoleView(self.bot, role.id)
        view.children[0].label = label
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="role-menu", description="Crée un menu déroulant pour les rôles")
    async def role_menu(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        roles = interaction.guild.roles[1:11]  # Les 10 premiers rôles
        
        if not roles:
            await interaction.response.send_message("❌ Pas de rôles disponibles!", ephemeral=True)
            return
        
        roles_dict = {}
        options = []
        
        for i, role in enumerate(roles):
            key = f"role_{i}"
            roles_dict[key] = role.id
            options.append(discord.SelectOption(label=role.name, value=key))
        
        embed = discord.Embed(
            title="👥 Sélecteur de Rôles",
            description="Choisissez les rôles que vous voulez",
            color=discord.Color.blurple()
        )
        
        view = RoleView(self.bot, roles_dict)
        view.children[0].options = options
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
