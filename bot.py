import nextcord
from nextcord.ext import commands

from dotenv import load_dotenv

import binascii
import os

from constants import *

load_dotenv()

# FUNCTIONS #

def make_hexdump(data, bytes_per_line=16, offset=0x0000): 
    # Chunk generator
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    text = ""
    text += " " * 7 + " ".join([f"{i:02X}" for i in range(bytes_per_line)]) + "\n"
    
    counter = offset
    for i in chunks(data, bytes_per_line):
        text += f"{counter:04X} : "                                                              \
            + binascii.hexlify(i, " ").decode("UTF-8").ljust(bytes_per_line * 3)                 \
            + "".join([chr(j) if chr(j).isascii() and chr(j).isprintable() else "." for j in i]) \
            + "\n"

        counter += bytes_per_line

    return text

#############

print(f"HardestDrive v1.0 by Martysh12#1610")

bot = commands.Bot(command_prefix=PREFIX, activity=nextcord.Game(PREFIX + "help"))
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user} (ID: {bot.user.id})")

# Checking for errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send(ERRORS["guildonly"])
    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(ERRORS["invalidcmd"])
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(ERRORS["args"])
    else:
        raise error

# COMMANDS #

@bot.command()
@commands.guild_only()
async def help(ctx):
    """Show help"""
    await ctx.send(HELP)

@bot.command()
@commands.guild_only()
async def read(ctx, bpr: int=16):
    """Read file"""
    if bpr < 4:
        await ctx.send(ERRORS["bprtoolow"])
    with open("drive", "rb") as f:
        await ctx.send("```" + make_hexdump(f.read(), bytes_per_line=bpr) + "```")

bot.run(os.getenv("TOKEN"))

############
