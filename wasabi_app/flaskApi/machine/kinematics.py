import json
import math

arm_length = 0
hand_length = 0
spacing = 0
tool_offset = 0

with open('../../config.json', "r") as j:
    config = json.loads(j.read())
    machine_conf = config["machine"]
    dimensions = machine_conf["machineDimensions"]
    arm_length = dimensions["arm"]
    hand_length = dimensions["hand"]
    spacing = dimensions["spacing"]
    tool_offset = dimensions["tool_offset"]


class Vec2d:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vec2d(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        return self.__mul__(1/scalar)

    def __add__(self, other):
        if isinstance(other, Vec2d):
            return Vec2d(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if isinstance(other, Vec2d):
            return self + (-1 * other)

    def __repr__(self):
        return f"vec2d: x:{self.x}, y:{self.y}"

    def get_length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalize(self):
        return self / self.get_length()


class MachinePosition:
    def __init__(self, endpt: Vec2d, alpha, beta):
        self.toolhead = endpt
        self.alpha = alpha
        self.beta = beta

    def __repr__(self):
        alpha = math.degrees(self.alpha)
        beta = math.degrees(self.beta)
        return f"{alpha=}, {beta=}"


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


def solve_5bar_IK(target: Vec2d) -> MachinePosition:
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

    # print(f"""
    #       {math.degrees(alpha_1)=}
    #       {math.degrees(alpha_2)=}
    #       {math.degrees(beta_1)=}
    #       {math.degrees(beta_2)=}
    #       """)

    output = MachinePosition(endpt=target, alpha=alpha_final, beta=beta_final)

    return output


def solve_5bar_FK(alpha: float, beta: float):
    alpha = 3 * math.pi / 2 - alpha
    beta = beta - math.pi / 2
    elbow_A = vec_from_angle_length(alpha, arm_length)
    elbow_B = vec_from_angle_length(beta, arm_length) + Vec2d(spacing, 0)
    midpoint = (elbow_A + elbow_B)/2
    elbow_to_elbow = elbow_B - elbow_A
    midpoint_to_joint_length = math.sqrt(
        hand_length ** 2 - (((elbow_to_elbow.get_length())/2) ** 2))
    elbow_to_elbow_unit_vec = elbow_to_elbow.normalize()
    midpoint_to_hand_joint = midpoint_to_joint_length * \
        Vec2d(-elbow_to_elbow_unit_vec.y, abs(elbow_to_elbow_unit_vec.x))

    joint_position = midpoint + midpoint_to_hand_joint

    hand_vector = joint_position - elbow_A
    tool_offset_vector = hand_vector.normalize() * tool_offset

    end_point = joint_position + tool_offset_vector

    print(f"""
    {elbow_A=}
    {elbow_B=}
    {midpoint_to_joint_length=}
    {midpoint=}
    {joint_position=}
          """)

    return end_point


def test():
    print(f"""
    arm length: {arm_length}
    hand length: {hand_length}
    spacing: {spacing}
    tool offset: {tool_offset}
    """)

    while True:
        print("Forward kinematic test")
        inpa = math.radians(float(input("input a:")))
        inpb = math.radians(float(input("input b:")))

        solution = solve_5bar_FK(inpa, inpb)

        print(f"position: {solution}")

        print("inverse kinematic test:")
        inverse = solve_5bar_IK(solution)
        print(f"inverse solver returned: {inverse}")


if __name__ == "__main__":
    test()
