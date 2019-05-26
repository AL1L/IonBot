import importlib
import os
import time
import traceback

import discord
from buildabot import Feature, FeatureManager
from buildabot import Typer
from buildabot import utils as u

from features.commands.command_context import CommandContext
from features.embed_ui import EmbedUI


class CommandManager(Feature):

    def __init__(self, fm, m):
        super().__init__(fm, m)
        self.prefix = '.'
        self.storage = {}
        self.ignore = []
        self.embed_ui: EmbedUI = None
        self.directories = [
            os.path.join(self.feature_manager.features_dir, 'commands/cmds/')
        ]
        self.aliases = {
            # Dev
            "sudo": "runas",

            # Util
            "ui": "userinfo",
            "uc": "usercount",
            "usercounts": "usercount"
        }
        self.types = [
            ['none', ""],
            ['tickets', "Tickets"],
            ['general', "General"],
            ['info', "Info"],
            ['discord', "Discord"],
            ['eco', "Economy"],
            ['mod', "Moderation"],
            ['admin', "Admin"],
            ["util", "Utilities"],
            ['config', "Config"],
            ['dev', "Developer"]
        ]
        self.snowflake_settings = None
        try:
            from features.snowflake_settings.settings import SnowflakeSettings
            self.snowflake_settings: SnowflakeSettings = None
        except ImportError:
            pass

        if 'commands' not in self.config:
            self.config['commands'] = {}
        if 'default' not in self.config['commands']:
            self.config['commands']['default'] = {}

    def add_type(self, key: str, name: str, after: str = None):
        i = len(self.types)
        if after:
            after = after.lower()
            for j in range(len(self.types)):
                t = self.types[j]
                if after == t[0]:
                    i = j
                    break
        self.types.insert(i, [key.lower(), name])

    def add_alias(self, alias, of):
        self.aliases[alias] = of

    def remove_alias(self, alias):
        if alias in self.aliases:
            del self.aliases[alias]

    def add_command_dir(self, directory, ftr_dir=False):
        if ftr_dir:
            directory = os.path.join(
                self.feature_manager.features_dir, directory)
        self.directories.append(directory)

    def remove_command_dir(self, directory):
        self.directories.remove(directory)

    def get_feature(self, name):
        return self.feature_manager.get_feature(name)

    def set_ignore(self, id, ignore):
        if id in self.ignore and not ignore:
            self.ignore.remove(id)
        elif ignore and id not in self.ignore:
            self.ignore.append(id)

    def on_load(self):
        if 'prefix' in self.config:
            self.prefix = self.config['prefix']

    async def on_enable(self):
        self.embed_ui = self.feature_manager.get_feature("EmbedUI")
        self.on_event("on_message", self.on_message, priority=100)

        if self.feature_manager.is_enabled("SnowflakeSettings"):
            from features.snowflake_settings.settings import SnowflakeSettings
            self.snowflake_settings: SnowflakeSettings = self.feature_manager.get_feature(
                "SnowflakeSettings")
            self.snowflake_settings.register_config_value('guild', 'commands:prefix', 'str',
                                                          'Prefix to be used for commands',
                                                          default=self.prefix)
            self.add_command_dir('snowflake_settings/cmds', ftr_dir=True)

    @staticmethod
    def get_commands_in_dir(dir):
        if not os.path.isdir(dir):
            return {}
        package = dir.replace('\\', '/').split('/')
        remove = 0
        for n in package:
            if n == 'features':
                break
            remove += 1
        package = '.'.join(package[remove:])
        files = {}
        for name in os.listdir(dir):
            if name == "__init__" or name == "__pycache__":
                continue

            path = os.path.join(dir, name)
            if os.path.isfile(path):
                if not name.endswith('.py'):
                    continue
                files[name[:-3]] = package
            elif os.path.isdir(path):
                x = CommandManager.get_commands_in_dir(path)
                files = {**files, **x}

        return files

    def get_commands(self):
        files = {}
        for d in self.directories:
            x = CommandManager.get_commands_in_dir(d)
            files = {**files, **x}
        return files

    def get_command(self, name, is_dm=False):
        name = str(name).lower()

        if name in self.aliases:
            return self.get_command(self.aliases[name])

        commands = self.get_commands()

        if name not in commands:
            return

        module = getattr(__import__(commands[name], fromlist=[name]), name)
        importlib.reload(module)
        if hasattr(module, 'meta'):
            try:
                command = getattr(module, module.meta['class'])(self)
                command.meta = module.meta

                Typer.verify_dict({
                    'class*': 'str',
                    'description*': 'str',
                    'usage*': 'str',
                    'pack*': 'str',
                    'type': 'str',
                    'permissions': 'str[]',
                    'no_dm': 'bool',
                    'special': 'bool'
                }, command.meta)
            except AttributeError or TypeError as e:
                self.logger.error('Invalid class meta in command', name)
                self.logger.error(traceback.format_exc())
                return
            except:
                self.logger.error('Failed to load command', name)
                self.logger.error(traceback.format_exc())
                return
            key = command.meta['class']
            if key not in self.storage:
                self.storage[key] = {}
            command.storage = self.storage[key]
            command.name = name
            return command
        else:
            command = module.Command()
            return command

    def has_permission(self, cmd, msg, is_dm=False):
        if cmd == "__pycache__":
            return [False, 'INVALID_COMMAND']
        if cmd == "__init__":
            return [False, 'INVALID_COMMAND']
        if isinstance(cmd, str):
            command = self.get_command(cmd)
        else:
            command = cmd

        if 'permissions' not in command.meta and not hasattr(command, 'permissions'):
            return [True]

        if msg.author.id in self.bot.config['admins']:
            return [True]

        req_perms = None

        if 'permissions' in command.meta:
            req_perms = command.meta['permissions']
        elif hasattr(command, 'permissions'):
            req_perms = command.permissions

        if req_perms is not None:
            user_perms = msg.channel.permissions_for(msg.author)
            voice_perms = discord.Permissions.voice()
            parent_perms = None
            if not is_dm:
                parent_perms = msg.author.guild_permissions
                if msg.channel.category is not None:
                    parent_perms = msg.channel.category.permissions_for(
                        msg.author)
            for req_perm in req_perms:
                if req_perm.startswith('user:'):
                    if str(msg.author.id) not in req_perm.split(':')[1].split(','):
                        return [False, 'INVALID_USER']
                elif req_perm.startswith('guild:'):
                    if str(msg.server.id) not in req_perm.split(':')[1].split(','):
                        return [False, 'INVALID_GUILD']
                elif req_perm.startswith('channel:'):
                    if str(msg.channel.id) not in req_perm.split(':')[1].split(','):
                        return [False, 'INVALID_CHANNEL']
                elif req_perm.lower() == 'bot_admin':
                    return [False, 'BOT_ADMIN']
                elif req_perm.lower() == 'team_member':
                    main_guild = self.bot.client.get_guild(514928702199431177)
                    has_team = False
                    main_member = main_guild.get_member(msg.author.id)

                    if main_member is not None:
                        for role in main_member.roles:
                            if role.name == 'Team':
                                has_team = True

                    if not has_team:
                        return [False, 'TEAM_MEMBER']
                else:
                    if getattr(voice_perms, req_perm) and not is_dm:
                        if not getattr(parent_perms, req_perm):
                            return [False, req_perm.upper()]
                    elif not getattr(user_perms, req_perm):
                        return [False, req_perm.upper()]
        return [True]

    def command_visible(self, command, context):
        guild_perms = self.config['commands']['default']
        if context.guild is not None:
            if str(context.guild.id) in self.config['commands']:
                guild_perms = {**guild_perms, **
                               self.config['commands'][str(context.guild.id)]}
            if self.snowflake_settings is not None:
                guild_perms = {**guild_perms,
                               **self.snowflake_settings.get_setting(context.guild.id, 'commands:commands', default={})}

        allow = True
        for k in guild_perms:
            if k.startswith(':'):
                t: str = k[1:].lower().strip('.*')
                if command.meta['pack'].lower().startswith(t):
                    allow = guild_perms[k]

        for k in guild_perms:
            if command.name.lower() == k.lower():
                allow = guild_perms[k]
        return allow

    async def on_message(self, message: discord.Message):
        return await self.run_command(message)

    async def run_command(self, message: discord.Message):
        start_ms_time = int(round(time.time() * 1000))

        if message.content == self.prefix + "fix":
            self.set_ignore(message.author.id, False)
        elif message.author.id in self.ignore:
            return

        prefix = self.prefix
        if self.snowflake_settings is not None:
            if message.guild is not None:
                prefix = self.snowflake_settings.get_setting(
                    message.guild.id, 'commands:prefix', default=prefix)

        if not message.content.startswith(prefix):
            return

        is_dm = isinstance(message.channel, discord.DMChannel)

        context = CommandContext(self, message, start_ms_time)

        from features.commands.command import Command
        command: Command = self.get_command(context.label, is_dm=is_dm)

        if command is None:
            return

        if not self.command_visible(command, context):
            return

        failed = False
        error = "None"
        has_perm = self.has_permission(command, message, is_dm=is_dm)

        if not has_perm[0]:
            # await context.error('You are lacking permission `{}`'.format(has_perm[1]))
            await context.error("You don't have permission to run that command", delete_after=15)
            return

        if 'no_dm' in command.meta and is_dm:
            await context.error("Soory, that command can't be run in DMs. Try again in a server channel")
            return

        try:
            await command.on_command(context)
        except CommandContext.ArgsException as e:
            await context.error(e.message)
        except:
            failed = True
            error = traceback.format_exc()
            if not is_dm and context.channel.name == "testing":
                await context.send(description='```{}```\n(Full error was shown because of channel name)'.format(error),
                                   image='https://i.imgur.com/uXt0Xbs.gif', color=discord.Colour.red())
            else:
                await context.send(title='There was an error while executing that command!',
                                   description='Staff has been notified and will fix\n'
                                               'this bug as soon as possible.\n\n'
                                               'Thank you for your patience! 😬', color=discord.Color.red())

        # Log the command
        log = 'CMD "{}#{}" ({}) ran "{}"'.format(context.author.name, context.author.discriminator,
                                                 context.author.id, context.label)
        self.logger.info(log)
        if failed:
            self.logger.error(error)
        time_took = int(round(time.time() * 1000)) - context.start_time

        log_msg = ''
        log = True
        log_channel = None
        if self.feature_manager.is_enabled("Config"):
            log_channel = self.feature_manager.get_feature(
                "Config").get('debug_channel', context=context)

        if log and log_channel is not None:
            try:
                embed = discord.Embed()
                embed.colour = discord.Colour.green()
                perms = str(has_perm[0])
                if not has_perm[0]:
                    perms = perms + ' ({})'.format(has_perm[1])
                    embed.colour = discord.Colour.orange()

                embed.description = '**Command:**\n{cmd_name}\n\n' + \
                                    '**Args:**\n{cmd_args}\n\n' + \
                                    '**Has Permission:**\n{has_perms}\n\n' + \
                                    '**Author:**\n{author}\n\n' + \
                                    '**Raw:**\n```{raw}```\n\n' + \
                                    '**Start Time:**\n{start}\n\n' + \
                                    '**End Time:**\n{end}'
                if failed:
                    embed.colour = discord.Colour.red()
                    log_msg = '<@&465103804271165454>'
                    embed.description = embed.description + \
                        '\n\n**Error:**\n```{error}```'
                embed.description = embed.description.format(cmd_name=context.name, cmd_args=context.args,
                                                             author='`{author_name}#{author_discriminator}` _({author_id})_'.format(
                                                                 author_name=context.author.name,
                                                                 author_discriminator=context.author.discriminator,
                                                                 author_id=context.author.id),
                                                             raw=message.content,
                                                             start=u.format_ms_time(
                                                                 start_ms_time),
                                                             end=u.format_ms_time(
                                                                 start_ms_time + time_took),
                                                             has_perms=perms, error=error[:650])
                embed.title = 'Command Ran'
                embed.set_footer(text="\U000023F3 Took {}ms".format(time_took))
                await log_channel.send(log_msg, embed=embed)
            except ValueError:
                pass
