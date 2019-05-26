from buildabot import Typer


class Setting:
    def __init__(self, us, name: str, expected_type, desc, ignore=False, default=None, is_list=False):
        from features.snowflake_settings.settings import SnowflakeSettings
        self.settings: SnowflakeSettings = us
        self.name = name
        self.key = name.replace(' ', '_').lower()
        self.description = desc
        self.type = expected_type
        self.ignore = ignore
        self.default = default
        self.list = is_list

    def set(self, user, value, context=None):
        check_value = Typer.check_arg(value, self.type, context=context)
        if self.type == 'bool':
            value = check_value

        if value == self.default:
            self.settings.del_setting(user, self.key)
        else:
            self.settings.set_setting(user, self.key, value)

    def get(self, user, context=None):
        value = self.settings.get_setting(user, self.key, default=self.default)
        return Typer.check_arg(value, self.type, context=context)
