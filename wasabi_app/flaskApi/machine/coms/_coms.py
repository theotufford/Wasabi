import asyncio
import serial
import math
import RPi.GPIO as pio
import zlib
import time
import json
from typing import Literal
from . import codex
from ._packet import make_new_packet, Packet, state_packet, parse_header


class ComsChannel:
    def __init__(self, timeout):
        self.picostate: Literal[codex.BUSY, codex.LISTENING] = codex.BUSY
        self.tx_head = 0
        self.tx_tail = 0
        self.tx_queue_size = 10
        self.txQueue = [None for i in range(0, self.tx_queue_size)]
        # initialize serial contact
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=timeout)
        self.response_tree = {}
        self.hwinit()

        def send_listening(ctx):
            self.queue_packet(state_packet(codex.LISTENING))

        def check_ack(ctx):
            got_packet: Packet = ctx["rxpacket"]
            return got_packet.code == codex.LISTENING

        def purge_syn(ctx):
            self.delete_response("startup_syn")
            self.delete_response("startup_ack")

        self.add_response("startup_syn", lambda ctx: True, send_listening)
        self.add_response("startup_ack", check_ack, purge_syn)

    def add_response(self, name, condition_callback, action_callback):
        self.response_tree[name] = (name, condition_callback, action_callback)

    def delete_response(self, name):
        del self.response_tree[name]

    def queue_packet(self, packet: Packet):
        self.txQueue[self.tx_head] = packet
        self.tx_head = (self.tx_head + 1) % self.tx_queue_size

    async def listen(self) -> Packet | None:
        self.ser.write(state_packet(codex.LISTENING).get_full_bytes())
        self.ser.flush()
        start = time.perf_counter()
        header_data: bytearray
        while True:
            if self.ser.in_waiting > 4:
                header_data = self.ser.read(4)
                if header_data[0] == codex.COMS_START_BYTE:
                    break
                else:
                    continue
            current = time.perf_counter()
            if current - start > 5:
                return None

        coms_code, datatype, datalen, = parse_header(header_data)

        start = time.perf_counter()
        serial_data: bytearray
        while True:
            if self.ser.in_waiting >= datalen:
                serial_data = self.ser.read(datalen)
            current = time.perf_counter()
            if current - start > 2:
                raise serial.SerialTimeoutException()
                return None

        return Packet(coms_code, datatype, datalen, serial_data)

    async def loop(self):
        packet_recieved = await self.listen()

        called_functions = []
        if packet_recieved is not None:
            for name, condition_callback, action_callback in self.response_tree.values():
                context = {"self": self, "rxpacket": packet_recieved,
                           "called_functions": called_functions}
                case = condition_callback(context)
                if case:
                    action_callback(context)
                    called_functions.append(name)

        if self.picostate == codex.LISTENING:
            if self.tx_tail != self.tx_head:
                next_packet = self.txQueue[self.tx_tail]
                self.tx_tail = (self.tx_tail + 1) % self.tx_queue_size
                self.ser.write(next_packet.get_full_bytes())
                self.ser.flush()
                self.picostate = codex.BUSY

    def __del__(self):
        self.ser.close()
        pio.cleanup()


if __name__ == '__main__':
    pass
