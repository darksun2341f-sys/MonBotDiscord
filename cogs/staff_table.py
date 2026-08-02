import unicodedata

import discord
from discord import app_commands
from discord.ext import commands
from utils.authorization import has_bot_administrator_access


EXCLUDED_ROLE_NAMES = {"debutant", "confirmer", "confirme"}
DIRECTION_ROLE_NAMES = {
    "owner",
    "co-owner",
    "co owner",
    "coowner",
    "administrateur",
    "administrator",
    "architecte",
    "architect",
}
STAFF_ROLE_NAMES = {
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
MAX_MEMBERS_PER_ROLE = 16


def normalized_role_name(name: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", name.casefold())
        if unicodedata.category(character) != "Mn"
    ).strip()


def role_by_name(guild: discord.Guild, name: str) -> discord.Role | None:
    return next(
        (role for role in guild.roles if normalized_role_name(role.name) == name), None
    )


def staff_roles(guild: discord.Guild) -> list[discord.Role]:
    owner = role_by_name(guild, "owner")
    helper = role_by_name(guild, "helper")
    fallback_names = DIRECTION_ROLE_NAMES | STAFF_ROLE_NAMES

    if owner is not None and helper is not None:
        lowest_position = min(owner.position, helper.position)
        highest_position = max(owner.position, helper.position)
        allowed = lambda role: lowest_position <= role.position <= highest_position
    else:
        allowed = lambda role: normalized_role_name(role.name) in fallback_names

    return [
        role
        for role in reversed(guild.roles)
        if not role.is_default()
        and not role.managed
        and normalized_role_name(role.name) not in EXCLUDED_ROLE_NAMES
        and allowed(role)
    ]


def member_line(members: list[discord.Member]) -> str:
    if not members:
        return "| Aucun membre"

    mentions = "  ".join(member.mention for member in members[:MAX_MEMBERS_PER_ROLE])
    if len(members) > MAX_MEMBERS_PER_ROLE:
        mentions += f"\n| + {len(members) - MAX_MEMBERS_PER_ROLE} autre(s)"
    return f"| {mentions}"


def add_role_section(
    embed: discord.Embed,
    title: str,
    roles: list[discord.Role],
    staff_member_ids: set[int],
) -> int:
    if not roles:
        return 0

    embed.add_field(name=title, value="----------------", inline=False)
    for role in roles:
        members = [member for member in role.members if not member.bot]
        staff_member_ids.update(member.id for member in members)
        member_count = "membre" if len(members) == 1 else "membres"
        embed.add_field(
            name=f"`{len(members)} {member_count}`",
            value=f"{role.mention}\n{member_line(members)}",
            inline=False,
        )
    return len(roles)


def build_staff_embed(guild: discord.Guild, bot: commands.Bot) -> discord.Embed:
    embed = discord.Embed(
        title=f"{bot.user.display_name if bot.user else 'Staff'} | Tableau du staff",
        description="Tableau de bord des membres du staff.",
        color=discord.Color.from_rgb(88, 101, 242),
        timestamp=discord.utils.utcnow(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    roles = staff_roles(guild)
    direction_roles = [
        role for role in roles if normalized_role_name(role.name) in DIRECTION_ROLE_NAMES
    ]
    team_roles = [role for role in roles if role not in direction_roles]
    staff_member_ids: set[int] = set()
    displayed_roles = add_role_section(
        embed, "DIRECTION", direction_roles, staff_member_ids
    )
    displayed_roles += add_role_section(
        embed, "EQUIPE STAFF", team_roles, staff_member_ids
    )

    if displayed_roles == 0:
        embed.add_field(
            name="Aucun role staff trouve",
            value="Les roles doivent etre compris entre helper et owner.",
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{len(staff_member_ids)} membre(s) dans l'equipe staff | "
            "Mis a jour en temps reel"
        ),
        icon_url=guild.icon.url if guild.icon else None,
    )
    return embed


class StaffTableView(discord.ui.View):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Actualiser",
        style=discord.ButtonStyle.secondary,
        custom_id="staff_table_refresh",
    )
    async def refresh(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not has_bot_administrator_access(interaction):
            await interaction.response.send_message(
                "Cette action est reservee aux administrateurs.", ephemeral=True
            )
            return

        guild = interaction.guild
        if guild is None:
            return
        await interaction.response.edit_message(
            embed=build_staff_embed(guild, self.bot),
            view=self,
            allowed_mentions=discord.AllowedMentions(roles=True, users=False),
        )


class StaffTable(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="tableau-staff",
        description="Affiche les roles du staff et leurs membres.",
    )
    @app_commands.guild_only()
    @app_commands.check(has_bot_administrator_access)
    async def staff_table(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return
        await interaction.response.send_message(
            embed=build_staff_embed(guild, self.bot),
            view=StaffTableView(self.bot),
            allowed_mentions=discord.AllowedMentions(roles=True, users=False),
        )


async def setup(bot: commands.Bot) -> None:
    bot.add_view(StaffTableView(bot))
    await bot.add_cog(StaffTable(bot))
