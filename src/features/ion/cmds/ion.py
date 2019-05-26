import discord

from features.commands.command import Command
from features.commands.command_context import CommandContext
from os import path, mkdir
from subprocess import STDOUT, check_output
import traceback

meta = {
    'class': 'Ion',
    'description': "Run Ion code",
    'usage': '<code>',
    'pack': 'ion',
    'type': "util",
    'permissions': ['bot_dev']
}

package_xml = """<Package>
    <Identifier>{user.id}</Identifier>
    <Name>{user.name}</Name>
    <Description>Run Ion code in Discord</Description>
    <Version>1.0.0</Version>
    <Build>0</Build>
    <Author>{user.name}</Author>
    <Options>
        <SourceRoot>src</SourceRoot>
    </Options>
</Package>"""


class Ion(Command):

    async def on_command(self, context: CommandContext):
        exe = False
        code: str = context.arg_string
        if code.startswith('exe'):
            exe = True
            code = code[4:]

        code = code.strip().strip('`')

        if code.startswith('ion'):
            code = code[3:]
        if code.startswith('csharp'):
            code = code[6:]

        msg = None

        user_workspace = 'ion/{}'.format(context.author.id)
        user_main = 'ion/{}/src/main.ion'.format(context.author.id)

        if not path.isdir(user_workspace):
            msg = await context.ok('Creating user workspace...')
            mkdir(user_workspace)
            mkdir('{}/src'.format(user_workspace))
            package = open('{}/Package.xml'.format(user_workspace), 'wt')
            package.write(package_xml.format(user=context.author))
            package.close()

        if msg is None:
            msg = await context.ok('Saving to file...')
        else:
            await context.ok('Saving to file...', edit=msg)
            
        main = open(user_main, 'wt')
        main.write(code)
        main.close()

        await context.ok('Executing...', edit=msg)

        try:
            out = check_output(['ion', 'run'], shell=True, stderr=STDOUT, cwd=path.abspath(user_workspace)).decode()
        except FileNotFoundError:
            await context.error("Ion not installed")
            return
        except Exception as e:
            out = e.output.decode()

        out = out.replace(path.abspath('ion'), '')
        out = out.replace('\\', '/')
            
        embed = await context.send(description='```\n{}```'.format(out[0:1950]), title="Output", send=False)
            
        if exe:
            await msg.delete()
            await context.channel.send(embed=embed, file=discord.File("{}/ion.bin/{}.exe".format(user_workspace, context.author.id)))
        else:
            await msg.edit(embed=embed)

