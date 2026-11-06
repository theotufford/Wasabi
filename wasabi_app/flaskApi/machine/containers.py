import math
from typing import Self
from .utils import xy_to_alph, alph_to_vec, alph_to_xy, is_alphnum_coord
from .kinematics import Vec2d, Vec3d, vec3d_rotate_xy


class Reagent_Mix:
    def __init__(self, contents={}, is_reservoir=False):
        self.contents = contents
        self.is_reservoir = is_reservoir

    def get_total_volume(self):
        total_volume = 0
        for reagent in self.contents:
            held_volume = self.contents[reagent]
            total_volume += held_volume
        return total_volume

    def release_volume(self, target_volume):
        released_volume = Reagent_Mix({}, False)
        v_total = self.get_total_volume()
        for reagent in self.contents.keys():
            volume = (self.contents[reagent] / v_total) * target_volume
            if not self.is_reservoir:
                self.contents[reagent] -= volume
            released_volume.contents[reagent] = volume
        return released_volume

    def __repr__(self):
        return f"{self.contents}"

    def gain_reagent(self, reagent, volume=0):
        if self.is_reservoir:
            return ValueError("attempting to add reagent to mix that is reservoir with indeterminate volume")
        self.empty = False

        if not self.contents.get(reagent):
            self.contents[reagent] = 0

        self.contents[reagent] += volume

    def gain_mixed_volume(self, liquid: Self):
        if self.is_reservoir:
            return ValueError("attempting to add reagent to mix that is reservoir with indeterminate volume")
        for reagent in liquid.contents:
            volume = liquid.contents[reagent]
            self.gain_reagent(reagent, volume)


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
        self.named_containers[name] = Reagent_Mix({}, False)
        self.named_positions[name] = Vec3d(position)

    def set_tl(self, position: Vec3d):
        self.zero_position = position - \
            vec3d_rotate_xy(self.plate.tl_offset, self.rotation)

    def get_named_container(self, name) -> Reagent_Mix:
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
                self.wells[wellid] = Reagent_Mix({}, False)

    def __repr__(self):
        return f" {self.rows * self.columns} well plate with contents: {self.wells}"
