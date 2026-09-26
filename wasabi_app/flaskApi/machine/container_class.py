import math
from typing import Self
from utils import Vec2d, vec_to_alph, vec2d_rotate_rads


class Reagent_Mix:
    def __init__(self, contents={}, is_reservoir=False):
        self.contents = contents
        self.is_reservoir = False

    def get_total_volume(self):
        if self.is_reservoir:
            return 1
        total_volume = 0
        for reagent in self.contents:
            held_volume = self.contents[reagent]
            total_volume += held_volume
        return total_volume

    def release_volume(self, target_volume):
        released_volume = Reagent_Mix()
        released_volume.contents = self.contents
        v_total = self.get_total_volume()
        for reagent in self.contents:
            volume = (self.contents[reagent] / v_total) * target_volume
            if not self.is_reservoir:
                self.contents[reagent] -= volume
            released_volume.contents[reagent] = volume

        return released_volume

    def __repr__(self):
        return f"{self.contents}"

    def gain_reagent(self, reagent, volume=0,  reservoir=False):
        if self.is_reservoir:
            return ValueError("attempting to add reagent to mix that is reservoir with indeterminate volume")
        self.empty = False
        self.is_reservoir = reservoir
        if reservoir:
            self.contents[reagent] = 1
            return
        if not self.contents.get(reagent):
            self.contents[reagent] = 0
        self.contents[reagent] += volume

    def gain_mixed_volume(self, liquid: Self):
        if self.is_reservoir:
            return ValueError("attempting to add reagent to mix that is reservoir with indeterminate volume")
        for reagent in liquid.contents:
            volume = liquid.contents[reagent]
            self.gain_reagent(reagent, volume)


class Well:
    def __init__(self, plate_settings, index_vector: Vec2d, contents):
        self.index_vector = index_vector
        self.alph = vec_to_alph(index_vector)
        self.absolute_position: Vec2d()
        self.liquid = Reagent_Mix(contents)
        self.major_diameter = plate_settings["major_diameter"]
        self.minor_diameter = plate_settings["minor_diameter"]
        self.depth = plate_settings["well_depth"]

    def release_aspirate(self, volume) -> Reagent_Mix:
        return self.liquid.release_volume(volume)

    def gain_liquid(self, liquid: Reagent_Mix):
        if liquid is None:
            return
        return self.liquid.gain_mixed_volume(liquid)


class Plate:
    def __init__(self, settings: dict, a1: Vec2d = Vec2d(0, 0), bottom_right_vector: Vec2d | None = None):
        self.settings = settings
        self.rows = settings["rows"]
        self.columns = settings["columns"]
        self.spacing = settings["spacing"]
        self.a1 = a1
        self.br = bottom_right_vector
        self.plate_rotation = 0
        if bottom_right_vector is None:
            self.br = Vec2d(self.rows, self.columns) * self.spacing
        else:
            corner_angle = math.atan(self.rows/self.columns)
            corner_vector = bottom_right_vector - a1
            measured_corner_angle = math.atan(corner_vector.y, corner_vector.x)
            self.plate_rotation = measured_corner_angle - corner_angle

        self.wells = []
        for row_y in range(0, self.rows):
            for col_x in range(0, self.columns):
                new_well = Well(self.settings, self.spacing *
                                                Vec2d(col_x, row_y))
                new_well.absolute_position = self.a1 + vec2d_rotate_rads(
                    new_well.relative_position, self.plate_rotation)
                self.wells.append(new_well)

    def clear_contents(self):
        for well in self.wells:
            well.liquid = Reagent_Mix()
        return self.wells

    def set_plate_position(self, a1: Vec2d, br: Vec2d | None = None):
        self.a1 = a1
        if br is None:
            self.br = Vec2d(self.rows, self.columns) * self.spacing
        br = self.br
        relative_corner_angle = math.atan(self.rows/self.columns)
        corner_vector = br - a1
        measured_corner_angle = math.atan(corner_vector.y / corner_vector.x)
        self.plate_rotation = measured_corner_angle - relative_corner_angle
        print(f"{br=}, {a1=}, {self.plate_rotation=}")
        for wellobject in self.wells:
            wellobject.absolute_position = a1 + vec2d_rotate_rads(
                wellobject.relative_position, self.plate_rotation)

    def by_alph(self, alph):
        for well in self.wells:
            col_row_vec = well.relative_position / self.spacing
            wellid = vec_to_alph(col_row_vec)
            if alph == wellid:
                return well

    def by_position(self, vec: Vec2d):
        for well in self.wells:
            dist_to_center = (
                vec - well.absolute_position).get_vec().get_length()
            if dist_to_center < self.spacing / 2:
                return well

    def get_well_vol_dict(self):
        out = {}
        for wellobj in self.wells:
            alph = vec_to_alph(wellobj.relative_position)
            out[alph] = wellobj.liquid.contents
        return out

    def __repr__(self):
        return f"{self.rows}x{self.columns}; {self.spacing}mm"
