import time
import math
import json
import RPi.GPIO as pio
from .utils import MachinePosition
from serialcoms import ComsChannel


class MachineState:
    def __init__(self):
        self.current_position = MachinePosition()
        self.upper_left_corner = MachinePosition()
        self.lower_right = MachinePosition()
        self.well_map = None
        self.motors_enabled = True
        self.settings = None
