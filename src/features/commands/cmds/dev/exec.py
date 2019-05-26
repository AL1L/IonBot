import traceback
from features.commands.command import Command
from features.commands.command_context import CommandContext
import discord

meta = {
    'class': 'Exec',
    'description': 'Run a command',
    'usage': '<cmd>',
    'pack': 'commands.dev',
    'type': 'dev',
    'permissions': ['bot_admin']
}


class Exec(Command):

    async def on_command(self, context: CommandContext):
        cmd: str = context.message.content[5:]
        cmd = cmd.strip().strip('`')
        if cmd.startswith('py'):
            cmd = cmd[2:]
        if cmd.startswith('thon'):
            cmd = cmd[4:]
        try:
            l = {
                'self': self,
                'context': context,
                'bot': self.bot,
                'out': None,
                'discord': discord,
                'loop': context.command_manager.feature_manager.loop,
                'get_feature': context.command_manager.feature_manager.get_feature,
                'client': context.command_manager.feature_manager.get_feature
            }
            exec(cmd, l, l)
            await context.ok('`{}`:\n```{}```'.format(cmd, l['out']))
        except Exception as e:
            await context.error('```{}```'.format(traceback.format_exc()))
