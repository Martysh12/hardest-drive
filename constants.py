PREFIX = "hdd$"

HELP = f"""The bot is simple - you store and read data.

Commands:
```
 - {PREFIX}read                        - Read data from the Hard Drive
 - {PREFIX}write <start> <data in hex> - Write data to the Hard Drive
```

Notes:
The start position in `{PREFIX}write` is counted from 0,
meaning that writing from start position `0` would write
from the start of the hard drive.

"Data in hex" means data structured like this:
`FF4BAA10`
"""
