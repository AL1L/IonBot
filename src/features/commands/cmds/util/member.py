import discord

from buildabot import utils as u
from features.commands.command import Command
from features.commands.command_context import CommandContext

meta = {
    'class': 'Command',
    'description': 'Get info on a member',
    'usage': '<user>',
    'pack': 'commands.util',
    'type': 'info',
    'permissions': [],
    'no_dm': True
}


class Command(Command):
    async def on_command(self, context: CommandContext):
        if len(context.args) < 1:
            member = context.author
        else:
            member: discord.Member = await context.parse_member(context.args[0])
            if member is None:
                await context.error('Member not found')
                return

        roles = []
        user_roles = list(member.roles)
        user_roles.reverse()
        for role in user_roles:
            roles.append(role.name)
        roles.remove('@everyone')

        if len(roles) == 0:
            roles = "_None_"
        else:
            roles = ", ".join(roles)

        embed: discord.Embed = await context.send(fields={
            "Joined Guild": u.format_ms_time_simple(member.joined_at.timestamp() * 1000),
            "Joined Discord": u.format_ms_time_simple(member.created_at.timestamp() * 1000),
            "Roles": roles,
        }, inline=False, thumbnail=member.avatar_url, send=False)

        embed.set_author(name="{0.display_name} ({0.id})".format(member),
                         url=member.avatar_url,
                         icon_url=member.avatar_url)

        await context.channel.send(embed=embed)
