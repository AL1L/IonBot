import importlib
import json
from buildabot import utils, Typer
from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Reload',
    'description': 'Reloads the config of the bot, will not work for changing bot token',
    'usage': '',
    'pack': 'commands.dev',
    'type': 'dev',
    'permissions': ['bot_admin']
}


class Reload(Command):

    async def on_command(self, context: CommandContext):
        do_not_use = False
        if do_not_use:
            await context.error("This command is currently broken, do not use.")
            return
        msg = await context.ok('Reloading modules...')
        # Imports
        importlib.reload(utils)

        await context.ok('Reloading config...', edit=msg)
        # Config
        config = None

        try:
            config = json.load(open('config.json'))
        except:
            await context.error('Missing or invalid config file')
            return

        #  await context.ok('Reloading features...', edit=msg)
        # await self.bot.feature_manager.reload_all_features()

        self.bot.config = config

        # await msg.edit(embed=await context.send(description='Stopping web server...', send=False))
        # await context.workshop.stop_server()
        # await msg.edit(embed=await context.send(description='Restarting web server...', send=False))
        # await context.workshop.start_server()

        await context.ok('Reload complete!', edit=msg)
        return
