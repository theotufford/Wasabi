import asyncio
import serial
import math
import RPi.GPIO as pio
import zlib
import time
import json
import struct
from .kinematics import Vec2d, solve_5bar_FK, solve_5bar_IK
from queue import Queue
from typing import Literal


def int_vec_to_bytes(intgr_arr: list[int]) -> bytearray:
    outData = bytearray()
    for intgr in intgr_arr:
        outData += intgr.to_bytes(4, 'little', signed=True)
    return outData


# state enum
BUSY = 0
LISTENING = 1


TIMEOUT_S = 999

COMS_START_BYTE = b"\xf8"
STATE = 0
MESSAGE = 1
SETTINGS = 2
MOVE = 3
HOME = 4
BUZZ = 5

COMS_INV = [
    "STATE ",
    "MESSAGE ",
    "SETTINGS ",
    "MOVE ",
    "HOME ",
    "BUZZ ",
]


# abstracts the encode - decode process
class Packet:
    def __init__(self, code, datatype, datalen, data: bytearray):
        if datalen > 256:
            raise ValueError("packet data too large!")
        self.code = code
        self.datalen = datalen
        if datatype == int:
            self.datatype_id = 0
        elif datatype == float:
            self.datatype_id = 1
        elif datatype is None:
            self.datatype_id = 2
        else:
            return NotImplemented
        self.data = data
        self.checksum = 0

    # packet structure is strictly ordered by byte:
    # 0: start byte
    # 1: coms code
    # 2: data type
    # 3: data length
    # 4 to n + 3: data
    # n+4 to n+8: checksum

    def calculate_checksum(self) -> bytearray:
        message_bytes = self.make_header()
        message_bytes += self.data
        return zlib.crc32(message_bytes).to_bytes(4, byteorder='little')

    def make_header(self) -> bytearray:
        header = bytearray(COMS_START_BYTE)
        header += self.code.to_bytes(1)
        header += self.datatype_id.to_bytes(1)
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
    datatype = int(header[2])
    datalen = int(header[3])
    new_packet = Packet(coms_code, datatype, datalen, b"")
    return new_packet


def make_new_packet(code, datatype, data: bytearray) -> Packet:
    return Packet(code=code, datatype=datatype, datalen=len(data), data=data)


def state_packet(state: Literal[BUSY, LISTENING]):

    return make_new_packet(STATE, int,)


class ComsChannel:

    def __init__(self):
        self.picostate: Literal[BUSY, LISTENING]
        self.rxQueue: Queue[Packet] = Queue(maxsize=10)
        self.txQueue()
        # initialize serial contact
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=TIMEOUT_S)
        self.startup_handshake()

    def comsloop(self):
        pass

    def startup_handshake(self):
        self.send_packet(state_packet(LISTENING))
        yield

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
        print(f"sending {COMS_INV[message.code]} {message.get_int_argvec()}")
        self.most_recent_tx = message
        self.ser.write(message.get_full_bytes())

    def send_int_vec(self, code, intgr_arr: list[int]) -> None:
        data = int_vec_to_bytes(intgr_arr)
        pack = make_new_packet(code, data)
        self.send_packet(pack)

    # meant to recieve absolute position in step units
    def send_move_steps(self, alpha: int, beta: int, z: int):
        self.send_int_vec(MOVE, [alpha, beta, z])
        self.get_confirm()

    def send_pump_action_steps(self, motor_id, speed, accel, vol_step_count):
        self.send_int_vec(
            PUMP_ACTION, [motor_id, speed, accel, vol_step_count])
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


def get_settings_packet(settings_dict):
    motors = settings["machine"]["motors"]
    common_settings = motors["common_settings"]
    settings = [
        # a motor settings
        motors["a"]["stp_pin"],
        motors["a"]["dir_pin"],
        motors["a"]["invert_dir"],
        1600,  # hard coded to max microsteps
        common_settings["arms_angular_max_velocity"],
        common_settings["arms_angular_accel"],
        # b motor settings
        motors["b"]["stp_pin"],
        motors["b"]["dir_pin"],
        motors["b"]["invert_dir"],
        1600,  # hard coded to max microsteps
        common_settings["arms_angular_max_velocity"],
        common_settings["arms_angular_accel"],
        # z motor settings
        motors["z"]["stp_pin"],
        motors["z"]["dir_pin"],
        motors["z"]["invert_dir"],
        1600,  # hard coded to max microsteps
        common_settings["z_max_angular_velocity"],
        common_settings["z_angular_accel"]
    ]
    pump_microsteps = common_settings["pump_steps_per_revoulution"]
    # send pump motor settings -----------------
    for pump_conf in motors["pumps"]:
        settings += [
            pump_conf["stp_pin"],
            pump_conf["dir_pin"],
            pump_conf["invert_dir"],
            pump_microsteps,
            pump_conf["ang_v_max"],
            pump_conf["ang_accel_rad"]
        ]
    # send other pico pin settings -------------
    pinsettings = settings["machine"]["pins"]
    settings += [
        pinsettings["motor_enable_pin"],
        pinsettings["pump_enable_pin"],
        pinsettings["a_endstop"],
        pinsettings["b_endstop"],
        pinsettings["z_endstop"]
    ]
    return settings


if __name__ == '__main__':
    pass
