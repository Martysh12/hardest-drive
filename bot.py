import nextcord
from nextcord.ext import commands, tasks

from dotenv import load_dotenv

import binascii
import datetime
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



# VARIABLES #

global_num_reads = 0
global_num_writes = 0
global_bytes_written = 0

#############

print(f"HardestDrive v1.0 by Martysh12#1610")

bot = commands.Bot(command_prefix=PREFIX, activity=nextcord.Game(PREFIX + "help"))
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user} (ID: {bot.user.id})")

@tasks.loop(minutes=5)
async def write_read_report():
    print(f"[{datetime.datetime.now().strftime('%X')}] Operations since {datetime.datetime.now() - datetime.timedelta(minutes=5)}:")
    print("\t" + "Reads: "         + str(global_num_reads))
    print("\t" + "Writes: "        + str(global_num_writes))
    print("\t" + "Bytes written: " + str(global_bytes_written))
    print()

    global global_num_reads
    global global_num_writes
    global global_bytes_written

    global_num_reads = 0
    global_num_writes = 0
    global_bytes_written = 0

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
async def read(ctx, page: int=1, bpr: int=8):
    """Read file"""
    if bpr < 4:
        await ctx.send(ERRORS["bprtoolow"])
        return

    with open("drive", "rb") as f:
        drive_content = f.read()
        drive_pages = [drive_content[i:i + BYTES_PER_PAGE] for i in range(0, len(drive_content), BYTES_PER_PAGE)]

        try:
            current_page = drive_pages[page - 1]
        except:
            await ctx.send(ERRORS["invalidpage"])
            return

        embed = nextcord.Embed(title="Hexdump", description=f"```{make_hexdump(current_page, bytes_per_line=bpr, offset=(page - 1) * BYTES_PER_PAGE)}```", color=0x6ad643)
        embed.set_footer(text=f"Page {page} out of {len(drive_pages)}")
        await ctx.send(embed=embed)

        global global_num_reads
        global_num_reads += 1

@bot.command()
@commands.guild_only()
async def write(ctx, start_pos, data):
    """Read file"""
    try:
        parsed_start_pos = int(start_pos, 0)
    except ValueError:
        await ctx.send(ERRORS["badstartpos"])
        return

    try:
        b = bytes.fromhex(data)
    except ValueError:
        await ctx.send(ERRORS["invalidhex"])
        return

    with open("drive", "rb") as f:
        file_data = f.read()

        if parsed_start_pos + len(b) > len(file_data) or parsed_start_pos < 0:
            await ctx.send(ERRORS["outofbounds"])
            return

    with open("drive", "wb") as f:
        f.write(file_data[:parsed_start_pos] + b + file_data[parsed_start_pos: - len(b)])

    await ctx.send(f"Wrote {len(b)} byte(s) to position {parsed_start_pos} successfully!")

    global global_num_writes
    global global_bytes_written

    global_num_writes += 1
    global_bytes_written += len(b)

write_read_report.start()
bot.run(os.getenv("TOKEN"))

############
