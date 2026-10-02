COMS_START_BYTE = b"\xf8"
STATE = 0
MESSAGE = 1
SETTINGS = 2
MOVE = 3
HOME = 4
BUZZ = 5

INT = 0
FLOAT = 1
NONE = 2

types_by_code = [int, float, None]

COMS_INV = [
    "STATE ",
    "MESSAGE ",
    "SETTINGS ",
    "MOVE ",
    "HOME ",
    "BUZZ ",
]

BUSY = 0
LISTENING = 1
