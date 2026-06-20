#!./.venv/bin/python
from serial import Serial
import RPi.GPIO as pio
import zlib
import time
import json
import struct


def get_settings_dict(path):
    config_path = path
    conf_dict = {}

    with open(config_path, "r") as conf:
        conf_dict = json.load(conf)
    return conf_dict


TIMEOUT_S = 2

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
MOVE_ABSOLUTE = 11
MOVE_RELATIVE = 12
DISPENSE = 13
ASPIRATE = 14
TOGGLE_PUMPS = 15
TOGGLE_MOTORS = 16
HOME = 17
POSITION = 18
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
    "MOVE_ABSOLUTE",
    "MOVE_RELATIVE",
    "DISPENSE",
    "ASPIRATE",
    "TOGGLE_PUMPS",
    "TOGGLE_MOTORS",
    "HOME",
    "POSITION",
    "BUZZ"
]


def getInt_from_8arr(byte):
    return int.from_bytes(byte, byteorder="little", signed=False)


def intgr_to_8arr(intgr):
    return struct.pack("<i", intgr)


# abstracts the encode - decode process

class Packet:
    def __init__(self, code, datalen, data: bytearray):
        if datalen > 256:
            raise ValueError("packet data too large!")
        self.code = code
        self.datalen = datalen
        self.data = data
        self.checksum = None

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
    # 3 - 3 + n: data
    # n+4 - n+8: checksum

    def calculate_checksum(self) -> bytearray:
        message_bytes = self.make_header()
        message_bytes += self.data
        return zlib.crc32(message_bytes).to_bytes(4, byteorder='little')

    def make_header(self) -> bytearray:
        header = bytearray([COMS_START_BYTE])
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


def make_new_packet(code, data: bytearray) -> Packet:
    return Packet(code=code, datalen=len(data), data=data)


def parse_header(header: bytearray) -> Packet:
    coms_code = int(header[1])
    datalen = int(header[2])
    new_packet = Packet(coms_code, datalen, b"")
    return new_packet


