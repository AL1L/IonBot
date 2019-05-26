from subprocess import check_output
from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Stop',
    'description': 'Stops the bot',
    'usage': '',
    'pack': 'commands.dev',
    'type': 'dev',
    'permissions': ['bot_admin']
}


class Stop(Command):

    async def on_command(self, context: CommandContext):
        await context.ok('Stopping bot')
        await self.bot.feature_manager.disable_all_features()
        await self.bot.client.logout()
        await self.bot.client.close()
        try:
            check_output(['pm2', 'stop', '1'])
            return
        except:
            pass
