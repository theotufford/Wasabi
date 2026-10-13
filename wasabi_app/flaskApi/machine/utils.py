from .kinematics import Vec2d
import typing
from ..db import get_db
import string


def alph_to_xy(alphnum: str):
    print(f"given {alphnum}")
    coord_y: int = 0
    base26_rep = []
    for i in range(0, len(alphnum)):
        alph = alphnum[i]
        if alph.isalpha():
            base26_rep.append(ord(alph) - ord('A') + 1)
        else:
            base26_rep.reverse()
            for d in reversed(range(len(base26_rep))):
                coord_y += base26_rep[d] * (26 ** d)

            # 0 indexing
            coord_x = int(alphnum[i:]) - 1
            coord_y -= 1

            print([coord_x, coord_y])
            return [coord_x, coord_y]


def alph_to_vec(alph):
    x, y = alph_to_xy(alph)
    return Vec2d([x, y])


def vec_to_alph(vec):
    return xy_to_alph(round(vec.x), round(vec.x))


def xy_to_alph(x: int, y: int):
    x += 1
    y += 1
    result = []
    while y > 0:
        y, rem = divmod(y-1, 26)
        result.append(string.ascii_uppercase[rem])

    return f"{"".join(reversed(result))}{x}"


def get_linear_well_array_height(well_array: list):
    x, lowest_seen = alph_to_xy(well_array[0])
    x, highest_seen = alph_to_xy(well_array[-1])
    for well in well_array:
        x, y = alph_to_xy(well)
        if y > highest_seen:
            highest_seen = y
        if y < lowest_seen:
            lowest_seen = y
    return highest_seen - lowest_seen


def get_linear_well_array_width(well_array: list):
    lowest_seen, y = alph_to_xy(well_array[0])
    highest_seen, y = alph_to_xy(well_array[-1])
    for well in well_array:
        x, y = alph_to_xy(well)
        if x > highest_seen:
            highest_seen = x
        if x < lowest_seen:
            lowest_seen = x
    return highest_seen - lowest_seen


def order_from_to_coords(from_input, to_input):
    from_x, from_y = alph_to_xy(from_input)
    to_x, to_y = alph_to_xy(to_input)
    if from_x > to_x:
        from_x, to_x = to_x, from_x
    if from_y > to_y:
        from_y, to_y = to_y, from_y
    return [[from_x, from_y], [to_x, to_y]]


def order_from_to_alphs(from_input, to_input):
    from_x, from_y = alph_to_xy(from_input)
    to_x, to_y = alph_to_xy(to_input)
    if from_x > to_x:
        from_x, to_x = to_x, from_x
    if from_y > to_y:
        from_y, to_y = to_y, from_y
    return [xy_to_alph(from_x, from_y), xy_to_alph(to_x, to_y)]


def corners_to_range(from_input: str, to_input: str):
    [from_x, from_y], [to_x, to_y] = order_from_to_coords(from_input, to_input)

    all_wells = []
    for y in range(from_y, to_y+1):
        for x in range(from_x, to_x+1):
            all_wells.append(xy_to_alph(x, y))

    return all_wells


def get_reagent(id):
    db = get_db()
    reagent = db.execute("""
                      SELECT reagent FROM pumpMap
                      WHERE pumpID = ?
                      LIMIT 1
                      """, (id,)).fetchone()[0]
    return reagent


def get_pump_id(reagent):
    db = get_db()
    pumpid = db.execute("""
                      SELECT pumpID FROM pumpMap
                      WHERE reagent = ?
                      LIMIT 1
                      """, (reagent,)).fetchone()[0]
    return pumpid


class liq_handling_data():
    def __init__(self, volume, reagent: str | None = None, pumpid: int | None = None):
        if self.pumpid is None and self.reagent is None:
            raise ValueError(
                "trying to construct nondescript liq handling data!")
        self.volume = volume
        self.reagent = reagent
        self.pumpid = pumpid
        if self.reagent is None:
            self.reagent = get_reagent(self.pumpid)
        if self.pumpid is None:
            self.pumpid = get_pump_id(self.reagent)
