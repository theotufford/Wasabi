import struct
import zlib
from . import pack_codes
from typing import Literal


def make_uint8_t(val: int):
    return val.to_bytes(byteorder="little", length=1)


def make_pico_int(val: int):
    return val.to_bytes(byteorder="little", length=4)


HEADER_SIZE = 5


class Packet:
    def __init__(self, code, datatype, datalen, data: bytearray):
        if datalen > 1024:
            raise ValueError("packet data too large!")
        self.code = code
        self.datalen = datalen
        if datatype == int:
            self.datatype_id = pack_codes.INT
        elif datatype == float:
            self.datatype_id = pack_codes.FLOAT
        elif datatype is bytearray:
            self.datatype_id = pack_codes.STRUCT
        elif datatype is None:
            self.datatype_id = pack_codes.NONE
        else:
            return ValueError(f"got unconfigured datatype: {datatype}")
        self.data = data
        self.checksum = 0

    # packet structure is strictly ordered by byte:
    # 0: start byte
    # 1: coms code
    # 2: data type
    # 3-4: data length
    # 5 to n + 5: data
    # n+6 to n+10: checksum

    def make_header(self) -> bytearray:
        header = bytearray(pack_codes.COMS_START_BYTE)
        header += make_uint8_t(self.code)
        header += make_uint8_t(self.datatype_id)
        header += make_uint8_t(self.datalen)
        return header

    def calculate_checksum(self) -> bytearray:
        message_bytes = self.make_header()
        message_bytes += self.data
        return make_pico_int(zlib.crc32(message_bytes))

    def get_full_bytes(self) -> bytearray:
        out_bytes = self.make_header()
        out_bytes += self.data
        out_bytes += make_pico_int(zlib.crc32(out_bytes))
        return out_bytes

    def get_int_argvec(self) -> list[int]:
        intgr_iter = struct.iter_unpack("<i", self.data)
        argvec = [intgr[0] for intgr in intgr_iter]
        return argvec

    def get_float_argvec(self) -> list[float]:
        flt_iter = struct.iter_unpack("<f", self.data)
        argvec = [flt[0] for flt in flt_iter]
        return argvec


def parse_header(header: bytearray) -> tuple:
    coms_code = int(header[1])
    datatype = pack_codes.types_by_code[int(header[2])]
    datalen = int(header[3])
    return (coms_code, datatype, datalen)


def make_new_packet(code, datatype, data: bytearray) -> Packet:
    return Packet(code=code, datatype=datatype, datalen=len(data), data=data)


def make_int_vec_packet(code, vec: list[int]) -> Packet:
    output_data = b""
    for entry in vec:
        output_data += make_pico_int(entry)


def state_packet(state: Literal[pack_codes.BUSY, pack_codes.LISTENING]):
    state = bytearray(bytes([state]))
    return make_new_packet(pack_codes.STATE, int, state)


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
        common_settings["kinematic_steps_per_revolution"],
        # b motor settings
        motors["b"]["stp_pin"],
        motors["b"]["dir_pin"],
        pinsettings["b_endstop"],
        motors["b"]["invert_dir"],
        common_settings["kinematic_steps_per_revolution"],
        # z motor settings
        motors["z"]["stp_pin"],
        motors["z"]["dir_pin"],
        pinsettings["z_endstop"],
        motors["z"]["invert_dir"],
        common_settings["kinematic_steps_per_revolution"],
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

    return make_int_vec_packet(pack_codes.WAKE, settings)


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
        data = bytearray(
            b"".join([self.motid, self.profile_id, self.movetype]))
        data += bytearray(struct.pack("<i", self.step_target))
        data += bytearray(struct.pack("<f", self.vmax))
        data += bytearray(struct.pack("<f", self.accel))
        return data


def move_packet(moves: list[MoveEntity]) -> Packet:
    output_data = b""
    for move in moves:
        output_data += move.data
    return Packet(pack_codes.MOVE, bytearray, len(output_data), output_data)
