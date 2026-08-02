import discord
from discord import app_commands
from discord.ext import commands
from utils.authorization import has_bot_administrator_access


class Announcements(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="annonce", description="Publie une annonce dans le salon choisi.")
    @app_commands.guild_only()
    @app_commands.check(has_bot_administrator_access)
    @app_commands.describe(
        channel="Le salon dans lequel publier l'annonce",
        message="Le texte a publier",
    )
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
    ) -> None:
        if len(message) > 2_000:
            await interaction.response.send_message(
                "Une annonce ne peut pas depasser 2 000 caracteres.", ephemeral=True
            )
            return

        await channel.send(message)
        await interaction.response.send_message(
            f"Annonce envoyee dans {channel.mention}.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Announcements(bot))
