import asyncio
import serial
import math
import threading
import RPi.GPIO as pio
import zlib
import time
import json
from typing import Literal
import threading
from . import codex
from .packet import make_new_packet, Packet, code_packet, state_packet, parse_header, get_settings_packet, parse_int, HEADER_SIZE


class Loopctx:
    def __init__(self, current_packet: Packet, called_functions: list[str]):
        self.current_packet = current_packet
        self.called_functions = called_functions


def code_dependent_true(target_code):
    return lambda ctx: ctx.current_packet.code == target_code


class ComsChannel:
    def __init__(self, settings_path,  timeout):
        self.picostate: Literal[codex.BUSY,
                                codex.LISTENING, codex.IDLE] = codex.BUSY
        self.self_state: Literal[codex.BUSY,
                                              codex.LISTENING, codex.IDLE] = codex.BUSY
        self.settings_path = settings_path
        self.queue_size = 60
        self.tx_head = 0
        self.tx_tail = 0
        self.queue_count = 0
        self.queue_lock = threading.RLock()
        self.txQueue: list[Packet | None] = [
            None for i in range(0, self.queue_size)]
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

        def update_pico_state(context: Loopctx):
            self.picostate = context.current_packet.data[0]

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
        with self.queue_lock:
            if self.queue_count == self.queue_size:
                raise OverflowError("trying to queue too many packets!")
                return
            self.txQueue[self.tx_head] = packet
            self.tx_head = (self.tx_head + 1) % self.queue_size
            self.queue_count += 1

    def listen_for_packet(self):
        header_data = bytearray()
        while True:
            if self.ser.in_waiting > HEADER_SIZE:
                if len(header_data) == 0 or header_data[0] != codex.COMS_START_BYTE[0]:
                    header_data = self.ser.read(1)
                    continue
                else:
                    header_data += self.ser.read(HEADER_SIZE-1)
                    break
            else:
                return None
        coms_code, datatype, datalen, = parse_header(header_data)
        print(f"got {codex.COMS_INV[coms_code]}")
        serial_data: bytearray
        checksum: int

        if datatype is None:
            output = code_packet(coms_code)

        start = time.perf_counter()
        while True:
            if self.ser.in_waiting >= datalen + 4:  # (checksum len)
                serial_data = self.ser.read(datalen)
                checksum = parse_int(self.ser.read(4))
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
        with self.queue_lock:
            next_packet = self.txQueue[self.tx_tail]
            if next_packet.code == codex.STATE:
                self.self_state = next_packet.data[0]

            print(f"transmitting packet: {next_packet}")
            self.ser.write(next_packet.get_full_bytes())
            self.ser.flush()
            self.txQueue[self.tx_tail] = None
            self.tx_tail = (self.tx_tail + 1) % self.queue_size
            self.queue_count -= 1

    def init_coms_handler_loop(self):
        last = self.picostate
        while True:
            # print(f"\r time: {time.perf_counter()}, picostate: {codex.STATE_INV[self.picostate]}", end=" ")
            with self.queue_lock:
                if self.picostate != codex.BUSY:
                    if self.queue_count > 0:
                        self.send_packet(state_packet(codex.LISTENING))
                    elif self.self_state == codex.LISTENING:
                        self.send_packet(state_packet(codex.IDLE))

                    while self.queue_count > 0:
                        self.transmit_next()
                        if self.queue_count == 0:
                            self.picostate = codex.BUSY

            current_packet = self.listen_for_packet()
            if current_packet is None:
                continue

            called_functions = []
            print(f"got packet: {current_packet}")
            for name, condition_callback, action_callback in self.response_tree.values():
                context = Loopctx(current_packet, called_functions)
                if condition_callback(context):
                    action_callback(context)
                    called_functions.append(name)
            if self.picostate != last:
                last = self.picostate
                print(f"state updated: {codex.STATE_INV[self.picostate]}")

    def __del__(self):
        self.ser.close()
        pio.cleanup()


if __name__ == '__main__':
    pass
