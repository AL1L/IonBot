import discord

from features.commands.command import Command
from features.commands.command_context import CommandContext
from features.embed_ui import EmbedUI
from concurrent.futures._base import TimeoutError
import json

meta = {
    'class': 'FizzBuzz',
    'description': "Classic Fizz Buzz",
    'usage': '',
    'pack': 'commands.dev',
    'type': "dev",
    'permissions': ['bot_admin']
}

def fizz_buzz(n):
    d = ["fizzbuzz", "{0}", "{0}", "fizz", "{0}", "buzz", "fizz",
        "{0}", "{0}", "fizz", "buzz", "{0}", "fizz", "{0}", "{0}"]
    return d[n % 15].format(n)

class FizzBuzz(Command):

    async def on_command(self, context: CommandContext):
        try:
            n = int(context.args[0])
        except:
            await context.error("That's not a number")
            return

        await context.ok(fizz_buzz(n))
