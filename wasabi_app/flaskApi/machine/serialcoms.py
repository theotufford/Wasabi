#!./.venv/bin/python
import asyncio
import serial
import math
import RPi.GPIO as pio
import zlib
import time
import json
import struct
from .kinematics import Vec2d, solve_5bar_FK, solve_5bar_IK

pio.setmode(pio.BCM)


def int_vec_to_bytes(intgr_arr: list[int]) -> bytearray:
    outData = bytearray()
    for intgr in intgr_arr:
        outData += intgr.to_bytes(4, 'little', signed=True)
    return outData


TIMEOUT_S = 999

COMS_START_BYTE = b"\xf8"
EMPTY = 0
WAKE = 1
CONFIRM = 2
MESSAGE = 3
ERROR = 4
RE_REQUEST = 5
NEW_PUMP = 6
A_MOTOR = 7
B_MOTOR = 8
Z_MOTOR = 9
MACHINE_PIN_DEFINITIONS = 10
MOVE = 11
PUMP_ACTION = 12
ENABLE_PUMPS = 13
DISABLE_PUMPS = 14
ENABLE_MOTORS = 15
DISABLE_MOTORS = 16
HOME = 17
INITIAL_POSITION = 18
BUZZ = 19

COMS_INV = [
    "EMPTY",
    "WAKE",
    "CONFIRM",
    "MESSAGE",
    "ERROR",
    "RE_REQUEST",
    "NEW_PUMP",
    "A_MOTOR",
    "B_MOTOR",
    "Z_MOTOR",
    "MACHINE_PIN_DEFINITIONS",
    "MOVE",
    "PUMP_ACTION",
    "ENABLE_PUMPS",
    "DISABLE_PUMPS",
    "ENABLE_MOTORS",
    "DISABLE_MOTORS",
    "HOME",
    "INITIAL_POSITION",
    "BUZZ"
]


# abstracts the encode - decode process

class Packet:
    def __init__(self, code, datalen, data: bytearray):
        if datalen > 256:
            raise ValueError("packet data too large!")
        self.code = code
        self.datalen = datalen
        self.data = data
        self.checksum = 0

    def __repr__(self):
        return f"""
            {COMS_INV[self.code]}
            data: {self.data}
            calculated checksum: {self.calculate_checksum()}
            rx checksum:         {self.checksum}
        """
    # packet structure is strictly ordered by byte:
    # 0: start byte
    # 1: coms code
    # 2: data length
    # 3 to n + 3: data
    # n+4 to n+8: checksum

    def calculate_checksum(self) -> bytearray:
        message_bytes = self.make_header()
        message_bytes += self.data
        return zlib.crc32(message_bytes).to_bytes(4, byteorder='little')

    def make_header(self) -> bytearray:
        header = bytearray(COMS_START_BYTE)
        header += self.code.to_bytes(1)
        header += self.datalen.to_bytes(1)
        return header

    def get_full_bytes(self) -> bytearray:
        out_bytes = self.make_header()
        out_bytes += self.data
        out_bytes += zlib.crc32(out_bytes).to_bytes(4, byteorder='little')
        return out_bytes

    def get_int_argvec(self) -> list:
        intgr_iter = struct.iter_unpack("<i", self.data)
        argvec = [intgr[0] for intgr in intgr_iter]
        return argvec


def parse_header(header: bytearray) -> Packet:
    coms_code = int(header[1])
    datalen = int(header[2])
    new_packet = Packet(coms_code, datalen, b"")
    return new_packet


def make_new_packet(code, data: bytearray) -> Packet:
    return Packet(code=code, datalen=len(data), data=data)


