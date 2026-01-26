from time import sleep
import serial
import RPi.GPIO as pio
import time
import json
import struct


class ComsCodexEnum:
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


def getInt_from_8arr(byte):
    return int.from_bytes(byte, byteorder="little", signed=False)


def float_to_8arr(flt):
    return struct.pack("<f", flt)


# def pico8arr_tofloat(pico_bArr):
#     return 3.14


class ComsChannel:
    settingsPath = "./testdata.json"

    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", 115200, timeout=1)
        self.rx_data_array = bytearray()
        self.rx_code = 0
        # circular message queue buffer so that messages can
        # be repeated on checksum fail by decrementing the
        # send index
        self.message_queue = []
        self.message_history_length = 5
        self.send_index = 0
        self.queue_head_index = 0
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

    def pico_listening(self):
        # get tx ok pin state
        return True

    def notify_listening(self, listening=True):
        # set state of listening pin
        pass

    def queue_send(self, code, data=b""):
        self.queue_head_index = (
            self.queue_head_index + 1) % self.message_history_length

        header = bytearray([
            codex.COMS_START_BYTE[0],
            code,
            len(data),
            self.queue_head_index
        ])
        message = header + data

        self.message_queue[self.queue_head_index] = message

    def send_if_listening(self):
        while self.send_index != self.queue_head_index:
            if not self.pico_listening():
                continue
            message = self.message_queue[self.send_index]
            code = message[1]
            print(f"""
            ------------ SENDING MESSAGE ------------
            code:{codex.inverted[code]}
            lengthbyte: {message[2]}
            message index:
            data: {message[3:]}
            """)
            self.ser.write(message)
            self.send_index = (self.send_index + 1) % self.message_history_length
            return True

    def blocking_read(self):

        self.notify_listening()

        body_len = 0
        startfound = False
        while True:
            if self.ser.in_waiting > 0:
                if startfound:
                    self.rx_code = getInt_from_8arr(self.ser.read())
                    body_len = getInt_from_8arr(self.ser.read())
                    break
                if self.ser.read(1) == codex.COMS_START_BYTE:
                    startfound = True
            elif not startfound:
                self.request_data()

        print("------------ NEW MESSAGE ------------")
        print(f"expected len: {body_len}", end="\t")

        body = bytes()
        print(f"code:{codex.inverted[self.rx_code]}")
        if body_len == 0:
            print("no body")
            return
        while True:
            print(f"""
            \rwaiting for {body_len} bytes
            \rcurrently:{self.ser.in_waiting}
            """, end="")
            if self.ser.in_waiting >= body_len:
                print("\n")
                body = self.ser.read(body_len)
                if body_len % 4 == 0:
                    floatval = struct.unpack("<f", body)[0]
                    print(f"first float: {floatval}\tbytearray body: {body}")
                    break
                if self.rx_code <= codex.ERROR:
                    print(f"body: {body}")
                break
        self.notify_listening(False)
        return body


try:
    pio.setmode(pio.BCM)
    pio.setup(17, pio.OUT)
    pio.output(17, pio.LOW)
    time.sleep(0.5)
    pio.output(17, pio.HIGH)
    data_stream = ComsChannel()
    while True:
        data_stream.queue_send(codex.MOVE, float_to_8arr(20.123498))
        data_stream.send_if_listening()
        message_body = data_stream.blocking_read()
finally:
    pio.cleanup()
