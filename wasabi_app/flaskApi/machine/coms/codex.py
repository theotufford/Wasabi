
COMS_START_BYTE = b"\xf8"
STATE = 0
RE_REQUEST = 1
MESSAGE = 2
MOVE = 3
HOME = 4
WAKE = 5

INT = 0
FLOAT = 1
STRUCT = 2
NONE = 3

TRAPEZOIDAL = 0
NO_DECEL = 1
NO_ACCEL = 2
LINEAR = 3

types_by_code = [
    int,
    float,
    bytearray,  # using this like void *
    None
]

COMS_INV = [
    "STATE",
    "RE_REQUEST",
    "MESSAGE",
    "MOVE",
    "HOME",
    "WAKE"
]

BUSY = 0
LISTENING = 1
IDLE = 2

A_MOTOR = 0
B_MOTOR = 1
Z_MOTOR = 2


def PUMP(num):
    return num + 3
