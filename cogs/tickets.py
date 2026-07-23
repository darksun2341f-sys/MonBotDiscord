import discord
from discord.ext import commands
from discord import app_commands, ui
import json
from pathlib import Path

class TicketView(ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @ui.button(label="📩 Créer un Ticket", style=discord.ButtonStyle.blurple, emoji="📩")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        category_name = "Tickets"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            try:
                category = await guild.create_category(category_name)
                await category.edit(position=0)
            except:
                await interaction.response.send_message("❌ Erreur création de catégorie!", ephemeral=True)
                return
        
        channel_name = f"ticket-{interaction.user.name}"
        
        try:
            ticket_channel = await guild.create_text_channel(
                channel_name,
                category=category,
                topic=f"Ticket de {interaction.user} - {interaction.user.id}"
            )
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            
            for overwrite_target, perms in overwrites.items():
                await ticket_channel.set_permissions(overwrite_target, overwrite=perms)
            
            embed = discord.Embed(
                title="🎫 Nouveau Ticket",
                description=f"Bienvenue {interaction.user.mention}!\nL'équipe du support va vous aider bientôt.",
                color=discord.Color.blurple()
            )
            
            await ticket_channel.send(embed=embed, view=CloseTicketView(self.bot, interaction.user))
            await interaction.response.send_message(f"✅ Ticket créé: {ticket_channel.mention}", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

class CloseTicketView(ui.View):
    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    @ui.button(label="Fermer", style=discord.ButtonStyle.red, emoji="❌")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.guild_permissions.manage_channels or interaction.user == self.user:
            await interaction.response.defer()
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Vous n'avez pas la permission!", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket-setup", description="Configure le système de tickets")
    async def ticket_setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎫 Système de Tickets",
            description="Cliquez sur le bouton ci-dessous pour créer un ticket",
            color=discord.Color.blurple()
        )
        
        await interaction.response.send_message(embed=embed, view=TicketView(self.bot))

async def setup(bot):
    await bot.add_cog(Tickets(bot))
