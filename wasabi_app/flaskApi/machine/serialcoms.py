#!./.venv/bin/python
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
        outData += intgr.to_bytes(4, 'little', signed=False)
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
        # reboot the pico
        run_pin = 18
        pio.setup(run_pin, pio.OUT)
        pio.output(run_pin, pio.LOW)
        time.sleep(0.1)
        pio.output(run_pin, pio.HIGH)
        time.sleep(0.1)

        # initialize serial contact
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=TIMEOUT_S)

        # do startup handshake
        print("initiating coms startup handshake")
        while True:
            self.get_packet()
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
        self.await_confirm()

    def __del__(self):
        self.ser.close()
        pio.cleanup()

    def re_request(self):
        return
        self.ser.reset_input_buffer()
        self.send_code(RE_REQUEST)

    def await_confirm(self):
        start = time.perf_counter()
        while True:
            self.get_packet()
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

    def send_move_steps(self, a_target_abs: int, b_target_abs: int, z_target_rel: int):
        self.send_int_vec(MOVE, [a_target_abs, b_target_abs, z_target_rel])

    def send_pump_action_steps(self, motor_id, vol_step_count):
        self.send_int_vec(PUMP_ACTION, [motor_id, vol_step_count])

    def check_and_handle_CRC32(self, callback: callable):
        start = time.perf_counter()
        current = start
        while self.ser.in_waiting < 4:
            if current - start > TIMEOUT_S:
                self.ser.reset_input_buffer()
                print("\n\nNon fatal error: missing checksum. Re-requesting\n\n")
                self.re_request()
                self.get_packet()
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

    def await_header(self, timeout):
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

    def check_and_handle_re_req(self):
        found_message = self.await_header(0)
        if found_message is None:
            return False
        if found_message.code == RE_REQUEST:
            self.most_recent_rx.checksum = self.ser.read(4)
            self.check_and_handle_CRC32(self.check_and_handle_re_req)
            self.send_packet(self.most_recent_tx)
            return True
        self.get_packet()

    def get_packet(self, header_already_found=False):
        recieved = None
        if not header_already_found:
            recieved = self.await_header(TIMEOUT_S)
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

    def send_settings(self, settings):
        # send kinematic motor settings ------------
        motors = settings["motors"]
        a_mot_settings = get_mot_argvec(motors["a"])
        self.send_int_vec(A_MOTOR, a_mot_settings)
        self.await_confirm()

        b_mot_settings = get_mot_argvec(motors["b"])
        self.send_int_vec(B_MOTOR, b_mot_settings)
        self.await_confirm()

        z_mot_settings = get_mot_argvec(motors["z"])
        self.send_int_vec(Z_MOTOR, z_mot_settings)
        self.await_confirm()

        # send pump motor settings -----------------
        for pump_conf in settings["motors"]["pumps"]:
            pump_settings = get_mot_argvec(pump_conf)
            self.send_int_vec(NEW_PUMP, pump_settings)
            self.await_confirm()

        # send other pin settings ------------------
        pinsettings = settings["machine"]["pins"]
        pins = [
            pinsettings["motor_enable_pin"],
            pinsettings["pump_enable_pin"],
            pinsettings["a_endstop"],
            pinsettings["b_endstop"],
            pinsettings["z_endstop"]
        ]

        self.send_int_vec(MACHINE_PIN_DEFINITIONS, pins)
        self.send_code(CONFIRM)
        self.await_confirm()

    def send_buzz(self, motor_id: int):
        self.send_data(BUZZ, motor_id.to_bytes(4, 'little', signed=False))

    def send_home(self):
        self.send_code(HOME)


def get_mot_argvec(mot_conf):
    # order dependent parsing of motor config because coms rx relies on order
    out = [
        mot_conf["stp_pin"],
        mot_conf["dir_pin"],
        mot_conf["invert_dir"],
        mot_conf["steps_per_rev"],
        mot_conf["ang_v_max"],
        mot_conf["ang_accel_rad"],
    ]
    return out


if __name__ == '__main__':
    coms = ComsChannel()
    settings = None
    with open("./machine_config.json", "r") as conf:
        settings = json.load(conf)
        coms.send_settings(settings)

    a_steps_per_rad = settings["motors"]["a"]["steps_per_rev"] / (2 * math.pi)
    b_steps_per_rad = settings["motors"]["b"]["steps_per_rev"] / (2 * math.pi)
    z_mm_per_step = settings["motors"]["z"]["steps_per_rev"] / 4

    print("SETTINGS INITIALIZED")

    positions = []

    cleaning_well = settings["machine"]["cleaner_position"]

    for i in range(0, 8):
        for j in range(0, 12):
            positions.append([-j * 9, i * 9])

    coms.send_code(HOME)
    initial_pos: Vec2d
    initial_a: int
    initial_b: int
    initial_z: int
    while True:
        coms.get_packet()
        if coms.most_recent_rx.code == INITIAL_POSITION:
            returned_pos_steps = coms.most_recent_rx.get_int_argvec()
            initial_a = returned_pos_steps[0]
            initial_b = returned_pos_steps[1]
            initial_z = returned_pos_steps[2]
            a_mot_angle = initial_a / a_steps_per_rad
            b_mot_angle = initial_b / b_steps_per_rad
            initial_pos = solve_5bar_FK(settings, a_mot_angle, b_mot_angle)
            print(f"starting position: {initial_pos}")
            break

    def conv(xy_list_coord):
        relative_pos = Vec2d(xy_list_coord[0], xy_list_coord[1])
        abs_pos = relative_pos + initial_pos
        angles = solve_5bar_IK(settings, abs_pos)
        alpha = math.ceil(angles.alpha * a_steps_per_rad)
        beta = math.ceil(angles.beta * b_steps_per_rad)
        return [alpha, beta]

    z_cleared = math.floor(initial_z - z_mm_per_step * 10)
    coms.send_move_steps(initial_a, initial_b, z_cleared)
    coms.await_confirm()
    coms.send_move_steps(initial_a, initial_b, initial_z)
    coms.await_confirm()

    step_positions = [conv(coord) for coord in positions]
    cleaning_well = conv(cleaning_well)

    input("enter to continue")

    for position in step_positions:
        coms.send_move_steps(position[0], position[1], initial_z)
        coms.await_confirm()
        coms.send_move_steps(cleaning_well[0], cleaning_well[1], initial_z)
        coms.await_confirm()

    coms.send_move_steps(initial_a, initial_b, initial_z)
