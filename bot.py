import nextcord
from nextcord.ext import commands, tasks

from dotenv import load_dotenv

import binascii
import curses
import datetime
import io
import json
import math
import os
import textwrap

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

last_bytes_written = b''

limits = {}

limits_last_cleared = 0

# Graphics-related variables
stdscr = curses.initscr()

log_stream = io.StringIO()
event_stream = io.StringIO()

#############

# Setting up files
if not os.path.exists("drive"):
    with open("drive", "w") as f:
        f.write("[]")

if not os.path.exists("history.json"):
    with open("history.json", "w"):
        pass

print(f"HardestDrive v1.0 by Martysh12#1610", file=log_stream)

# Setting up graphics
curses.curs_set(False)
stdscr.clear()

bot = commands.Bot(command_prefix=PREFIX, activity=nextcord.Game(PREFIX + "help"))
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Ready! Logged in as {bot.user} (ID: {bot.user.id})", file=log_stream)

@tasks.loop(seconds=0.5)
async def graphics():
    stdscr.clear()

    rows, cols = stdscr.getmaxyx()

    # Drawing screen borders #

    stdscr.addstr(
        0,
        0,
        BORDER_CHARS["corners"]["down_right"].ljust(
            cols - 1, BORDER_CHARS["flat"]["horizontal"]
        )
        + BORDER_CHARS["corners"]["down_left"],
    )

    for i in range(1, rows - 1):
        stdscr.addstr(
            i,
            0,
            BORDER_CHARS["flat"]["vertical"].ljust(cols - 1)
            + BORDER_CHARS["flat"]["vertical"],
        )

    stdscr.addstr(
        rows - 1,
        0,
        BORDER_CHARS["corners"]["up_right"].ljust(
            cols - 1, BORDER_CHARS["flat"]["horizontal"]
        ),
    )
    stdscr.insch(rows - 1, cols - 1, ord(BORDER_CHARS["corners"]["up_left"]))

    ##########################

    # Drawing panels #

    stdscr.addch(0, round(cols / 2), BORDER_CHARS["half_crosses"]["horizontal_down"])

    for i in range(1, round(rows / 2)):
        stdscr.addstr(
            i,
            1,
            BORDER_CHARS["flat"]["vertical"].rjust(round(cols / 2))
        )

    stdscr.addstr(
        round(rows / 2), 0,
        BORDER_CHARS["half_crosses"]["vertical_right"]                    \
        + BORDER_CHARS["flat"]["horizontal"] * (math.ceil(cols / 2) - 1)  \
        + BORDER_CHARS["half_crosses"]["horizontal_up"]                   \
        + BORDER_CHARS["flat"]["horizontal"] * (math.floor(cols / 2) - 2) \
        + BORDER_CHARS["half_crosses"]["vertical_left"]
    )

    ##################

    # Drawing text #

    stdscr.addstr(0, 2, " Log ")
    stdscr.addstr(0, math.ceil(cols / 2) + 2, " Events ")

    stdscr.addstr(round(rows / 2), 2, " Statistics ")

    ################

    # Drawing data #

    wrapped_log = [
        line
        for para in log_stream.getvalue().split('\n')
        for line in textwrap.wrap(
            para,
            width=math.ceil(cols / 2) - 2
        )
    ][-round((rows / 2) - 2):]

    for i, v in enumerate(wrapped_log):
        stdscr.addstr(i + 1, 2, v)

    wrapped_events = [
        line
        for para in event_stream.getvalue().split('\n')
        for line in textwrap.wrap(
            para,
            width=math.floor(cols / 2) - 2
        )
    ][-round((rows / 2) - 2):]

    for i, v in enumerate(wrapped_events):
        stdscr.addstr(i + 1, math.ceil(cols / 2) + 2, v)

    # Statistics
    stdscr.addstr(round(rows / 2) + 1, 2, f"Times read          : {global_num_reads}")
    stdscr.addstr(round(rows / 2) + 2, 2, f"Times written       : {global_num_writes}")

    stdscr.addstr(round(rows / 2) + 4, 2, f"Total bytes written : {global_bytes_written}")

    stdscr.addstr(round(rows / 2) + 6, 2, f"Last bytes written  : {last_bytes_written}")

    

    with open("drive", "rb") as f:
        drive_content = f.read()
        page = [drive_content[i:i + 256] for i in range(0, len(drive_content), 256)][0]

        split_hexdump = make_hexdump(page, bytes_per_line=16).split("\n")

        x_pos = cols - len(max(split_hexdump, key=len)) - 2

        stdscr.addstr(round(rows / 2) + 1, x_pos, f"1st & 2nd page hexdump:")

        for i, v in enumerate(split_hexdump):
            stdscr.addstr(i + round(rows / 2) + 3, x_pos, v)

    ################

    stdscr.refresh()

@tasks.loop(minutes=LIMIT_RESET_MINUTES)
async def clear_limits():
    global limits
    global limits_last_cleared

    for i in limits.keys():
        limits[i] = 8

    limits_last_cleared = datetime.datetime.now()

    print(f"[{datetime.datetime.now().strftime('%X')}] Limits have been reset.", file=log_stream)

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

        print(f"[{datetime.datetime.now().strftime('%X')}] READ:\t{str(ctx.author)}, {page=}, {bpr=}", file=event_stream)
        write_history(ctx.author.id, str(ctx.message.author), False, datetime.datetime.now().isoformat())

        embed = nextcord.Embed(title="Hexdump", description=f"```{make_hexdump(current_page, bytes_per_line=bpr, offset=(page - 1) * BYTES_PER_PAGE)}```", color=0x6ad643)
        embed.set_footer(text=f"Page {page} out of {len(drive_pages)}")
        await ctx.send(embed=embed)

@bot.command()
@commands.guild_only()
async def write(ctx, start_pos, *data):
    """Read file"""

    data = " ".join(data)

    if ctx.author.id not in limits:
        limits[ctx.author.id] = 8

    try:
        parsed_start_pos = int(start_pos, 0)
    except ValueError:
        await ctx.send(ERRORS["badstartpos"])
        return

    if data.startswith("\'") and data.endswith("\'") and len(data) >= 3: # it's text
        b = data[1:-1].encode("UTF-8")
    else:
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
    print(f"[{datetime.datetime.now().strftime('%X')}] WRITE:\t{str(ctx.author)}, {parsed_start_pos=}, {b=}", file=event_stream)

    limits[ctx.author.id] -= len(b)

    global last_bytes_written
    last_bytes_written = b

    await ctx.send(f"Wrote {len(b)} byte(s) to position {parsed_start_pos} successfully!")

@bot.command()
@commands.guild_only()
async def limit(ctx):
    if ctx.author.id not in limits:
        limits[ctx.author.id] = 8

    message = ""
    message += f"You have {limits[ctx.author.id]} byte(s) left.\n"
    message += f"Limits reset <t:{round((limits_last_cleared + datetime.timedelta(minutes=5)).timestamp())}:R>."
    
    print(f"[{datetime.datetime.now().strftime('%X')}] LIMIT:\t{str(ctx.author)}, {limits[ctx.author.id]}", file=event_stream)

    await ctx.send(message)

graphics.start()
clear_limits.start()
bot.run(os.getenv("TOKEN"))

############
