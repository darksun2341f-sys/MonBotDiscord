from utils.authorization import has_bot_administrator_access, has_permission


class DummyPermissions:
    def __init__(self, administrator=False, manage_messages=False):
        self.administrator = administrator
        self.manage_messages = manage_messages


class DummyUser:
    def __init__(self, user_id, permissions=None):
        self.id = user_id
        self.guild_permissions = permissions or DummyPermissions()


class DummyInteraction:
    def __init__(self, user):
        self.user = user


def test_bot_operator_bypasses_permission_checks():
    interaction = DummyInteraction(DummyUser(673215452284977172, DummyPermissions()))

    assert has_bot_administrator_access(interaction) is True
    assert has_permission(interaction, "manage_messages") is True
