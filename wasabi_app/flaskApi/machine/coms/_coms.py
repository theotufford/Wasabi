import asyncio
import serial
import math
import RPi.GPIO as pio
import zlib
import time
import json
from queue import Queue
from typing import Literal
from . import codex
from ._packet import make_new_packet, Packet


def state_packet(state: Literal[codex.BUSY, codex.LISTENING]):
    return make_new_packet(codex.STATE, int)


class ComsChannel:
    def __init__(self, timeout):
        self.picostate: Literal[codex.BUSY, codex.LISTENING]
        self.rxQueue: Queue[Packet] = Queue(maxsize=10)
        self.txQueue()
        # initialize serial contact
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=timeout)
        self.startup_handshake()

    def startup_handshake(self):
        self.send_packet(state_packet(codex.LISTENING))

    def __del__(self):
        self.ser.close()
        pio.cleanup()


if __name__ == '__main__':
    pass
