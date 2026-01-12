from time import sleep
import serial
import RPi.GPIO as pio
import time
import json


class ComsCodexEnum:
    # this is a mismatch byte comparison is being buggy
    COMS_START_BYTE = b"\xf8"

    WAITING = 0
    WAKE = 1
    CONFIRM = 2
    MESSAGE = 3
    ERROR = 4
    NEW_PUMP = 5
    A_MOTOR = 6
    B_MOTOR = 7
    Z_MOTOR = 8
    MACHINE_PIN_DEFINITIONS = 9
    MACHINE_DIMENSIONS = 10
    MOVE = 11
    DISPENSE = 12
    ASPIRATE = 13
    TOGGLE_PUMPS = 14
    TOGGLE_MOTORS = 15
    ZERO_MOTORS = 16
    A_POSITION = 17
    B_POSITION = 18
    X_POSITION = 19
    Y_POSITION = 20
    Z_POSITION = 21

    inverted = [
        "waiting",
        "WAKE",
        "CONFIRM",
        "MESSAGE",
        "ERROR",
        "NEW_PUMP",
        "A_MOTOR",
        "B_MOTOR",
        "Z_MOTOR",
        "MACHINE_PIN_DEFINITIONS",
        "MACHINE_DIMENSIONS",
        "MOVE",
        "DISPENSE",
        "ASPIRATE",
        "TOGGLE_PUMPS",
        "TOGGLE_MOTORS",
        "ZERO_MOTORS",
        "A_POSITION",
        "B_POSITION",
        "X_POSITION",
        "Y_POSITION",
        "Z_POSITION",
    ]


codex = ComsCodexEnum()


def getInt_from_8byte(byte):
    return int.from_bytes(byte, byteorder="little", signed=False)


# def pico8arr_tofloat(pico_bArr):
#     return 3.14


class ComsChannel:
    settingsPath = "./testdata.json"

    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=1)
        self.rx_data_array = bytearray()
        self.rx_code = 0
        while True:
            self.read()
            if self.rx_code == codex.WAKE:
                print("wake rxd")
                self.send(codex.CONFIRM)
            if self.rx_code == codex.CONFIRM:
                print("coms initialized")
                self.send(codex.CONFIRM)
                break
        return

    def send(self, code, data=b""):
        header = bytearray([codex.COMS_START_BYTE[0], code, len(data)])
        message = header + data
        print(f"sending {message}")
        self.ser.write(message)

    def read(self):
        header = bytearray()
        while True:
            if self.ser.in_waiting >= 3:
                header = self.ser.read(3)
                break
        self.rx_code = header[1]
        message_len = header[2]
        message = bytearray()
        print(f"rxd\t{codex.inverted[self.rx_code]}", end="")
        if message_len == 0:
            print(" ")
            return
        while True:
            if self.ser.in_waiting >= message_len:
                message = self.ser.read(message_len)
                break
        print(": ", message)


try:
    pio.setmode(pio.BCM)
    pio.setup(17, pio.OUT)
    pio.output(17, pio.LOW)
    time.sleep(0.50)
    pio.output(17, pio.HIGH)
    picoStream = ComsChannel()
    pio.cleanup()
except KeyboardInterrupt:
    pio.cleanup()

