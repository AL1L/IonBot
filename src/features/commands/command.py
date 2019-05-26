from features.commands.command_context import CommandContext
from features.commands.command_manager import CommandManager


class Command(object):

    def __init__(self, command_manager):
        self.meta = {}
        self.command_manager: CommandManager = command_manager
        self.bot = command_manager.bot
        self.storage = {}
        self.name = None

    async def on_command(self, context: CommandContext):
        pass
