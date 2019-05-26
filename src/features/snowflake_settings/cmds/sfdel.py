import re

from features.commands.command import Command
from features.commands.command_context import CommandContext
from features.snowflake_settings.settings import SnowflakeSettings

meta = {
    'class': 'SFDel',
    'description': "Delete a snowflake setting",
    'usage': '',
    'pack': 'snowflake',
    'type': "config",
    'permissions': ['bot_admin']
}


class SFDel(Command):

    async def on_command(self, context: CommandContext):
        if len(context.args) < 2:
            raise CommandContext.MissingArgsException(context)

        settings: SnowflakeSettings = self.command_manager.feature_manager.get_feature('SnowflakeSettings')
        context.args[0] = context.args[0].lower()
        if context.args[0] == 'guild':
            context.args[0] = context.guild.id
        elif context.args[0] == 'channel':
            context.args[0] = context.channel.id
        elif context.args[0] == '@me' or context.args[0] == 'me':
            context.args[0] = context.author.id
        else:
            context.args[0] = re.sub("[^0-9]", '', context.args[0])

        snowflake = context.args[0]
        key = context.args[1]

        try:
            settings.del_setting(int(snowflake), key)
        except ValueError:
            await context.error('Invalid snowflake')
            return

        await context.ok('**{}** for __{}__ was deleted'.format(key, snowflake))
