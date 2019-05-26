import re
import string
import time
from typing import List

import discord
from buildabot import Feature, Typer

meta = {
    'class': 'EmbedUI',
    'name': 'EmbedUI',
    'description': 'Standardize the way your bot looks',
    'softdepends': ['SnowflakeSettings']
}


class EmbedUI(Feature):

    def __init__(self, fm, m):
        super().__init__(fm, m)
        self.defaults = {}
        self.empty = discord.embeds.EmptyEmbed

    def _convert_color(self, color):
        if color == self.empty:
            return self.empty
        if type(color) is int:
            if color < 0 or color > 0xffffff:
                return self.empty
            return color
        color = color.strip('#')
        if color.startswith('0x'):
            color = color[2:]
        if len(color) != 6 or set(color) - set(string.hexdigits):
            return self.empty
        return int(color, 16)

    def _get_user(self, user):
        if user == self.empty:
            return user
        if user is None:
            return None

        if hasattr(user, 'id'):
            return user

        if not isinstance(user, int):
            return None
        return self.feature_manager.bot.client.get_user(user)

    def _get_default(self, key):
        if key is None:
            return self.empty
        value = None
        if key in self.config:
            value = self.config[key]
        if value is None:
            return self.empty
        return value

    def _sanitize_str(self, o, def_key=None):
        if o is None:
            return self._get_default(def_key)
        if o == self.empty:
            return o
        s = str(o).strip()
        if s == '':
            return self._get_default(def_key)
        return s

    def add_description(self, embed: discord.Embed, description=None, format=None):
        description = self._sanitize_str(description, def_key='description')
        if format is not None:
            description = description.format(**format)
        embed.description = description
        return embed

    def add_color(self, embed: discord.Embed, color=None):
        if not isinstance(color, int):
            color = self._sanitize_str(color, def_key='color')

        embed.colour = self._convert_color(color)

        return embed

    def add_footer(self, embed: discord.Embed, name=None, icon=None, start_time: int = None, suffix=None, author=None, format=None):
        name = self._sanitize_str(name, def_key='footer_name')
        icon = self._sanitize_str(icon, def_key='footer_icon')
        suffix = self._sanitize_str(suffix, def_key='footer_suffix')
        author = self._get_user(author)
        time_took = 0
        if start_time is not None:
            time_took = int(round(time.time() * 1000)) - int(start_time)

        set_name = ''
        if name != self.empty:
            set_name += name
        if suffix != self.empty:
            if set_name != '':
                set_name += ' » '
            set_name += suffix
        if author is not None and author != self.empty:
            dm = False
            if self.feature_manager.is_enabled("SnowflakeSettings"):
                dm = self.feature_manager.get_feature('SnowflakeSettings').get_setting(author, 'debug_mode',
                                                                                       default=False)
            if dm:
                if start_time is not None:
                    if set_name != '':
                        set_name += ' | '
                    set_name += '{}ms'.format(time_took)

        if set_name != '':
            if format is not None:
                set_name = set_name.format(**format)
            embed.set_footer(text=set_name, icon_url=icon)
        elif icon != self.empty:
            embed.set_footer(icon_url=icon)

        return embed

    def add_fields(self, embed: discord.Embed, fields: dict = None, inline=True, format=None):
        if fields is None:
            fields = self._get_default('fields')
        if isinstance(fields, dict):
            for k, v in fields.items():
                if v is not None:
                    if isinstance(v, tuple) or isinstance(v, list):
                        val = v[0]
                        if format is not None:
                            val = val.format(**format)
                        embed.add_field(name=str(k), value=val, inline=v[1])
                    else:
                        v = str(v)
                        if format is not None:
                            v = v.format(**format)
                        embed.add_field(
                            name=str(k), value=v, inline=inline)

        return embed

    def add_author(self, embed: discord.Embed, title=None, icon=None, link=None, author=None, format=None):
        title = self._sanitize_str(title, def_key='author_title')
        icon = self._sanitize_str(icon, def_key='author_title')
        link = self._sanitize_str(link, def_key='author_title')
        author = self._get_user(author)

        if author == self.empty:
            return embed
        if author is not None:
            embed.set_author(name=author.display_name,
                             icon_url=author.avatar_url)
        else:
            if title != self.empty:
                if format is not None:
                    title = title.format(**format)
                embed.set_author(name=title, icon_url=icon, url=link)

        return embed

    def add_title(self, embed: discord.Embed, title=None, format={}):
        title = self._sanitize_str(title, def_key='title')
        if title == self.empty:
            return embed
        if format is not None:
            title = title.format(**format)
        embed.title = title
        return embed

    def add_image(self, embed: discord.Embed, image=None):
        image = self._sanitize_str(image, def_key='image')
        if image != self.empty:
            embed.set_image(url=image)
        return embed

    def add_thumbnail(self, embed: discord.Embed, image=None):
        image = self._sanitize_str(image, def_key='thumbnail')
        if image != self.empty:
            embed.set_thumbnail(url=image)
        return embed

    def generate_embed(self, description=None, fields: dict = None, inline=True, footer=None, title=None,
                       color: discord.Colour = None, image=None, thumbnail=None, author=None,
                       start_time: int = None, author_text=None, author_icon=None, format=None) -> discord.Embed:
        """
        Create an embed, values left None will use the default specified in the feature config

        :param description: Content of embed
        :param fields: Dictionary of fields
        :param inline: If fields should be inline or not
        :param footer: Footer text
        :param title: Embed title
        :param color: Embed color
        :param image: Image it be placed in the embed
        :param thumbnail: Image it be placed as the thumbnail
        :param author: discord.User or discord.Member as in author
        :param start_time: Start time of the task, used if the author is set and has debug_mode set to true
        :param author_text: Text to use as the author section
        :param author_icon: Icon of the author
        :return: discord.Embed
        """
        embed = discord.Embed()

        self.add_author(embed, author=author,
                        title=author_text, icon=author_icon, format=format)
        self.add_color(embed, color=color)
        self.add_description(embed, description=description, format=format)
        self.add_fields(embed, fields=fields, inline=inline, format=format)
        self.add_footer(embed, suffix=footer,
                        start_time=start_time, author=author, format=format)
        self.add_image(embed, image=image)
        self.add_thumbnail(embed, image=thumbnail)
        self.add_title(embed, title=title, format=format)

        return embed

    async def ask(self, embed, choices: List, channel: discord.abc.Messageable, user=None, timeout=None, bot=False,
                  clear=True, msg: discord.Message = None):
        if user is not None:
            user = self._get_user(user)

        if msg is None:
            msg = await channel.send(embed=embed)
        else:
            if embed is not None:
                await msg.edit(embed=embed)

        for i in range(len(choices)):
            choices[i] = str(choices[i])
            if len(choices[i]) > 4:
                choices[i] = self.bot.client.get_emoji(
                    int(re.sub('[^0-9]', '', choices[i])))

        for c in choices:
            await msg.add_reaction(c)

        def check(reaction: discord.Reaction, usr):
            if usr is not None:
                if usr.id == self.bot.client.user.id:
                    return
            if not bot and usr.bot:
                return False
            if user is not None:
                if usr is None:
                    return False
                if usr.id != user.id:
                    return False

            if reaction.message.id != msg.id:
                return False

            if isinstance(reaction.emoji, discord.Emoji):
                is_in = False
                for c in choices:
                    if isinstance(c, discord.Emoji):
                        if c.id == reaction.emoji.id:
                            is_in = True
                if not is_in:
                    return False
            elif reaction.emoji not in choices:
                return False

            return True

        reaction, user = await self.bot.client.wait_for('reaction_add', check=check, timeout=timeout)

        if clear:
            if isinstance(msg.channel, discord.DMChannel):
                await msg.delete()
                msg = await channel.send(embed=embed)
            else:
                await msg.clear_reactions()

        index = 0
        for c in choices:
            if isinstance(c, discord.Emoji):
                if c.id == reaction.emoji.id:
                    if user is None:
                        return msg, index, user
                    else:
                        return msg, index
            else:
                if c == reaction.emoji:
                    if user is None:
                        return msg, index, user
                    else:
                        return msg, index
            index += 1

        if user is None:
            return msg, -1, user
        else:
            return msg, -1

    async def input(self, message=None, channel=None, user=None, guild=None, timeout=None, delete=False, bot=False, full=False, context=None, ignore=True, expected_type=None, on_invalid=None):
        if expected_type:
            if not Typer.is_valid_type(expected_type):
                raise ValueError('Type "{}" not found'.format(expected_type))
        if context:
            if message is None:
                message = context.message
        if message:
            if not channel:
                channel = message.channel
            if not user:
                user = message.author
            if not guild:
                guild = message.guild

        if not ignore:
            if context is None or user is None:
                ignore = False
            else:
                context.command_manager.set_ignore(user.id, True)

        def check(message):
            if bot:
                if message.author.bot:
                    return False
            if channel:
                if message.channel.id != channel.id:
                    return False
            if user:
                if message.author.id != user.id:
                    return False
            if guild:
                if not message.guild:
                    return False
                if message.guild.id != guild.id:
                    return False

            return True

        while True:
            message = await self.bot.client.wait_for('message', check=check, timeout=timeout)

            if delete and isinstance(message.channel, discord.TextChannel):
                try:
                    await message.delete()
                except discord.DiscordException:
                    pass

            if expected_type is not None:
                try:
                    message.content = Typer.check_arg(
                        message.content, expected_type, context=context)
                except TypeError:
                    if on_invalid is not None:
                        await on_invalid()

                    continue

            if not ignore:
                context.command_manager.set_ignore(user.id, False)

            if full:
                return message
            return message.content
