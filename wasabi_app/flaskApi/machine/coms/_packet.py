import struct
import zlib
import codex


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
        header = bytearray(codex.COMS_START_BYTE)
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


def get_settings_packet(settings_dict):
    motors = settings_dict["machine"]["motors"]
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
