from features.commands.command import Command
import discord
from features.commands.command_context import CommandContext

meta = {
    'class': 'Eval',
    'description': 'Run a command',
    'usage': '<cmd>',
    'pack': 'commands.dev',
    'type': 'dev',
    'permissions': ['bot_admin']
}


class Eval(Command):

    async def on_command(self, context: CommandContext):
        cmd = context.message.content[5:]
        cmd = cmd.strip()
        try:
            out = eval(cmd)
            await context.ok('`{}`:\n```{}```'.format(cmd, out))
        except Exception as e:
            await context.error(e)
