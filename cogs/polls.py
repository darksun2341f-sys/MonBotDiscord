import discord
from discord.ext import commands
from discord import app_commands

class PollView(discord.ui.View):
    def __init__(self, options):
        super().__init__()
        self.votes = {i: 0 for i in range(len(options))}
        self.options = options
        self.voted = set()

    @discord.ui.button(label="Option 1", style=discord.ButtonStyle.blurple)
    async def option_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voted:
            await interaction.response.send_message("❌ Vous avez déjà voté!", ephemeral=True)
            return
        
        self.votes[0] += 1
        self.voted.add(interaction.user.id)
        await interaction.response.defer()
        await self.update_message(interaction)

    @discord.ui.button(label="Option 2", style=discord.ButtonStyle.green)
    async def option_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voted:
            await interaction.response.send_message("❌ Vous avez déjà voté!", ephemeral=True)
            return
        
        self.votes[1] += 1
        self.voted.add(interaction.user.id)
        await interaction.response.defer()
        await self.update_message(interaction)

    @discord.ui.button(label="Option 3", style=discord.ButtonStyle.red)
    async def option_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.voted:
            await interaction.response.send_message("❌ Vous avez déjà voté!", ephemeral=True)
            return
        
        self.votes[2] += 1
        self.voted.add(interaction.user.id)
        await interaction.response.defer()
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        total_votes = sum(self.votes.values())
        
        embed_text = ""
        for i, (option, votes) in enumerate(zip(self.options, self.votes.values())):
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            embed_text += f"\n{option}: {votes} vote(s) ({percentage:.1f}%)"
        
        embed = discord.Embed(
            title="📊 Sondage",
            description=embed_text or "Aucun vote pour le moment",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Total: {total_votes} vote(s)")
        
        await interaction.message.edit(embed=embed)

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Crée un sondage")
    @app_commands.describe(
        question="La question du sondage",
        option1="Première option",
        option2="Deuxième option",
        option3="Troisième option (optionnel)"
    )
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None):
        options = [option1, option2]
        if option3:
            options.append(option3)
        
        embed = discord.Embed(
            title="📊 Sondage",
            description=question,
            color=discord.Color.blurple()
        )
        
        for i, option in enumerate(options, 1):
            embed.add_field(name=f"Option {i}", value=option, inline=False)
        
        view = PollView(options)
        
        # Adapter les boutons
        for i, button in enumerate(view.children[:len(options)]):
            button.label = options[i]
        
        # Masquer les boutons non utilisés
        for button in view.children[len(options):]:
            button.disabled = True
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Polls(bot))
