from .kinematics import Vec2d


def alph_to_xy(alph):
    coordchar = alph[0].capitalize()
    coord_x = int(alph[1:]) - 1
    coord_y = ord(coordchar) - ord('A')
    print(f"converted {alph} into {coord_x}, {coord_y}")
    return [coord_x, coord_y]


def alph_to_vec(alph):
    x, y = alph_to_xy(alph)
    return Vec2d(x, y)


def xy_to_alph(x, y):
    alph = chr(y + ord('A'))
    return f"{alph}{x + 1}"


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
