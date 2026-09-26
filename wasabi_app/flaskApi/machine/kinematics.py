import json
import math


class Vector:
    def __init__(self, elements: list[float]):
        self.dimension = len(elements)
        self.elements = elements

    def __add__(self, other):
        if isinstance(other, Vector):
            if self.dimension == other.dimension:
                return self.__class__(
                    [self.elements[i] + other.elements[i]
                     for i in range(0, self.dimension)]
                )
        return NotImplemented

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return self.__class__([element * scalar for element in self.elements])
        else:
            return NotImplemented

    def get_length(self):
        axis_sqsum = 0
        for element in self.elements:
            axis_sqsum += element ** 2
        return math.sqrt(axis_sqsum)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return self.__mul__(1/scalar)

    def __sub__(self, other):
        if isinstance(other, Vector):
            return self + (-1 * other)

    def __repr__(self):
        return f"cartesian vector elements: {self.elements}"

    def normalize(self):
        return self / self.get_length()


def dot_product(vec1: Vector, vec2: Vector) -> float:
    if vec1.dimension != vec2.dimension:
        raise ValueError(
            f"trying to take dot product of vectors without common dimension: {vec1}, {vec2}")
    out = 0
    for i in range(0, vec1.dimension):
        out += vec1.elements[i] * vec2.elements[i]

    return out


class Vec2d(Vector):
    def __init__(self, axes):
        self.x = axes[0]
        self.y = axes[1]
        super().__init__(axes)

    def __repr__(self):
        return f"a 2d vector with elements: {self.x=}, {self.y=}"


class Vec2d_Ang(Vector):
    def __init__(self, axes):
        self.a = axes[0]
        self.b = axes[1]
        super().__init__(axes)

    def __repr__(self):
        return f"a 2d vector with elements: {self.x=}, {self.y=}"


def vec2d_rotate_rads(initial_vector, radians) -> Vec2d:
    rotation_matrix_row_1 = Vec2d(math.cos(radians), math.sin(radians))
    rotation_matrix_row_2 = Vec2d(-math.sin(radians), math.cos(radians))
    output_vec = Vec2d(dot_product(initial_vector, rotation_matrix_row_1),
                       dot_product(initial_vector, rotation_matrix_row_2))
    return output_vec


class Vec3d(Vector):
    def __init__(self, axes):
        self.x = axes[0]
        self.y = axes[1]
        self.z = axes[2]
        super().__init__(axes)

    def __repr__(self):
        return f"a 3d vector with elements: {self.x=}, {self.y=}, {self.z=}"


def vec_from_angle_length(angle, length) -> Vec2d:
    unit_x = math.cos(angle)
    unit_y = math.sin(angle)

    return length * Vec2d(unit_x, unit_y)


def inv_law_of_cosines(hypot, opposite, adjacent):
    # print(f"getting theta for {hypot=}, {opposite=}, {adjacent=}")

    cos_of_theta = ((opposite ** 2) - (hypot ** 2) - (adjacent ** 2)) / \
        (- 2 * hypot * adjacent)
    theta = math.acos(cos_of_theta)
    return theta


def solve_5bar_IK(settings: dict, target_x: float, target_y: float) -> Vec2d_Ang:

    target = Vec2d(-target_x, target_y)

    machine_conf = settings["machine"]
    dimensions = machine_conf["machineDimensions"]
    arm_length = dimensions["arm"]
    hand_length = dimensions["hand"]
    spacing = dimensions["spacing"]
    tool_offset = dimensions["tool_offset"]

    end_pt_hypot_long = target.get_length()
    alpha_1 = math.atan2(target.y, target.x)
    alpha_2 = inv_law_of_cosines(
        end_pt_hypot_long, hand_length + tool_offset, arm_length)

    elbow_vec = vec_from_angle_length(alpha_1 + alpha_2, arm_length)

    hand_unit_vec = (target - elbow_vec) * \
        (1. / (hand_length + tool_offset))

    joint = target - (tool_offset * hand_unit_vec)

    # print(f"{joint=}")

    b_mot_to_joint = Vec2d(spacing, 0) - joint

    # beta 1 gets flipped because we are going counter clockwise and atan2
    # registers that technically our b motor to joint line is in the first
    # quadrant the instinct might be to flip b_mot_to_joint.x. however, that
    # would reflect it across the y axis even if beta_final is less than
    # 90 degrees (where the arm is in the fourth quadrant)

    beta_1 = - math.atan2(b_mot_to_joint.y, b_mot_to_joint.x)
    beta_2 = inv_law_of_cosines(
        b_mot_to_joint.get_length(), hand_length, arm_length)

    alpha_final = 3 * math.pi / 2 - alpha_1 - alpha_2

    beta_final = 3 * math.pi / 2 - beta_1 - beta_2

    print(f"solved IK - target_pos: {target}, alpha: {
          (180 / math.pi) * alpha_final}, {(180 / math.pi) * beta_final}")

    return Vec2d_Ang(alpha_final, beta_final)


def solve_5bar_FK(settings: dict, alpha: float, beta: float) -> Vec2d:

    machine_conf = settings["machine"]
    dimensions = machine_conf["machineDimensions"]
    arm_length = dimensions["arm"]
    hand_length = dimensions["hand"]
    spacing = dimensions["spacing"]
    tool_offset = dimensions["tool_offset"]

    alpha = 3 * math.pi / 2 - alpha
    beta = beta - math.pi / 2
    wrist_A = vec_from_angle_length(alpha, arm_length)
    wrist_B = vec_from_angle_length(beta, arm_length) + Vec2d(spacing, 0)
    midpoint = (wrist_A + wrist_B)/2
    wrist_to_wrist = wrist_B - wrist_A
    midpoint_to_joint_length = math.sqrt(
        hand_length ** 2 - ((wrist_to_wrist.get_length()/2) ** 2))
    wrist_to_wrist_unit_vec = wrist_to_wrist.normalize()
    midpoint_to_hand_joint = midpoint_to_joint_length * \
        Vec2d(-wrist_to_wrist_unit_vec.y, abs(wrist_to_wrist_unit_vec.x))

    joint_position = midpoint + midpoint_to_hand_joint

    hand_vector = joint_position - wrist_A
    tool_offset_vector = hand_vector.normalize() * tool_offset

    end_point = joint_position + tool_offset_vector

    return end_point
