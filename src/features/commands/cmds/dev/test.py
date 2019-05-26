import discord

from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Test',
    'description': "A test command for the bot developer",
    'usage': '',
    'pack': 'commands.dev',
    'type': "dev",
    'permissions': ['bot_dev']
}


class Test(Command):

    async def on_command(self, context: CommandContext):
        await context.ok("Yay!")
