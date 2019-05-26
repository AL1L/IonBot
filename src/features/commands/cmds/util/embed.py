import string

import discord
import json
from features.commands.command import Command
from features.commands.command_context import CommandContext

def color_converter(color):
    if type(color) is int:
        if color < 0 or color > 0xffffff:
            raise ValueError('Color value is outside of valid range')
        return color
    color = color.strip('#')
    if color.startswith('0x'):
        color = color[2:]
    if len(color) != 6 or set(color) - set(string.hexdigits):
        raise ValueError('Invalid color hex value')
    return int(color, 16)

meta = {
    'class': 'Embed',
    'description': 'Create an embed\nIf footer is none, the default will be used\n\nMay also use this [embed builder](https://embedbuilder.nadekobot.me/) as the arguments.',
    'usage': '[title];[color];[footer text];[footer icon];[author text];[author icon];[image url];[thumbnail url];[body text]',
    'pack': 'commands.util',
    'type': 'util',
    'permissions': ['manage_messages']
}


class Embed(Command):

    async def on_command(self, context: CommandContext):
        if len(context.args) < 1:
            raise CommandContext.MissingArgsException(context)
        embed = discord.Embed()
        content = ''

        if context.arg_string.startswith("{"):
            data = json.loads(context.arg_string)

            def p(name, part):
                if name in data:
                    if part in data[name]:
                        return data[name][part]
                return discord.Embed.Empty

            if 'plainText' in data:
                content = data['plainText']

            if 'title' in data:
                embed.title = data['title']

            if 'description' in data:
                embed.description = data['description']

            if 'color' in data:
                embed.colour = data['color']

            if 'thumbnail' in data:
                embed.set_thumbnail(url=data['thumbnail'])

            if 'image' in data:
                embed.set_image(url=data['image'])

            if 'author' in data:
                embed.set_author(name=p('author', 'name'), url=p('author', 'url'), icon_url=p('author', 'icon_url'))

            if 'footer' in data:
                embed.set_footer(text=p('footer', 'text'), icon_url=p('footer', 'icon_url'))

            if 'fields' in data:
                for f in data['fields']:
                    embed.add_field(name=f['name'], value=f['value'], inline=f['inline'])
        else:
            parts = context.message.arg_string.strip().split(';')

            if parts[0].strip() != "":
                embed.title = parts[0]

            if parts[1].strip() != "":
                try:
                    embed.colour = color_converter(parts[1])
                except ValueError as e:
                    s = ValueError()
                    await context.error(str(e))

            if parts[2].strip() != "":
                if parts[3].strip() != "":
                    embed.set_footer(text=parts[2], icon_url=parts[3])
                else:
                    embed.set_footer(text=parts[2])

            if parts[4].strip() != "":
                if parts[5].strip() != "":
                    embed.set_author(name=parts[4], icon_url=parts[5])
                else:
                    embed.set_author(name=parts[4])
            elif parts[5].strip() != "":
                embed.set_author(icon_url=parts[5])

            if parts[6].strip() != "":
                embed.set_image(url=parts[6])

            if parts[7].strip() != "":
                embed.set_thumbnail(url=parts[7])

            if parts[8].strip() != "":
                embed.description = parts[8]

        await context.channel.send(embed=embed)
