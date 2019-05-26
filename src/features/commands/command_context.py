import re
import warnings

import discord
from concurrent.futures._base import TimeoutError


class CommandContext(object):

    def __init__(self, command_manager, message: discord.Message, start_time):
        from features.commands.command_manager import CommandManager

        self.command_manager: CommandManager = command_manager
        self.start_time = start_time
        self.message: discord.Message = message
        self.channel: discord.TextChannel = message.channel
        self.guild: discord.Guild = message.guild
        self.author: discord.Member = message.author
        self.config = {}

        msg_parts = []

        for part in message.content.split(' '):
            if part.strip() != '':
                msg_parts.append(part.strip())
        self.prefix = self.command_manager.prefix

        if self.command_manager.snowflake_settings is not None:
            if self.guild is not None:
                self.prefix = self.command_manager.snowflake_settings.get_setting(self.guild.id, 'commands:prefix',
                                                                                  default=self.prefix)

        self.label: str = msg_parts[0][len(self.prefix):]
        self.name = self.label
        self.arg_string: str = message.content[len(
            command_manager.prefix) + len(self.label):].strip()
        self.args = msg_parts[1:]

    @property
    def workshop(self):
        warnings.warn(DeprecationWarning())
        return self.command_manager.bot

    def parse_mention(self, mstr, t=-1):
        mstr = re.sub('[^0-9]', '', mstr)
        if len(mstr) == 0:
            return None
        try:
            mid = int(mstr)
        except ValueError:
            return None
        m = None

        if m is None and (t == 0 or t == -1):
            m = self.message.guild.get_member(mid)

        if m is None and (t == 1 or t == -1):
            m = self.message.guild.get_channel(mid)

        if m is None and (t == 2 or t == -1):
            pass
            # m = self.message.guild.roles[mid]

        return m

    async def parse_member(self, mstr):
        mstr = mstr.strip().strip('<>').strip('@').strip('!')
        try:
            member = self.message.guild.get_member(int(mstr))
            if member is None:
                member = await self.message.guild.get_ban(int(mstr))
        except ValueError:
            return None
        except AttributeError:
            return None
        except discord.DiscordException:
            return None
        return member

    async def send(self, description=None, fields: dict = None, inline: bool = True, footer=None, title=None,
                   color: discord.Colour = None, send: bool = True, image=None, thumbnail=None, author=None, content='',
                   dm=False, channel=None, show_time=None, edit=None, delete_after=None) -> discord.Message:
        embed_ui = self.command_manager.embed_ui
        if author is None:
            author = self.message.author
        if channel is None:
            channel = self.channel

        embed = embed_ui.generate_embed(description=description, fields=fields, inline=inline, footer=footer,
                                        title=title, color=color, image=image, thumbnail=thumbnail, author=author,
                                        start_time=self.start_time)

        if send:
            try:
                if edit is not None:
                    await edit.edit(content=str(content), embed=embed)
                elif dm:
                    return await author.send(str(content), embed=embed, delete_after=delete_after)
                else:
                    return await channel.send(str(content), embed=embed, delete_after=delete_after)
            except discord.Forbidden as e:
                return
        else:
            return embed

    async def ok(self, msg, fields=None, author=None, footer=None, dm=False, channel=None, send=True, delete_after=None, edit=None):
        if msg is None or str(msg).strip() == '':
            return None
        return await self.send(description=str(msg).strip(), fields=fields, author=author, footer=footer, dm=dm,
                               channel=channel, send=send, edit=edit, delete_after=delete_after)

    async def error(self, msg, fields=None, author=None, footer=None, dm=False, channel=None, send=True, delete_after=None, edit=None):
        if msg is None or str(msg).strip() == '':
            return None
        return await self.send(description=str(msg).strip(), title="Oh no!", fields=fields, author=author,
                               footer=footer, color=discord.Color.red(), dm=dm, channel=channel, send=send,
                               edit=edit, delete_after=delete_after)

    async def warn(self, msg, fields=None, author=None, footer=None, dm=False, channel=None, send=True, delete_after=None, edit=None):
        if msg is None or str(msg).strip() == '':
            return None
        return await self.send(description=str(msg).strip(), title="Hmm...", fields=fields, author=author,
                               footer=footer, color=discord.Color.dark_gold(), dm=dm, channel=channel, send=send,
                               edit=edit, delete_after=delete_after)

    async def user_flow(self, flow, context={}, on_timeout=None):
        assert self.command_manager.feature_manager.is_enabled(
            "EmbedUI"), "The EmbedUI feature is required for a userflow"

        from features.embed_ui import EmbedUI
        embedui: EmbedUI = self.command_manager.get_feature("EmbedUI")

        rtn = context

        class m:
            def __init__(self, context):
                self.msg = None
                self.context = context

            async def send(self, embed):
                if self.msg is None:
                    self.msg = await self.context.channel.send(embed=embed)
                elif not isinstance(self.context.channel, discord.TextChannel):
                    if msg is not None:
                        try:
                            await self.msg.delete()
                        except discord.DiscordException:
                            pass
                    self.msg = await self.context.channel.send(embed=embed)
                else:
                    await self.msg.edit(embed=embed)
        msg = m(self)
        key = None

        try:
            for item in flow:
                action = item['action']

                def get_val(key, d=None):
                    if key not in item:
                        return d
                    return item[key]

                key = get_val('key')
                default = get_val('default')

                embed = embedui.generate_embed(**item['embed'], format=rtn, author=self.author, start_time=self.start_time)

                if action == 'input':
                    await msg.send(embed=embed)

                    async def on_invalid():
                        if callable(get_val('on_invalid')):
                            await (item['on_invalid'](key, msg))

                    val = await embedui.input(context=self, timeout=get_val('timeout', d=60), delete=get_val(
                        'delete', d=True), expected_type=get_val('type'), on_invalid=on_invalid)

                    if key is not None:
                        rtn[key] = val

                elif action == 'reaction':
                    await msg.send(embed=embed)

                    async def on_invalid():
                        if callable(get_val('on_invalid')):
                            await (item['on_invalid'](key, msg))

                    r = get_val('reactions')

                    assert r is not None, "Must supply reactions"

                    templates = {
                        "yes_no": ['✅', '❌'],
                        "5_star": [],
                        "opinion": ['<:dnd:476320660931739658>', '<:idle:476320661044854784>', '<:online:404074194129649665>'],
                        "thumbs": ['👍', '👎']
                    }

                    reactions = r

                    if isinstance(r, str):
                        if r in templates:
                            reactions = templates[r]

                    ingore, val = await embedui.ask(None, choices=reactions, msg=msg.msg, timeout=get_val('timeout', d=60), channel=self.channel, user=self.author, clear=False)

                    if isinstance(self.channel, discord.TextChannel):
                       await msg.msg.clear_reactions()

                    if isinstance(r, str):
                        if r in templates:
                            if r == 'yes_no':
                                val = True if val == 0 else False
                            elif r == '5_star':
                                val += 1
                            elif r == 'opinion':
                                val = 'red' if val == 0 else (
                                    "yellow" if val == 1 else "green")
                            elif r == 'thumbs':
                                val = 'up' if val == 0 else 'down'

                    if key is not None:
                        rtn[key] = val
                elif action == 'message':
                    await msg.send(embed=embed)
                    if key is not None:
                        rtn[key] = default
                else:
                    raise f"Invalid action: {action}"
        except TimeoutError:
            if callable(on_timeout):
                await msg.msg.clear_reactions()
                await on_timeout(key, msg, rtn)
            return False

        return rtn

    class CommandException(Exception):

        def __init__(self, context):
            self.context: CommandContext = context
            self.args = (self.context.label,)

    class ArgsException(CommandException):
        @property
        def message(self):
            return 'Invalid usage, try running `{}help {}`'.format(self.context.prefix, self.context.label)

    class MissingArgsException(ArgsException):
        pass

    class TooManyArgsException(ArgsException):
        pass

    class InvalidArgException(ArgsException):
        pass