class ComsChannel:

    def __init__(self):
        self.errcount = 0
        self.most_recent_rx: Packet
        self.most_recent_tx: Packet
        # initialize serial contact
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=TIMEOUT_S)

        self.startup_handshake()

    def startup_handshake(self):
        while True:
            asyncio.run(self.get_packet())
            code = self.most_recent_rx.code
            if code == WAKE:
                print("wake rxd")
                self.send_code(CONFIRM)
                continue
            if code == CONFIRM:
                self.send_code(CONFIRM)
                print("coms initialized")
                break
            raise ValueError(
                f"was expecting wake or confirm during boot, got: {code}")
        self.get_confirm()

    def __del__(self):
        self.ser.close()
        pio.cleanup()

    def re_request(self):
        return
        self.ser.reset_input_buffer()
        self.send_code(RE_REQUEST)

    def get_confirm(self):
        start = time.perf_counter()
        while True:
            asyncio.run(self.get_packet())
            code = self.most_recent_rx.code
            if code == CONFIRM:
                break
            current = time.perf_counter()
            if current - start > TIMEOUT_S:
                raise TimeoutError(
                    f"waited {TIMEOUT_S} seconds without recieving a confirm")

    def send_packet(self, message: Packet) -> None:
        # self.check_and_handle_re_req()
        print(f"sending {COMS_INV[message.code]} {message.get_int_argvec()}")
        self.most_recent_tx = message
        self.ser.write(message.get_full_bytes())

    def send_data(self, code, data) -> None:
        tmp = make_new_packet(code, data)
        self.send_packet(tmp)

    def send_code(self, code) -> None:
        self.send_data(code, b"")

    def send_int_vec(self, code, intgr_arr: list[int]) -> None:
        data = int_vec_to_bytes(intgr_arr)
        pack = make_new_packet(code, data)
        self.send_packet(pack)

    # meant to recieve absolute position in step units
    def send_move_steps(self, alpha: int, beta: int, z: int):
        self.send_int_vec(MOVE, [alpha, beta, z])
        self.get_confirm()

    def send_pump_action_steps(self, motor_id, speed, accel, vol_step_count):
        self.send_int_vec(PUMP_ACTION, [ motor_id, speed, accel, vol_step_count])
        self.get_confirm()

    async def check_and_handle_CRC32(self, callback: callable):
        start = time.perf_counter()
        current = start
        while self.ser.in_waiting < 4:
            if current - start > TIMEOUT_S:
                self.ser.reset_input_buffer()
                print("\n\nNon fatal error: missing checksum. Re-requesting\n\n")
                self.re_request()
                await self.get_packet()
            current = time.perf_counter()

        given = self.ser.read(4)
        self.most_recent_rx.checksum = given
        calculated = self.most_recent_rx.calculate_checksum()
        return
        if given != calculated:
            print(f"CRC error detected!! error counter is now {
                  self.errcount}, erroring packet:\n{self.most_recent_rx}")
            self.re_request()
            callback()

    async def get_header(self, timeout):
        self.most_recent_rx = Packet(EMPTY, 0, b"")
        start = time.perf_counter()
        while True:
            if self.ser.in_waiting > 0:
                initial_byte = self.ser.read(1)
                if initial_byte == COMS_START_BYTE:
                    break
                else:
                    continue
            current = time.perf_counter()
            if current - start > timeout:
                return None
        header_data = bytearray(COMS_START_BYTE)
        header_data += self.ser.read(2)
        self.most_recent_rx = parse_header(header_data)
        return self.most_recent_rx

    async def check_and_handle_re_req(self):
        found_message = await self.get_header(0)
        if found_message is None:
            return False
        if found_message.code == RE_REQUEST:
            self.most_recent_rx.checksum = self.ser.read(4)
            await self.check_and_handle_CRC32(self.check_and_handle_re_req)
            self.send_packet(self.most_recent_tx)
            return True
        self.get_packet()

    async def get_packet(self, header_already_found=False):
        recieved = None
        if not header_already_found:
            recieved = await self.get_header(TIMEOUT_S)
        else:
            recieved = self.most_recent_rx
        if recieved is None:
            raise TimeoutError(f"waited {TIMEOUT_S} seconds for message")

        len = self.most_recent_rx.datalen

        if len > 0:
            start = time.perf_counter()
            while True:
                if self.ser.in_waiting >= len:
                    self.most_recent_rx.data = self.ser.read(len)
                    break
                current = time.perf_counter()
                if current - start > TIMEOUT_S:
                    raise TimeoutError(f"""
                        waited {TIMEOUT_S} seconds without recieving full body
                        expected: {len} have: {self.ser.in_waiting}
                        """)

        self.check_and_handle_CRC32(self.get_packet)

        print(f"got {COMS_INV[self.most_recent_rx.code]}: {
              self.most_recent_rx.get_int_argvec()}")

        return

    def send_buzz(self, motor_id: int):
        motor_id = int(motor_id)
        self.send_data(BUZZ, motor_id.to_bytes(4, 'little', signed=True))

    def send_home(self):
        self.send_code(HOME)


if __name__ == '__main__':
    pass
