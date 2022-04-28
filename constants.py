PREFIX = "hdd$"

HELP = f"""The bot is simple - you store and read data.
There are only 2 commands, `read` and `write` (if you
don't count the `{PREFIX}limit` command).

Commands:
```
 - {PREFIX}read <opt: page> <opt: bytes per line> 
    - Read data from the Hard Drive

 - {PREFIX}write <start> <data in hex>
    - Write data to the Hard Drive


 - {PREFIX}limit
    - Tell you how many bytes you have left
```

Notes:
The start position in `{PREFIX}write` is counted from 0,
meaning that writing from start position `0` would write
from the start of the hard drive.

"Data in hex" means data structured like this: `FF4BAA10`

The `bytes per line` field in `read` cannot be less than 4.

Limit:
There is a limit to how many bytes you can place - 8 bytes
every 5 minutes.
You can check your limit using the {PREFIX}limit command.
"""

ERRORS = {
    "args"        : "Please pass all required arguments!",
    "guildonly"   : "Commands can only be used in servers!",
    "invalidcmd"  : "Invalid command!",
    "bprtoolow"   : "Too little bytes per line!",
    "badstartpos" : "Invalid start position!",
    "invalidhex"  : "Invalid hexadecimal string!",
    "outofbounds" : "Data is out of bounds!",
    "invalidpage" : "Invalid page number!",
    "limited"     : "The amount of bytes exceeds your limit! ({} > {})"
}

BYTES_PER_PAGE = 128
LIMIT_RESET_MINUTES = 5
