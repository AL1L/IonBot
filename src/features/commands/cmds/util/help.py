import discord
from buildabot import utils as u
import time

from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Help',
    'description': 'Shows list of commands the bot can do',
    'usage': '[command]',
    'pack': 'commands.util',
    'type': 'info',
    'permissions': []
}


class Help(Command):

    async def on_command(self, context: CommandContext):
        times = [0, 0]

        def start():
            times[0] = time.time()

        def end():
            times[1] = time.time()
        sections = {}
        for type in self.command_manager.types:
            sections[type[0]] = type[1]
        is_dm = isinstance(context.channel, discord.DMChannel)
        prefix = context.prefix

        show_all = False

        if len(context.args) > 0 and context.args[0] != "here":
            if context.args[0] == 'all' and context.author.id in self.bot.config['admins']:
                show_all = True
                context.args.pop(0)

        if len(context.args) > 0 and context.args[0] != "here":
            cmd_name = ' '.join(context.args[0:]).strip()
            command: Command = self.command_manager.get_command(cmd_name)
            if command is None or not self.command_manager.command_visible(command, context):
                await context.error("Command `{}` not found".format(cmd_name))
                return

            has_perm = self.command_manager.has_permission(
                cmd_name, context.message, is_dm=is_dm)

            color = discord.Colour.green()
            lang = u.lang_obj(context.message.author)
            perms_emoji = '✅'
            if not has_perm[0]:
                color = discord.Colour.orange()
                perms_emoji = "🚫"

            title = 'Command: {cmd_name}'.format(cmd_name=cmd_name)

            description = '**Usage:**\n' + prefix + cmd_name + ' '

            if 'usage' in command.meta:
                description += command.meta['usage']

            cmd_desc = command.meta['description']

            cmd_usage = "{cmd_prefix}{cmd_name} {usage}".format(cmd_prefix=prefix,
                                                                cmd_name=cmd_name, usage=command.meta['usage'])
            cmd_description = ''
            description = '**Usage:**\n{cmd_usage}\n\n' + \
                          '**Description:**\n{cmd_description}\n\n' + \
                          '**Type:** {cmd_type}\n\n' + \
                          '**Permission to Use:** {have_perms}\n\n'
            description = description.format(cmd_usage=cmd_usage,
                                             cmd_description=cmd_desc,
                                             cmd_type=sections[command.meta['type']],
                                             have_perms=str(perms_emoji))

            await context.send(description=description, title=title, color=color)
        else:
            cmds = {}
            all_cmds = self.command_manager.get_commands()

            amt = 0
            for cmd_name in all_cmds:
                try:
                    command: Command = self.command_manager.get_command(
                        cmd_name)

                    if not show_all:
                        start()
                        if not self.command_manager.has_permission(cmd_name, context.message, is_dm=is_dm)[0]:
                            continue
                        end()

                        if not self.command_manager.command_visible(command, context):
                            continue

                        if command.meta['type'] == 'hidden':
                            continue

                    usage = "{cmd_prefix}{cmd_name} {usage}".format(
                        cmd_prefix=prefix, cmd_name=cmd_name, usage=command.meta['usage'])
                    amt += 1
                    if command.meta['type'] not in cmds:
                        cmds[command.meta['type']] = {}

                    cmds[command.meta['type']][usage] = command.meta['description']
                except Exception:
                    pass

            help_list = ""

            for sec in sections:
                if sec in cmds:
                    if len(sections[sec]) != 0:
                        help_list = "{}\n\n**{}**".format(
                            help_list, sections[sec])

                    for usage in cmds[sec]:
                        help_list = "{}\n`{}`".format(
                            help_list, usage, cmds[sec][usage])
            if help_list == "":
                help_list = "_You have no access to any commands_"
            in_dm = amt > 15
            if len(context.args) > 0 and context.args[0] == "here":
                in_dm = False

            if in_dm:
                await context.ok('<@{}> the command list was sent to you.'
                                 .format(context.message.author.id), delete_after=120)
                await context.send(description=help_list, title='Command List', inline=False, dm=True)
            else:
                await context.channel.send(
                    embed=await context.send(description=help_list, title='Command List', send=False), delete_after=120)


def within(x, num, rang):
    return num - rang <= x <= num + rang
