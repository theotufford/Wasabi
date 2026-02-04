#!./.venv/bin/python
from time import sleep
import serial
import RPi.GPIO as pio
import time
import json
import struct


def get_settings_dict(path):
    config_path = path
    conf_dict = {}

    with open(config_path, "r") as conf:
        conf_dict = json.load(conf)
    return conf_dict


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
    MOVE = 10
    DISPENSE = 11
    ASPIRATE = 12
    TOGGLE_PUMPS = 13
    TOGGLE_MOTORS = 14
    ZERO_MOTORS = 15
    A_POSITION = 16
    B_POSITION = 17
    X_POSITION = 18
    Y_POSITION = 19
    Z_POSITION = 20

    inverted = [
        "WAITING",
        "WAKE",
        "CONFIRM",
        "MESSAGE",
        "ERROR",
        "NEW_PUMP",
        "A_MOTOR",
        "B_MOTOR",
        "Z_MOTOR",
        "MACHINE_PIN_DEFINITIONS",
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
        "Z_POSITION"
    ]


codex = ComsCodexEnum()


def getInt_from_8arr(byte):
    return int.from_bytes(byte, byteorder="little", signed=False)


def intgr_to_8arr(intgr):
    return struct.pack("<i", intgr)


# def pico8arr_tointgr(pico_bArr):
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
        self.message_history_length = 20
        self.send_index = 0
        self.queue_head_index = 0
        self.message_queue = [b"" for i in range(
            0, self.message_history_length)]
        while True:
            self.blocking_read()
            if self.rx_code == codex.WAKE:
                print("wake rxd")
                self.write_and_flush(codex.CONFIRM)
            if self.rx_code == codex.CONFIRM:
                print("coms initialized")
                self.write_and_flush(codex.CONFIRM)
                break
        return

    def await_confirm(self):
        while True:
            self.blocking_read()
            if self.rx_code == codex.CONFIRM:
                break

    def notify_listening(self, listening=True):
        # set state of listening pin
        pass

    def write_out(self, code, data=b""):

        header = bytearray()
        header += codex.COMS_START_BYTE
        header += code.to_bytes(1, byteorder='little')
        header += len(data).to_bytes(1, byteorder='little')
        header += self.queue_head_index.to_bytes(1, byteorder='little')

        message = header + data

        self.message_queue[self.queue_head_index] = message
        self.queue_head_index = (
            self.queue_head_index + 1) % self.message_history_length

    def flush_packets(self):
        while self.send_index != self.queue_head_index:
            # if not self.pico_listening():
            #     continue
            message = self.message_queue[self.send_index]
            code = message[1]
            print(f"""
            ------------ OUTGOING MESSAGE ------------
            code:{codex.inverted[code]}
            lengthbyte: {message[2]}
            message index: {message[3]}
            data: {message[4:]}
            """)
            self.ser.write(message)
            self.send_index = (self.send_index +
                               1) % self.message_history_length
            return True

    def write_and_flush(self, code, data=b""):
        self.write_out(code, data)
        self.flush_packets()

    def send_arg_vec(self, code, intgr_arr):
        print(f"{intgr_arr=}")
        outData = bytearray()
        for intgr in intgr_arr:
            outData += intgr_to_8arr(intgr)
        data_stream.write_out(code, outData)
        data_stream.flush_packets()

    def blocking_read(self):

        # if i can get this working without the control pins that would be good
        # self.notify_listening()

        body_len = 0
        startfound = False
        header = []
        while True:
            if self.ser.in_waiting > 0:
                if startfound:
                    header = self.ser.read(2)
                    break
                if self.ser.read(1) == codex.COMS_START_BYTE:
                    startfound = True

        self.rx_code = header[0]
        body_len = header[1]

        print(f"""
        ------------ INCOMING MESSAGE ------------
        expected len: {body_len}
        code:{codex.inverted[self.rx_code]}
        raw header:{header}
        """)
        body = bytes()
        arg_arr = []
        if body_len == 0:
            print("no body")
            return
        while True:
            if self.ser.in_waiting >= body_len:
                body = self.ser.read(body_len)
                if body_len % 4 == 0:
                    intgr_iter = struct.iter_unpack("<i", body)
                    arg_arr = [intgr[0] for intgr in intgr_iter]
                    print(f"int args: {arg_arr}")
                    break
                if self.rx_code <= codex.ERROR:
                    print(f"body: {body}")
                break
        print(f"raw body: {body}")
        return arg_arr


def get_axmot_argvec(mot_conf):
    # order dependent interpretation by enum
    out = [
        mot_conf["stp_pin"],
        mot_conf["dir_pin"],
        mot_conf["steps_per_rev"],
        mot_conf["angV_max"],
        mot_conf["accel_max"]
    ]
    return out


def get_pump_argvec(mot_conf):
    # notably this does not send the compensation
    # factor because the machine controller works
    # off step count alone
    out = [
        mot_conf["stp_pin"],
        mot_conf["dir_pin"],
        mot_conf["steps_per_rev"],
        mot_conf["accel_max"]
    ]
    return out


try:
    pio.setmode(pio.BCM)
    pio.setup(17, pio.OUT)

    # reboot the pico
    pio.output(17, pio.LOW)
    time.sleep(0.5)
    pio.output(17, pio.HIGH)

    data_stream = ComsChannel()
    outData = bytearray()

    settings = get_settings_dict("./test_data.json")

    for pump_conf in settings["pumps"]:
        pump_settings = get_pump_argvec(pump_conf)
        data_stream.send_arg_vec(codex.NEW_PUMP, pump_settings)
        data_stream.await_confirm()

    a_mot_settings = get_axmot_argvec(settings["a_axis"])
    data_stream.send_arg_vec(codex.A_MOTOR, a_mot_settings)
    data_stream.await_confirm()

    b_mot_settings = get_axmot_argvec(settings["b_axis"])
    data_stream.send_arg_vec(codex.B_MOTOR, b_mot_settings)
    data_stream.await_confirm()

    z_mot_settings = get_axmot_argvec(settings["z_axis"])
    data_stream.send_arg_vec(codex.Z_MOTOR, z_mot_settings)
    data_stream.await_confirm()

    data_stream.write_and_flush(codex.CONFIRM, b"")

    read_ind = 0
    while True:
        print(f"\r read index: {read_ind}", end="")
        data_stream.blocking_read()
        read_ind += 1
finally:
    pio.cleanup()
