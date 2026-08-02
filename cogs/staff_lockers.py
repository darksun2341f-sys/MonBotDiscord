import asyncio
import unicodedata

import discord
from discord.ext import commands


STAFF_ROLE_NAMES = {
    "owner",
    "co-owner",
    "co owner",
    "coowner",
    "administrateur",
    "administrator",
    "architecte",
    "architect",
    "staff-manager",
    "staff",
    "staff-test",
    "responsable",
    "responsable moderateur",
    "responsable animateur",
    "responsable helper",
    "moderateur",
    "moderator",
    "animateur",
    "helper",
}
LOCKER_CATEGORY_NAMES = {"casier", "casiers"}
LOCKER_CATEGORY_NAME = "casier"


def normalized_role_name(name: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", name.casefold())
        if unicodedata.category(character) != "Mn"
    ).strip()


def is_staff_member(member: discord.Member) -> bool:
    return any(normalized_role_name(role.name) in STAFF_ROLE_NAMES for role in member.roles)


def build_member_info_embed(member: discord.Member) -> discord.Embed:
    joined_at = member.joined_at
    roles = [role.mention for role in member.roles if not role.is_default()]
    roles_text = " ".join(roles) or "Aucun role"
    if len(roles_text) > 1_024:
        roles_text = f"{roles_text[:1_000]} ..."

    if joined_at is None:
        arrival_date = "Inconnue"
        seniority = "Inconnue"
    else:
        timestamp = int(joined_at.timestamp())
        arrival_date = f"<t:{timestamp}:F>"
        seniority = f"<t:{timestamp}:R>"

    embed = discord.Embed(
        title="Informations du membre",
        description=f"Fiche privee de {member.mention}",
        color=discord.Color.dark_teal(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID Discord", value=f"`{member.id}`", inline=False)
    embed.add_field(name="Date d'arrivee", value=arrival_date, inline=False)
    embed.add_field(name="Roles", value=roles_text, inline=False)
    embed.add_field(name="Anciennete", value=seniority, inline=False)
    return embed


class StaffLockers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.locks: dict[int, asyncio.Lock] = {}

    def guild_lock(self, guild_id: int) -> asyncio.Lock:
        return self.locks.setdefault(guild_id, asyncio.Lock())

    async def create_locker(self, member: discord.Member) -> None:
        guild = member.guild
        async with self.guild_lock(guild.id):
            category = next(
                (
                    item
                    for item in guild.categories
                    if item.name.casefold() in LOCKER_CATEGORY_NAMES
                ),
                None,
            )
            if category is None:
                category = await guild.create_category(
                    LOCKER_CATEGORY_NAME,
                    reason="Creation de la categorie des casiers staff",
                )

            topic = f"Casier prive du membre {member.id}"
            if any(channel.topic == topic for channel in category.text_channels):
                return

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                ),
            }
            if guild.me is not None:
                overwrites[guild.me] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    read_message_history=True,
                )

            locker = await guild.create_text_channel(
                "casier",
                category=category,
                overwrites=overwrites,
                topic=topic,
                reason=f"Creation du casier staff de {member}",
            )
            await locker.send(
                embed=build_member_info_embed(member),
                allowed_mentions=discord.AllowedMentions.none(),
            )

    async def delete_locker(self, member: discord.Member) -> None:
        guild = member.guild
        async with self.guild_lock(guild.id):
            topic = f"Casier prive du membre {member.id}"
            for category in guild.categories:
                for channel in category.text_channels:
                    if channel.topic == topic:
                        await channel.delete(
                            reason=f"Suppression du casier de {member}: plus de role staff"
                        )
                        return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if not member.bot and is_staff_member(member):
            await self.create_locker(member)

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        if not after.bot and not is_staff_member(before) and is_staff_member(after):
            await self.create_locker(after)
        elif not after.bot and is_staff_member(before) and not is_staff_member(after):
            await self.delete_locker(after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StaffLockers(bot))
