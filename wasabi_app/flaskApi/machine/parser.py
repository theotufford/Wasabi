# this file creates an abstract interface for our code to easily program
# the robot to do certain methods  without the granularity of programming
# each and every action

from .db import get_db
from .coms import Packet


def verify_has(data, *args):
    for key in args:
        if data.get(key) is None:
            raise ValueError(f"data:{data}\n is missing key:{key}")
    return True


# this function maps a1 -> [0,0]
def corners_to_range(from_input: str, to_input: str):
    fromchar = from_input[0]
    tochar = to_input[0]
    from_x = (ord(fromchar) - ord('A'))
    to_x = (ord(tochar) - ord('A'))
    from_y = int(from_input[1] - 1)
    to_y = int(to_input[1] - 1)

    if from_x > to_x:
        from_x, to_x = to_x, from_x

    if from_y > to_y:
        from_y, to_y = to_y, from_y

    all_wells = []

    for x in range(from_x, to_x):
        for y in range(from_y, to_y):
            all_wells.append([x, y])


class ExperimentMachineCode:
    # all coordinates in output machine code are given in relative well index
    # rather than an absolute coordinate system
    def __init__(self, pump_map: dict):
        self.instructions = []
        self.pumpmap = pump_map

    def move_to_well(self, coord):
        over =
        self.instructions.append(over)

    def dispense(self, reagent, volume):
        id = self.pumpmap.get(reagent)
        if id is None:
            raise ValueError(f"reagent '{reagent}' not found in pumpmap!")

        pass

    def aspirate(self, reagent, volume):
        pass

    def to_csv(self):
        pass


def parse_experiment(data):

    verify_has(data, "forms")

    # get pump map
    db = get_db()
    reagent_to_pump = {}
    dump = db.execute("""
                      SELECT pumpID, reagent
                      FROM pumpMap
                      """).fetchall()
    for row in dump:
        rowdict = dict(row)
        reagent_to_pump[rowdict["reagent"]] = rowdict["pumpID"]

    # TODO get well map
    homing_output = {}

    machine_code = ExperimentMachineCode(
        pump_map=reagent_to_pump, well_map=homing_output

    )

    forms = data["forms"]

    for instruction_form in forms:
        method = instruction_form["method"]
        if method == "constant":
            constant_volume(instruction_form, machine_code)
        if method == "gradient":
            gradient_volume(instruction_form, machine_code)
        if method == "serial_dilution":
            serial_dilution(instruction_form, machine_code)


# METHODS

def constant_volume(input_data: dict, machine_code: ExperimentMachineCode):
    verify_has(input_data, "from", "to", "volume", "reagent")
    well_array = corners_to_range(input_data["from"], input_data["to"])

    for well_index in well_array:
        machine_code.move_to_well(well_index)
        machine_code.dispense(input_data["reagent"], input_data["volume"])


def gradient_volume(input_data: dict, machine_code: ExperimentMachineCode):
    verify_has(input_data, "from", "to", "volume",
               "direction", "initial_volume", "increment", "reagent")

    well_array = corners_to_range(input_data["from"], input_data["to"])

    current_volume = input_data["initial_volume"]
    for well_index in well_array:
        machine_code.move_to_well(well_index)
        machine_code.dispense(input_data["reagent"], input_data["volume"])
        current_volume += input_data["increment"]


def serial_dilution(input_data: dict, machine_code: ExperimentMachineCode):
    pass
