import discord
from discord.ext import commands
from discord import app_commands, ui
from utils.authorization import has_bot_administrator_access

class SuggestionView(ui.View):
    def __init__(self, bot, suggestion_id, author_id):
        super().__init__()
        self.bot = bot
        self.suggestion_id = suggestion_id
        self.author_id = author_id

    @ui.button(label="👍 0", style=discord.ButtonStyle.green)
    async def upvote(self, interaction: discord.Interaction, button: ui.Button):
        current_count = int(button.label.split()[1])
        button.label = f"👍 {current_count + 1}"
        await interaction.response.defer()
        await interaction.message.edit(view=self)

    @ui.button(label="👎 0", style=discord.ButtonStyle.red)
    async def downvote(self, interaction: discord.Interaction, button: ui.Button):
        current_count = int(button.label.split()[1])
        button.label = f"👎 {current_count + 1}"
        await interaction.response.defer()
        await interaction.message.edit(view=self)

    @ui.button(label="💬 Répondre", style=discord.ButtonStyle.gray)
    async def reply(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(f"✅ Veuillez répondre dans le chat!", ephemeral=True)

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestion_counter = 0

    @app_commands.command(name="suggest", description="Envoyer une suggestion")
    @app_commands.describe(suggestion="Votre suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        self.suggestion_counter += 1
        
        embed = discord.Embed(
            title=f"💡 Suggestion #{self.suggestion_counter}",
            description=suggestion,
            color=discord.Color.blurple()
        )
        embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
        embed.set_footer(text=f"ID: {self.suggestion_counter}")
        
        await interaction.response.send_message(embed=embed, view=SuggestionView(self.bot, self.suggestion_counter, interaction.user.id))

    @app_commands.command(name="setup-suggestions", description="Configure le canal suggestions")
    async def setup_suggestions(self, interaction: discord.Interaction):
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        guild = interaction.guild
        
        # Créer le channel
        suggestions_channel = discord.utils.get(guild.text_channels, name="suggestions")
        if not suggestions_channel:
            try:
                suggestions_channel = await guild.create_text_channel("suggestions")
            except:
                await interaction.response.send_message("❌ Erreur création du channel!", ephemeral=True)
                return
        
        embed = discord.Embed(
            title="💡 Suggestions",
            description="Utilisez `/suggest` pour envoyer une suggestion!",
            color=discord.Color.blurple()
        )
        
        await suggestions_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Channel suggestions créé: {suggestions_channel.mention}")

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
