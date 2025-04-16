"""Some simple utilities to calculate movement and distance in space
"""
from __future__ import annotations

from dataclasses import dataclass
import math as m
import serializer


@dataclass
class TwoD:
    x: float = 0.0
    y: float = 0.0

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Oops TwoD points have only two indices")

    def __setitem__(self, index: int, value: float):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        else:
            raise IndexError("Oops TwoD point have only two indices")

    def __len__(self) -> int:
        return 2


class Point2D(TwoD):
    def __sub__(self, other: Point2D | Vector2D) -> Point2D | Vector2D:
        if isinstance(other, Point2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        elif isinstance(other, Vector2D):
            return Point2D(self.x - other.x, self.y - other.y)
        else:
            raise TypeError(
                "Subtraction on Point2Ds is defined for Point2Ds and Vector2Ds"
            )

    def __add__(self, other: Vector2D) -> Point2D:
        if isinstance(other, Vector2D):
            return Point2D(self.x + other.x, self.y + other.y)
        else:
            raise TypeError("Only Vector2D can be added to a Point2D")

    def __repr__(self) -> str:
        return f"Point2D({self.x}, {self.y})"

    def __eq__(self, other: Point2D) -> bool:
        if self is other:
            return True
        if isinstance(other, Point2D):
            return self.x == other.x and self.y == other.y
        else:
            raise TypeError("Other is {type(other)}, Point2D was expected")


_POINT_JSON_KEY = "__Point2D__"


def _json_serialize_point2d(point: Point2D):
    if not isinstance(point, Point2D):
        raise TypeError(
            f"Oops point is of {type(point)}, we expected a instance of {Point2D}"
        )
    return {_POINT_JSON_KEY: True, "x": point.x, "y": point.y}


def _json_deserialize_point2d(dct):
    if _POINT_JSON_KEY in dct:
        point = Point2D(dct["x"], dct["y"])
        return point
    return dct


# Add support for serializing points
serializer.serializer.register_serializer(Point2D, _json_serialize_point2d)
serializer.deserializer.register_deserializer(
    _POINT_JSON_KEY, _json_deserialize_point2d
)


class Vector2D(TwoD):
    def __add__(self, other: Vector2D):
        if isinstance(other, Vector2D):
            return Vector2D(self.x + other.x, self.y + other.y)
        else:
            raise TypeError(
                f"Only Vector2D can be added to Vector2D, other is: {type(other)}"
            )

    def __sub__(self, other: Vector2D):
        if isinstance(other, Vector2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        else:
            raise TypeError(
                f"Only Vector2D can be subtracted from Vector2D, other is: {type(other)}"
            )

    def __mul__(self, other: Vector2D | float) -> float:
        if isinstance(other, float) or isinstance(other, int):
            return self.scale(other)
        elif isinstance(other, Vector2D):
            return self.dot(other)

    def dot(self, other: Vector2D) -> float:
        return self.x * other.x + self.y * other.y

    def scale(self, scalar: float):
        return Vector2D(self.x * scalar, self.y * scalar)

    def __repr__(self) -> str:
        return f"Vector2D({self.x}, {self.y})"

    @property
    def unit(self):
        return self * (1 / self.magnitude)

    @property
    def magnitude(self) -> float:
        return m.sqrt(self.x**2 + self.y**2)
