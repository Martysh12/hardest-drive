import nextcord
from nextcord.ext import commands, tasks

from dotenv import load_dotenv

import binascii
import datetime
import json
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

def write_history(user_id: int, username: str, is_write: bool, time: str, data: bytes=b""):
    with open("history.json", "r+") as f:
        history = json.load(f)

        to_append = {
            "id": user_id,
            "name": username,
            "is_write": is_write,
            "timestamp": time
        }

        if is_write:
            to_append["data"] = binascii.b2a_base64(data).decode("UTF-8").replace("\n", "")

        history.append(to_append)

        # Clear the file
        f.seek(0)
        f.truncate(0)

        json.dump(history, f)

#############



# VARIABLES #

global_num_reads = 0
global_num_writes = 0
global_bytes_written = 0

limits = {}

limits_last_cleared = 0

#############

# Setting up files
if not os.path.exists("drive"):
    with open("drive", "w") as f:
        f.write("[]")

if not os.path.exists("history.json"):
    with open("history.json", "w"):
        pass

print(f"HardestDrive v1.0 by Martysh12#1610")

bot = commands.Bot(command_prefix=PREFIX, activity=nextcord.Game(PREFIX + "help"))
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user} (ID: {bot.user.id})")

@tasks.loop(minutes=5)
async def write_read_report():
    global global_num_reads
    global global_num_writes
    global global_bytes_written

    print(f"[{datetime.datetime.now().strftime('%X')}] Operations since {datetime.datetime.now() - datetime.timedelta(minutes=5)}:")
    print("\t" + "Reads: "         + str(global_num_reads))
    print("\t" + "Writes: "        + str(global_num_writes))
    print("\t" + "Bytes written: " + str(global_bytes_written))
    print()

    global_num_reads = 0
    global_num_writes = 0
    global_bytes_written = 0

@tasks.loop(minutes=LIMIT_RESET_MINUTES)
async def clear_limits():
    global limits
    global limits_last_cleared

    for i in limits.keys():
        limits[i] = 8

    limits_last_cleared = datetime.datetime.now()

    print(f"[{datetime.datetime.now().strftime('%X')}] Limits have been reset.")

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

    if page < 1:
        await ctx.send(ERRORS["invalidpage"])
        return

    with open("drive", "rb") as f:
        drive_content = f.read()
        drive_pages = [drive_content[i:i + BYTES_PER_PAGE] for i in range(0, len(drive_content), BYTES_PER_PAGE)]

        try:
            current_page = drive_pages[page - 1]
        except:
            await ctx.send(ERRORS["invalidpage"])
            return

        global global_num_reads
        global_num_reads += 1

        write_history(ctx.author.id, str(ctx.message.author), False, datetime.datetime.now().isoformat())

        embed = nextcord.Embed(title="Hexdump", description=f"```{make_hexdump(current_page, bytes_per_line=bpr, offset=(page - 1) * BYTES_PER_PAGE)}```", color=0x6ad643)
        embed.set_footer(text=f"Page {page} out of {len(drive_pages)}")
        await ctx.send(embed=embed)

@bot.command()
@commands.guild_only()
async def write(ctx, start_pos, data):
    """Read file"""

    if ctx.author.id not in limits:
        limits[ctx.author.id] = 8

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

    if len(b) > limits[ctx.author.id]:
        await ctx.send(ERRORS["limited"].format(len(b), limits[ctx.author.id]))
        return

    with open("drive", "rb") as f:
        file_data = f.read()

        if parsed_start_pos + len(b) > len(file_data) or parsed_start_pos < 0:
            await ctx.send(ERRORS["outofbounds"])
            return

    with open("drive", "wb") as f:
        f.write(file_data[:parsed_start_pos] + b + file_data[parsed_start_pos + len(b):])

    global global_num_writes
    global global_bytes_written

    global_num_writes += 1
    global_bytes_written += len(b)

    write_history(ctx.author.id, str(ctx.message.author), True, datetime.datetime.now().isoformat(), b)

    limits[ctx.author.id] -= len(b)

    await ctx.send(f"Wrote {len(b)} byte(s) to position {parsed_start_pos} successfully!")

@bot.command()
@commands.guild_only()
async def limit(ctx):
    if ctx.author.id not in limits:
        limits[ctx.author.id] = 8

    message = ""
    message += f"You have {limits[ctx.author.id]} byte(s) left.\n"
    message += f"Limits reset <t:{round((limits_last_cleared + datetime.timedelta(minutes=5)).timestamp())}:R>."

    await ctx.send(message)

write_read_report.start()
clear_limits.start()
bot.run(os.getenv("TOKEN"))

############
