BOT_OPERATOR_IDS = frozenset({673215452284977172})


def is_bot_operator(user) -> bool:
    return getattr(user, "id", None) in BOT_OPERATOR_IDS


def has_bot_administrator_access(interaction) -> bool:
    if is_bot_operator(interaction.user):
        return True

    permissions = getattr(interaction.user, "guild_permissions", None)
    return bool(permissions and permissions.administrator)


def has_permission(interaction, permission_name: str) -> bool:
    if is_bot_operator(interaction.user):
        return True

    permissions = getattr(interaction.user, "guild_permissions", None)
    if not permissions:
        return False

    return bool(getattr(permissions, permission_name, False))
