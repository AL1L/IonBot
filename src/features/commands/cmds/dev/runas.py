from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'RunAs',
    'description': "Run a command as another user",
    'usage': '<user> <command> [args...]',
    'pack': 'commands.dev',
    'type': "dev",
    'permissions': ['bot_admin'],
    'no_dm': True
}


class RunAs(Command):

    async def on_command(self, context: CommandContext):
        if len(context.args) < 2:
            raise CommandContext.MissingArgsException(context)
        user = await context.parse_member(context.args[0])
        command = self.command_manager.prefix + ' '.join(context.args[1:])

        if user is None:
            await context.error('RunAs: User not found')
            return

        msg = context.message
        msg.author = user
        msg.content = command

        await self.command_manager.run_command(msg)
