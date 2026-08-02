import discord
from discord.ext import commands

from cogs.staff_lockers import is_staff_member


EFFECTIFS_CHANNEL_NAME = "effectifs"


class StaffRoleLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        if after.bot or not (is_staff_member(before) or is_staff_member(after)):
            return

        added_roles = [
            role
            for role in after.roles
            if role not in before.roles
            and not role.is_default()
        ]
        removed_roles = [
            role
            for role in before.roles
            if role not in after.roles and not role.is_default()
        ]
        if not added_roles and not removed_roles:
            return

        channel = discord.utils.find(
            lambda item: item.name.casefold() == EFFECTIFS_CHANNEL_NAME,
            after.guild.text_channels,
        )
        if channel is None:
            return

        for role in added_roles:
            await channel.send(
                f"{role.mention} > **{after.display_name}**",
                allowed_mentions=discord.AllowedMentions(roles=True, users=False),
            )
        for role in removed_roles:
            await channel.send(
                f"{role.mention} < **{after.display_name}**",
                allowed_mentions=discord.AllowedMentions(roles=True, users=False),
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StaffRoleLog(bot))
