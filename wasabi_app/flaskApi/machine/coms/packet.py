import struct
import zlib
from . import codex
from typing import Literal


# packet structure is strictly ordered by byte:
# 0: start byte
# 1: coms code
# 2: data type
# 3-4: data length
# 5 to n + 5: data
# n+6 to n+10: checksum

HEADER_SIZE = 5


def make_uint8_t(val: int):
    return val.to_bytes(byteorder="little", length=1)


def make_uint16_t(val: int):
    return val.to_bytes(byteorder="little", length=2)


def get_pico_int(val: int):
    return val.to_bytes(byteorder="little", length=4, signed=True)


def get_pico_float(val: float):
    return struct.pack('<f', val)


def parse_uint16_t(databytes: bytearray):
    return struct.unpack("<H", databytes)[0]


def parse_int(databytes: bytearray):
    return struct.unpack("<i", databytes)[0]


class Packet:
    def __init__(self, code, datatype, datalen, data: bytearray, checksum=0):
        if datalen > 1024:
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
            return ValueError(f"got unconfigured datatype: {datatype}")
        self.data = data
        self.checksum = 0

    def __repr__(self):
        return f"{codex.COMS_INV[self.code]} type packet with {codex.types_by_code[self.datatype_id]} data of value: {self.data}"

    def make_header(self) -> bytearray:
        header = bytearray()
        header += codex.COMS_START_BYTE
        header += make_uint8_t(self.code)
        header += make_uint8_t(self.datatype_id)
        header += make_uint16_t(self.datalen)
        return header

    def calculate_checksum(self) -> bytearray:
        message_bytes = self.make_header()
        message_bytes += self.data
        return get_pico_int(0)

    def get_full_bytes(self) -> bytearray:
        out_bytes = self.make_header()
        out_bytes += self.data
        out_bytes += get_pico_int(0)
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
    coms_code = header[1]
    datatype = codex.types_by_code[header[2]]
    datalen = parse_uint16_t(header[3:5])
    return (coms_code, datatype, datalen)


def make_new_packet(code, datatype, data: bytearray) -> Packet:
    return Packet(code=code, datatype=datatype, datalen=len(data), data=data)


def make_int_vec_packet(code, vec: list[int]) -> Packet:
    output_data = b""
    for entry in vec:
        output_data += get_pico_int(entry)

    return Packet(code, int, len(output_data), output_data)


def make_float_vec_packet(code, vec: list[float]) -> Packet:
    output_data = b""
    for entry in vec:
        output_data += get_pico_float(entry)

    return Packet(code, float, len(output_data), output_data)


def code_packet(code: int):
    return make_new_packet(code, None, b"")


def state_packet(state: Literal[codex.BUSY, codex.LISTENING]):
    state = bytearray(bytes([state]))
    return make_new_packet(codex.STATE, int, state)


def get_settings_packet(settings_dict):
    motors = settings_dict["machine"]["motors"]
    common_settings = motors["common_settings"]
    pinsettings = settings_dict["machine"]["pins"]
    dimensionsettings = settings_dict["machine"]["machineDimensions"]

    kine_spr = common_settings["kinematic_steps_per_revolution"]

    a_lim_stp_pos = dimensionsettings["a_endstop_position_deg"] / 360
    b_lim_stp_pos = dimensionsettings["b_endstop_position_deg"] / 360
    z_lim_stp_pos = dimensionsettings["z_endstop_position_mm"] / dimensionsettings["z_screw_pitch"]

    a_lim_stp_pos = round(a_lim_stp_pos * kine_spr)
    b_lim_stp_pos = round(b_lim_stp_pos * kine_spr)
    z_lim_stp_pos = round(z_lim_stp_pos * kine_spr)
    # send common pico pin settings -------------
    settings = [
        # a motor settings
        motors["a"]["stp_pin"],
        motors["a"]["dir_pin"],
        pinsettings["a_endstop"],
        a_lim_stp_pos,
        motors["a"]["invert_dir"],
        kine_spr,
        # b motor settings
        motors["b"]["stp_pin"],
        motors["b"]["dir_pin"],
        pinsettings["b_endstop"],
        b_lim_stp_pos,
        motors["b"]["invert_dir"],
        kine_spr,
        # z motor settings
        motors["z"]["stp_pin"],
        motors["z"]["dir_pin"],
        pinsettings["z_endstop"],
        z_lim_stp_pos,
        motors["z"]["invert_dir"],
        kine_spr,
    ]
    pump_microsteps = common_settings["pump_steps_per_revolution"]
    # send pump motor settings -----------------
    for pump_conf in motors["pumps"]:
        settings += [
            pump_conf["stp_pin"],
            pump_conf["dir_pin"],
            -1,  # pumps dont have limit switches
            -1,
            pump_conf["invert_dir"],
            pump_microsteps
        ]

    return make_int_vec_packet(codex.WAKE, settings)


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

    def __repr__(self):
        return f"""
    mot: {self.motid}
    profile_id: {self.profile_id}
    movetype: {self.movetype}
    target: {self.step_target}
    vmax: {self.vmax}
    accel: {self.accel}
    """


def move_packet(moves: list[MoveEntity]) -> Packet:
    output_data = b""
    print(f"generating move packet: {moves}")
    for move in moves:
        output_data += move.data
    return Packet(codex.MOVE, bytearray, len(output_data), output_data)
