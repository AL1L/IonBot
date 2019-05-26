import json

from buildabot import Feature, Typer


class Ion(Feature):

    def __init__(self, fm, m):
        super().__init__(fm, m)

        self.command_manager = None

    async def on_enable(self):
        self.command_manager = self.feature_manager.get_feature("Commands")

        self.command_manager.add_command_dir('ion/cmds', ftr_dir=True)