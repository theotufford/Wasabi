import math
from typing import Self
from .utils import xy_to_alph, alph_to_vec, alph_to_xy, is_alphnum_coord
from .kinematics import Vec2d, Vec3d, vec3d_rotate_xy


class Reagent_Mix:
    def __init__(self, contents=dict(), is_reservoir=False):
        self.contents = contents
        self.is_reservoir = is_reservoir

    @property
    def total_volume(self):
        acc = 0
        for volume in self.contents.values():
            acc += volume
        return acc

    def gain(self, mix: Self) -> None:
        for reagent, volume in mix.contents.items():
            if not self.contents.get(reagent):
                self.contents[reagent] = 0
            self.contents[reagent] += volume

    def release(self, volume: float) -> Self:
        output_contents = {}
        scale_factor = volume / self.total_volume
        for reagent, vol in self.contents.items():
            volume_released = vol * scale_factor
            if not self.is_reservoir:
                self.contents[reagent] -= volume_released
            output_contents[reagent] = volume_released

        return Reagent_Mix(contents=output_contents, is_reservoir=False)

    def __repr__(self):
        return f"{self.contents}"


class Fixture:
    def __init__(self, settings_dict, plate_settings_dict: dict | None = None):
        self.named_containers: dict[Reagent_Mix] = {}
        self.named_positions: dict[Vec3d] = {}
        self.names = set()
        self.plateless = False
        if plate_settings_dict is not None:
            self.plate = Plate(plate_settings_dict)
        else:
            self.plateless = True
        self.rotation = 0
        self.zero_position = Vec3d(settings_dict["zero_position"])
        for name, position in settings_dict["named_containers"].items():
            self.add_named(name, position)

    def add_named(self, name, position):
        self.names.add(name)
        self.named_containers[name] = Reagent_Mix(
            {f"unknown contents of {name}": 1}, True)
        self.named_positions[name] = Vec3d(position)

    def set_tl(self, position: Vec3d):
        self.zero_position = position - \
            vec3d_rotate_xy(self.plate.tl_offset, self.rotation)

    def get_named_container(self, name) -> Reagent_Mix:
        print(f"getting container of name: {name}")
        if name in self.names:
            return self.named_containers[name]
        elif name in self.plate.all_ids:
            return self.plate.wells[name]

    def get_named_position(self, name):
        if name in self.names:
            return self.named_positions[name]
        elif name in self.plate.all_ids:
            relative_position_vec = Vec3d(
                [*alph_to_xy(name), 0]) * self.plate.spacing
            return vec3d_rotate_xy(
                self.plate.tl_offset + relative_position_vec, self.rotation) + self.zero_position


class Plate:
    def __init__(self, settings: dict):
        self.settings = settings
        self.rows = settings["rows"]
        self.columns = settings["columns"]
        self.spacing = settings["spacing"]
        self.tl_offset = Vec3d(settings["top_left_offset"])
        self.all_ids = set()
        self.wells = {}
        self.reset()

    def reset(self):
        self.all_ids = set()
        self.wells = {}
        for row_y in range(0, self.rows):
            for col_x in range(0, self.columns):
                wellid = xy_to_alph(col_x, row_y)
                self.all_ids.add(wellid)
                self.wells[wellid] = Reagent_Mix(dict(), False)

    def __repr__(self):
        return f" {self.rows * self.columns} well plate with contents: {self.wells}"
