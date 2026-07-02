import json
import math


class Vec2d:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vec2d):
            return Vec2d(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vec2d(self.x * scalar, self.y * scalar)

    def get_length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return self.__mul__(1/scalar)

    def __sub__(self, other):
        if isinstance(other, Vec2d):
            return self + (-1 * other)

    def __repr__(self):
        return f"vec3d: x:{self.x}, y:{self.y}"

    def normalize(self):
        return self / self.get_length()


class MachinePosition:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.alpha = 0
        self.beta = 0

    def __repr__(self):
        alpha = math.degrees(self.alpha)
        beta = math.degrees(self.beta)
        return f"dg: {alpha}, {beta}; pos: {self.x}, {self.y}, {self.z}"

    def toolhead(self) -> Vec2d:
        return Vec2d(self.x, self.y)


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


def solve_5bar_IK(machine_settings: dict, target: Vec2d) -> MachinePosition:

    machine_conf = machine_settings["machine"]
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

    output = MachinePosition()
    output.x = target.x
    output.y = target.y
    output.z = 0
    output.alpha = alpha_final
    output.beta = beta_final

    return output


def solve_5bar_FK(machine_settings: dict, alpha: float, beta: float) -> Vec2d:
    machine_conf = machine_settings["machine"]
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
        hand_length ** 2 - (((wrist_to_wrist.get_length())/2) ** 2))
    wrist_to_wrist_unit_vec = wrist_to_wrist.normalize()
    midpoint_to_hand_joint = midpoint_to_joint_length * \
        Vec2d(-wrist_to_wrist_unit_vec.y, abs(wrist_to_wrist_unit_vec.x))

    joint_position = midpoint + midpoint_to_hand_joint

    hand_vector = joint_position - wrist_A
    tool_offset_vector = hand_vector.normalize() * tool_offset

    end_point = joint_position + tool_offset_vector

    # print(f"""
    # {wrist_A=}
    # {wrist_B=}
    # {midpoint_to_joint_length=}
    # {midpoint=}
    # {joint_position=}
    #       """)

    return end_point
