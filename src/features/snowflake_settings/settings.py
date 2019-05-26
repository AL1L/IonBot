import json

from buildabot import Feature, Typer

from features.snowflake_settings.setting import Setting


class SnowflakeSettings(Feature):

    def __init__(self, fm, m):
        super().__init__(fm, m)
        self.settings = {}
        from features.database import Database
        self.database: Database = None
        self.presets = {}

    def register_config_value(self, category, key, expected_type, description: str, ignore=False, default=None):
        from buildabot import Typer

        if not Typer.is_valid_type(expected_type):
            raise ValueError('Type {} not found'.format(expected_type))

        value = Setting(self, key, expected_type, description,
                        ignore=ignore, default=default)

        if category not in self.presets:
            self.presets[category] = {}

        self.presets[category][value.key] = value

        self.guild_settings = {}
        self.member_settings = {}
        self.channel_settings = {}
        self.role_settings = {}

    async def on_enable(self):
        self.database = self.feature_manager.get_feature("Database")

        self.database.execute(
            """CREATE TABLE IF NOT EXISTS `settings` (
                `id` BIGINT NOT NULL PRIMARY KEY UNIQUE,
                `settings` LONGTEXT NOT NULL
            );""", no_return=True)
        self.database.commit()

        def json_type(arg, context, bot=None):
            return [json.loads(arg)]
        Typer.define_type('json', json_type)

    @staticmethod
    def _get_snowflake(snowflake):
        if hasattr(snowflake, 'id'):
            snowflake = snowflake.id

        if not isinstance(snowflake, int):
            raise ValueError('Invalid snowflake')

        return snowflake

    def get_settings(self, snowflake):
        snowflake = SnowflakeSettings._get_snowflake(snowflake)

        if snowflake in self.settings:
            return self.settings[snowflake]

        q = self.database.execute(
            'SELECT settings FROM settings WHERE `id` = %s', [snowflake])

        r = q.fetch()

        if r is None:
            self.settings[snowflake] = {}
            return {}

        j = json.loads(r[0])

        self.settings[snowflake] = j

        return j

    def set_settings(self, snowflake, settings: dict):
        c = self.get_settings(snowflake)
        snowflake = SnowflakeSettings._get_snowflake(snowflake)

        j = json.dumps(settings)

        if len(c) == 0:
            if len(settings) > 0:
                self.database.execute('INSERT INTO `settings` VALUES (%s, %s)', [
                                      snowflake, j], no_return=True)
                self.settings[snowflake] = settings
        elif len(settings) > 0:
            self.database.execute('UPDATE `settings` SET `settings` = %s WHERE `id` = %s', [j, snowflake],
                                  no_return=True)
            self.settings[snowflake] = settings

        if len(settings) == 0:
            self.database.execute('DELETE FROM `settings` WHERE `id` = %s', [
                                  snowflake], no_return=True)
            del self.settings[snowflake]
        self.database.commit()

    def get_setting(self, snowflake, key, default=None):
        c = self.get_settings(snowflake)

        if key not in c:
            return default

        return c[key]

    def set_setting(self, snowflake, key, value):
        c = dict(self.get_settings(snowflake))

        c[key] = value

        self.set_settings(snowflake, c)

    def del_setting(self, snowflake, key):
        c = dict(self.get_settings(snowflake))

        if key in c:
            del c[key]
            self.set_settings(snowflake, c)
