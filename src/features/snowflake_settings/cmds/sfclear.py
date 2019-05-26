import sys

from buildabot import utils

from features.commands.command import Command
from features.commands.command_context import CommandContext
from features.snowflake_settings.settings import SnowflakeSettings

meta = {
    'class': 'SFClear',
    'description': "Clear the snowflake setting cache",
    'usage': '',
    'pack': 'snowflake',
    'type': "config",
    'permissions': ['bot_admin']
}


class SFClear(Command):

    async def on_command(self, context: CommandContext):
        settings: SnowflakeSettings = self.command_manager.feature_manager.get_feature('SnowflakeSettings')

        size = sys.getsizeof(settings.settings)

        settings.settings = {}

        await context.ok('Cleared SnowflakeSettings cache of {}'.format(utils.sizeof_fmt(size)))
