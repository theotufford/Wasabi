import struct
import zlib
import codex
from typing import Literal


class Packet:
    def __init__(self, code, datatype, datalen, data: bytearray):
        if datalen > 255:
            raise ValueError("packet data too large!")
        self.code = code
        self.datalen = datalen
        if datatype == int:
            self.datatype_id = codex.INT
        elif datatype == float:
            self.datatype_id = codex.FLOAT
        elif datatype is bytearray:
            self.datatype_id = codex.STRUCT
        elif datatype is None:
            self.datatype_id = codex.NONE
        else:
            return NotImplemented
        self.data = data
        self.checksum = 0

    # packet structure is strictly ordered by byte:
    # 0: start byte
    # 1: coms code
    # 2: data type
    # 3: data length
    # 4 to n + 4: data
    # n+5 to n+9: checksum

    def make_header(self) -> bytearray:
        header = bytearray(codex.COMS_START_BYTE)
        header += self.code.to_bytes(1)
        header += self.datatype_id.to_bytes(1)
        header += self.datalen.to_bytes(1)
        return header

    def calculate_checksum(self) -> bytearray:
        message_bytes = self.make_header()
        message_bytes += self.data
        return zlib.crc32(message_bytes).to_bytes(4, byteorder='little')

    def get_full_bytes(self) -> bytearray:
        out_bytes = self.make_header()
        out_bytes += self.data
        out_bytes += zlib.crc32(out_bytes).to_bytes(4, byteorder='little')
        return out_bytes

    def get_int_argvec(self) -> list:
        intgr_iter = struct.iter_unpack("<i", self.data)
        argvec = [intgr[0] for intgr in intgr_iter]
        return argvec


def parse_header(header: bytearray) -> tuple:
    coms_code = int(header[1])
    datatype = codex.types_by_code[int(header[2])]
    datalen = int(header[3])
    return (coms_code, datatype, datalen)


def make_new_packet(code, datatype, data: bytearray) -> Packet:
    return Packet(code=code, datatype=datatype, datalen=len(data), data=data)


def state_packet(state: Literal[codex.BUSY, codex.LISTENING]):
    return make_new_packet(codex.STATE, int)


def get_settings_packet(settings_dict):
    motors = settings_dict["machine"]["motors"]
    common_settings = motors["common_settings"]

    # send common pico pin settings -------------
    pinsettings = settings_dict["machine"]["pins"]
    settings = [
        # a motor settings
        motors["a"]["stp_pin"],
        motors["a"]["dir_pin"],
        pinsettings["a_endstop"],
        motors["a"]["invert_dir"],
        1600,  # board is hard wired to max microsteps
        # b motor settings
        motors["b"]["stp_pin"],
        motors["b"]["dir_pin"],
        pinsettings["b_endstop"],
        motors["b"]["invert_dir"],
        1600,
        # z motor settings
        motors["z"]["stp_pin"],
        motors["z"]["dir_pin"],
        pinsettings["z_endstop"],
        motors["z"]["invert_dir"],
        1600,
    ]
    pump_microsteps = common_settings["pump_steps_per_revoulution"]

    # send pump motor settings -----------------
    for pump_conf in motors["pumps"]:
        settings += [
            pump_conf["stp_pin"],
            pump_conf["dir_pin"],
            -1,  # pumps dont have limit switches
            pump_conf["invert_dir"],
            pump_microsteps
        ]
    return settings


class MoveEntity:
    def __init__(self,
                 motid: int,
                 profile_id: int,
                 movetype: int,
                 step_target: int,
                 vmax: float,
                 accel: float):
        self.motid = bytes([motid])
        self.profile_id = bytes([profile_id])
        self.movetype = bytes([movetype])
        self.step_target = step_target
        self.vmax = vmax
        self.accel = accel

    @property
    def data(self):
        data = bytearray([self.motid, self.profile_id, self.movetype])
        data += bytearray(struct.pack("<i", self.step_target))
        data += bytearray(struct.pack("<f", self.vmax))
        data += bytearray(struct.pack("<f", self.accel))


def move_packet(moves: list[MoveEntity]) -> Packet:
    output_data = b""
    for move in moves:
        output_data += move.data
    return Packet(codex.MOVE, codex.STRUCT, len(output_data), output_data)
