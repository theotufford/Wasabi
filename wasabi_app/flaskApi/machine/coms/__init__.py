import asyncio
import serial
import math
import threading
import RPi.GPIO as pio
import zlib
import time
import json
from typing import Literal
from . import codex
from .packet import make_new_packet, Packet, empty_code_packet, parse_header, get_settings_packet, HEADER_SIZE, parse_int


class Loopctx:
    def __init__(self, current_packet: Packet, called_functions: list[str]):
        self.current_packet = current_packet
        self.called_functions = called_functions


def code_dependent_true(target_code):
    return lambda ctx: ctx.current_packet.code == target_code


class ComsChannel:
    def __init__(self, timeout, settings_path):
        self.picostate: Literal[codex.BUSY,
                                codex.LISTENING, codex.IDLE] = codex.BUSY
        self.settings_path = settings_path
        self.queue_size = 60
        self.tx_head = 0
        self.tx_tail = 0
        self.txQueue = [None for i in range(0, self.queue_size)]
        self.timeout = timeout
        # initialize serial contact
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=timeout)
        self.response_tree = {}

        # default responses

        self.add_response("reboot_response",
                          code_dependent_true(codex.WAKE),
                          lambda context: self.send_packet(
                              get_settings_packet(self.settings()))
                          )

        def update_pico_state(contex):
            pack: Packet = contex["rxpacket"]
            self.picostate = pack.data[0]

        self.add_response("state_response",
                          code_dependent_true(codex.STATE),
                          update_pico_state)

    def settings(self):
        with open(self.settings_path, "r") as conf:
            settings = json.load(conf)
            return settings

    def add_response(self, name, condition_callback, action_callback):
        self.response_tree[name] = (name, condition_callback, action_callback)

    def delete_response(self, name):
        del self.response_tree[name]

    def send_packet(self, packet: Packet):
        self.txQueue[self.tx_head] = packet
        self.tx_head = (self.tx_head + 1) % self.queue_size

    async def listen_until_packet(self):
        while True:
            header_data: bytearray

            while True:
                if self.ser.in_waiting > 0:
                    header_data = self.ser.read(1)
                    if header_data[0] == codex.COMS_START_BYTE[0]:
                        header_data += self.ser.read(HEADER_SIZE - 1)
                        break
                else:
                    asyncio.sleep(0)
            coms_code, datatype, datalen, = parse_header(header_data)

            serial_data: bytearray
            checksum: int
            start = time.perf_counter()
            while True:
                if self.ser.in_waiting >= datalen + 4:  # (checksum len)
                    serial_data = self.ser.read(datalen)
                    checksum = parse_int(self.ser.read(datalen))
                    break
                current = time.perf_counter()
                if current - start > self.timeout:
                    raise serial.SerialTimeoutException(
                        f"""
                        waited for packet for {self.timeout} seconds
                        after receiving header but got no data
                        header: {header_data}
                        parsed header: {parse_header(header_data)}
                        """)
            output = Packet(coms_code, datatype, datalen,
                            serial_data, checksum)
            return output

    def transmit_next(self):
        next_packet = self.txQueue[self.tx_tail]
        self.ser.write(next_packet.get_full_bytes())
        self.ser.flush()
        self.txQueue[self.tx_tail] = None
        self.tx_tail = (self.tx_tail + 1) % self.queue_size

    async def init_coms_handler_loop(self):
        while True:
            if self.picostate != codex.BUSY:
                if self.q:  # nothing to transmit
                    self.send_packet(empty_code_packet(codex.IDLE))
                else:
                    self.send_packet(empty_code_packet(state=codex.LISTENING))

            while self.tx_tail != self.tx_head and self.picostate != codex.BUSY:
                self.transmit_next()
                self.picostate = codex.BUSY

            if self.picostate in [codex.BUSY, codex.IDLE]:
                called_functions = []
                current_packet = await self.listen_until_packet()
                for name, condition_callback, action_callback in self.response_tree.values():
                    context = {}
                    if condition_callback(context):
                        action_callback(context)
                        called_functions.append(name)
            asyncio.sleep(0)

    def __del__(self):
        self.ser.close()
        pio.cleanup()


if __name__ == '__main__':
    pass