class ComsChannel:

    def connect(self):
        # reset serial if its already open
        if self.ser is not None:
            self.ser.close()

        # reboot the pico
        run_pin = 17
        pio.setmode(pio.BCM)
        pio.setup(run_pin, pio.OUT)
        pio.output(run_pin, pio.LOW)
        time.sleep(0.1)
        pio.output(run_pin, pio.HIGH)
        time.sleep(0.1)

        # initialize serial contact
        self.ser = Serial("/dev/ttyS0", 115200, timeout=TIMEOUT_S)

        # do startup handshake
        while True:
            self.handle_rx_message()
            code = self.most_recent_rx.code
            if code == WAKE:
                print("wake rxd")
                self.send_code(CONFIRM)
                continue
            if code == CONFIRM:
                print("coms initialized")
                self.send_code(CONFIRM)
                break
            raise ValueError(
                f"was expecting wake or confirm during boot, got: {code}")

    def __init__(self):
        self.errcount = 0
        self.most_recent_rx
        self.most_recent_tx
        self.ser = None
        self.connect()

    def __del__(self):
        self.ser.close()

    def await_confirm(self):
        start = time.perf_counter()
        while True:
            self.handle_rx_message()
            code = self.most_recent_rx.code
            if code == CONFIRM:
                break
            current = time.perf_counter()
            if current - start > TIMEOUT_S:
                raise TimeoutError(
                    f"waited {TIMEOUT_S} seconds without recieving a confirm")

    def send_packet(self, message: Packet) -> None:
        self.most_recent_tx = message
        self.ser.write(message.get_full_bytes())

    def send_data(self, code, data) -> None:
        tmp = make_new_packet(code, data)
        self.send_packet(tmp)

    def send_code(self, code) -> None:
        self.send_data(code, b"")

    def send_int_vec(self, code, intgr_arr: list[int]) -> None:
        print(f"{intgr_arr=}")
        outData = bytearray()
        for intgr in intgr_arr:
            outData += intgr_to_8arr(intgr)
        self.send_data(code, outData)

    def check_and_handle_CRC32(self, callback: callable):
        calculated = self.most_recent_rx.calculate_checksum()
        if self.most_recent_rx.checksum != calculated:
            print(f"CRC error detected!! error counter is now {
                  self.errcount}, erroring packet:\n{self.most_recent_rx}")
            self.send_code(RE_REQUEST)
            callback()

    def await_header(self, timeout):
        start = time.perf_counter()
        while True:
            if self.ser.in_waiting > 0:
                if self.ser.read(1) == COMS_START_BYTE:
                    break
                else:
                    self.send_code(RE_REQUEST)
                    return self.await_header(timeout)
            current = time.perf_counter()
            if current - start > timeout:
                return None
        header_data = bytearray([COMS_START_BYTE])
        header_data += self.ser.read(2)
        self.most_recent_rx = parse_header(header_data)
        return self.most_recent_rx

    def check_and_handle_re_req(self):
        found_message = self.await_header(0)
        if found_message is None:
            return False
        if found_message.code == RE_REQUEST:
            found_message.checksum = self.ser.read(4)
            self.most_recent_rx = found_message
            self.check_and_handle_CRC32(self.check_and_handle_re_req)
            self.send_packet(self.most_recent_tx)
            return True
        self.handle_rx_message()

    def handle_rx_message(self, header_already_found=False):
        recieved = None
        if not header_already_found:
            recieved = self.await_header(TIMEOUT_S)
        else:
            recieved = self.most_recent_rx
        if recieved is None:
            raise TimeoutError(f"waited {TIMEOUT_S} seconds for message")

        len = recieved.datalen

        if len > 0:
            start = time.perf_counter()
            while True:
                if self.ser.in_waiting >= len:
                    recieved.data = self.ser.read(len)
                    break
                current = time.perf_counter()
                if current - start > TIMEOUT_S:
                    raise TimeoutError(
                        f"""waited {TIMEOUT_S} seconds without recieving full body
                        expected: {len} have: {self.ser.in_waiting}
                        """)
        start = time.perf_counter()
        while self.ser.in_waiting <= 4:
            current = time.perf_counter()
            if current - start > TIMEOUT_S:
                raise TimeoutError("timed out waiting for checksum")

        recieved.checksum = self.ser.read(4)
        self.most_recent_rx = recieved
        self.check_and_handle_CRC32(self.handle_rx_message)

        return

    def send_settings(self):
        # init settings
        settings = None
        with open("./machine_config.json") as j:
            settings = json.dump(j.read())

        motors = settings["motors"]

        # send kinematic motor settings ------------

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

        for pump_conf in settings["pumps"]:
            pump_settings = get_mot_argvec(pump_conf)
            self.send_int_vec(NEW_PUMP, pump_settings)
            self.await_confirm()

        # send other pin settings ------------------
        # TODO

        self.send_code(CONFIRM)
        self.await_confirm()

    def send_buzz(self, motor_id: int):
        self.send_data(NEW_PUMP, bytearray(motor_id.to_bytes(1)))

    def send_home(self):
        self.send_code(HOME)

    def send_abs_move_steps(self, a_target: int, b_target: int, z_target: int):
        self.send_int_vec(MOVE_ABSOLUTE, [a_target, b_target, z_target])

    def send_rel_move_steps(self, a_target: int, b_target: int, z_target: int):
        self.send_int_vec(MOVE_RELATIVE, [a_target, b_target, z_target])


def get_mot_argvec(mot_conf):
    # order dependent parsing of motor config because coms rx relies on order
    out = [
        mot_conf["stp_pin"],
        mot_conf["dir_pin"],
        mot_conf["steps_per_rev"],
        mot_conf["ang_v_max"],
        mot_conf["ang_accel_rad"],
    ]
    return out
