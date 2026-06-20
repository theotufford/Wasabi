import math


class Vec2d:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vec2d(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

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


class MachinePosition:
    def __init__(self, endpt: Vec2d, alpha, beta):
        self.end = endpt
        self.alpha = alpha
        self.beta = beta
