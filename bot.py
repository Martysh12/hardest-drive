import nextcord
from nextcord.ext import commands

from dotenv import load_dotenv

import os

from constants import *

load_dotenv()

print(f"HardestDrive v1.0 by Martysh12#1610")

bot = commands.Bot(command_prefix=PREFIX, activity=nextcord.Game(PREFIX + "help"))
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user} (ID: {bot.user.id})")

# COMMANDS #

@bot.command()
async def help(ctx):
    """Show help"""
    await ctx.send(HELP)

bot.run(os.getenv("TOKEN"))

############
