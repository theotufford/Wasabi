import math
from typing import Self
from .utils import vec_to_alph, alph_to_vec
from .kinematics import Vec2d, Vec3d,  vec2d_rotate_rads


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


class Plate:
    def __init__(self, settings: dict, top_left_abs: Vec2d = Vec2d([0, 0]), bottom_right_abs: Vec2d | None = None):
        self.settings = settings
        self.rows = settings["rows"]
        self.columns = settings["columns"]
        self.spacing = settings["spacing"]
        self.tl = top_left_abs
        self.br = bottom_right_abs
        self.plate_rotation = 0
        if bottom_right_abs is None:
            self.br = Vec2d([self.rows, self.columns]) * self.spacing
        else:
            corner_angle = math.atan(self.rows/self.columns)
            corner_vector = bottom_right_abs - top_left_abs
            measured_corner_angle = math.atan(corner_vector.y, corner_vector.x)
            self.plate_rotation = measured_corner_angle - corner_angle

        self.wells = []
        for row_y in range(0, self.rows):
            for col_x in range(0, self.columns):
                new_well = Reagent_Mix()
                self.wells.append(new_well)

    def clear_contents(self):
        for well in self.wells:
            well = Reagent_Mix()
        return self.wells

    def get_well_abs_position(self, wellid):
        relative_position_vec = alph_to_vec(wellid) * self.spacing
        abs_position = self.tl + \
            vec2d_rotate_rads(relative_position_vec, self.plate_rotation)
        return abs_position

    def set_plate_position(self, a1: Vec2d, br: Vec2d | None = None):
        a1 = Vec2d([a1.x, a1.y])

        if br is None:
            self.br = Vec2d([self.columns-1, self.rows-1]) * self.spacing + a1
            br = self.br

        br = Vec2d([br.x, br.y])
        self.tl = a1

        relative_corner_angle = math.atan((self.rows-1)/(self.columns - 1))

        corner_vector = br - a1
        measured_corner_angle = math.atan(corner_vector.y / corner_vector.x)
        self.plate_rotation = measured_corner_angle - relative_corner_angle
        print(f"plate rotation: {self.plate_rotation}, measured_angle: {
              measured_corner_angle}, standard_angle: {relative_corner_angle}")

    def set_tl(self, a1):
        self.set_plate_position(a1)

    def set_br(self, br):
        self.set_plate_position(self.tl, br)

    def by_alph(self, alph) -> Reagent_Mix:
        col, row = alph_to_vec(alph).axes
        ind = col + ((row - 1) * self.columns)
        return self.wells[ind]

    def get_well_vol_dict(self):
        out = {}
        for wellobj in self.wells:
            alph = vec_to_alph(wellobj.relative_position)
            out[alph] = wellobj.liquid.contents
        return out

    def __repr__(self):
        return f"{self.rows}x{self.columns}; {self.spacing}mm"
