from buildabot import Feature
from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Features',
    'description': 'List all modules',
    'usage': '',
    'pack': 'commands.dev',
    'type': 'dev',
    'permissions': ['bot_admin']
}


class Features(Command):

    async def on_command(self, context: CommandContext):
        enabled: list[Feature] = []
        disabled: list[Feature] = []

        for fn in self.command_manager.feature_manager.features:
            f = self.command_manager.feature_manager.features[fn]
            if f.is_enabled():
                enabled.append(f)
            else:
                disabled.append(f)

        enabled_txt = ''
        for f in enabled:
            enabled_txt += '- {}\n'.format(f.meta['name'])
        if len(enabled_txt) == 0:
            enabled_txt = '*None*'

        disabled_txt = ''
        for f in disabled:
            disabled_txt += '- {}\n'.format(f.meta['name'])
        if len(disabled_txt) == 0:
            disabled_txt = '*None*'

        feilds = {'Enabled: {}'.format(len(enabled)): enabled_txt,
                  'Disabled: {}'.format(len(disabled)): disabled_txt}

        await context.send(
            description='There are {} loaded modules'.format(len(enabled) + len(disabled)),
            fields=feilds)
