import time

from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Ping',
    'description': "Check the response time of a command from message send to sending a reply",
    'usage': '',
    'pack': 'commands.dev',
    'type': "dev",
    'permissions': []
}


class Ping(Command):

    async def on_command(self, context: CommandContext):
        time_took = time.time() * 1000 - context.start_time
        await context.ok("Pong! ({:.2f} ms)".format(time_took))
