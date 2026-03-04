from __future__ import annotations

import math


class Vec:
    x: float = 0.0
    y: float = 0.0

    def __init__(self, otherVec: Vec | float, Y: float | None = None) -> None:
        # Assume that providing only one argument is the copy constructor intention:
        if None == Y:
            self.x = otherVec.x
            self.y = otherVec.y
        else:
            X = otherVec
            self.x = X
            self.y = Y

    def get_orientation_angle(self) -> float:
        """ Get angle of orientation in degrees """
        return math.degrees(math.atan2(self.y, self.x))

    def as_tuple(self) -> tuple[float, float]:
        """ Get (x,y) """
        return (self.x, self.y)

    def __add__(self, other: Vec) -> Vec:
        """ Add two vectors. """
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec) -> Vec:
        """ Subtract two vectors. """
        return Vec(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec:
        """ Multiply vector by a scalar. """
        return Vec(self.x * scalar, self.y * scalar)

    def dot(self, other: Vec) -> float:
        """ Dot product of two vectors. """
        return self.x * other.x + self.y * other.y

    def magnitude(self) -> float:
        """ Return the magnitude of the vector. """
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> Vec:
        """ Normalize the vector. """
        mag = self.magnitude()
        if mag != 0:
            return Vec(self.x / mag, self.y / mag)
        return Vec(self.x, self.y)

    def rotate(self, angle_degrees: float) -> Vec:
        """ Rotate this vector by 'angle' degrees. """
        radians = math.radians(angle_degrees)
        cos_angle = math.cos(radians)
        sin_angle = math.sin(radians)
        return Vec(
            cos_angle * self.x - sin_angle * self.y,
            sin_angle * self.x + cos_angle * self.y
        )

    def __repr__(self) -> str:
        return f"Vec({self.x}, {self.y})"
