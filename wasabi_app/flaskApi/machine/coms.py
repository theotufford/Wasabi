import serial
import RPi.GPIO as pio
import zlib

# coms codes
TO_WELL = 1
ASPIRATE = 2
DISPENSE = 3
BUZZ = 4
HOME = 5

# data type code
INT_DATA = 0
FLOAT_DATA = 1


class Packet:
    def __init__(self, header_code: int, data: list):
        self.header = header_code
        self.data = data
        data_type = type(data)
        if data_type is int:
            self.data_type_code = INT_DATA
        if data_type is float:
            self.data_type_code = FLOAT_DATA
        # TODO actually implement checksums
        self.checksum = 0xFFFFFFFF


Buzz_packet = Packet(BUZZ, bytearray())
Home_packet = Packet(HOME, bytearray())


def move_to_well_packet(row: int, col: int):
    pack = Packet(TO_WELL, data=[row, col])
    return pack


def packet_from_rx():
    pass
