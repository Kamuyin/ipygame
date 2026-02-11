"""ipygame.math — Vector2 / Vector3 classes."""

from __future__ import annotations

import math as _math
from typing import Sequence


class Vector2:
    """2D vector compatible with ``pygame.math.Vector2``."""

    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=None):
        if isinstance(x, (Vector2, tuple, list)):
            self.x = float(x[0])
            self.y = float(x[1])
        elif y is None:
            self.x = float(x)
            self.y = float(x)
        else:
            self.x = float(x)
            self.y = float(y)

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index):
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError(index)

    def __setitem__(self, index, value):
        if index == 0:
            self.x = float(value)
        elif index == 1:
            self.y = float(value)
        else:
            raise IndexError(index)

    def __iter__(self):
        yield self.x
        yield self.y

    def __add__(self, other):
        ox, oy = _unpack2(other)
        return Vector2(self.x + ox, self.y + oy)

    __radd__ = __add__

    def __iadd__(self, other):
        ox, oy = _unpack2(other)
        self.x += ox
        self.y += oy
        return self

    def __sub__(self, other):
        ox, oy = _unpack2(other)
        return Vector2(self.x - ox, self.y - oy)

    def __rsub__(self, other):
        ox, oy = _unpack2(other)
        return Vector2(ox - self.x, oy - self.y)

    def __isub__(self, other):
        ox, oy = _unpack2(other)
        self.x -= ox
        self.y -= oy
        return self

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector2(self.x * scalar, self.y * scalar)
        ox, oy = _unpack2(scalar)
        return Vector2(self.x * ox, self.y * oy)

    __rmul__ = __mul__

    def __imul__(self, scalar):
        if isinstance(scalar, (int, float)):
            self.x *= scalar
            self.y *= scalar
        else:
            ox, oy = _unpack2(scalar)
            self.x *= ox
            self.y *= oy
        return self

    def __truediv__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector2(self.x / scalar, self.y / scalar)
        ox, oy = _unpack2(scalar)
        return Vector2(self.x / ox, self.y / oy)

    def __itruediv__(self, scalar):
        if isinstance(scalar, (int, float)):
            self.x /= scalar
            self.y /= scalar
        else:
            ox, oy = _unpack2(scalar)
            self.x /= ox
            self.y /= oy
        return self

    def __floordiv__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector2(self.x // scalar, self.y // scalar)
        ox, oy = _unpack2(scalar)
        return Vector2(self.x // ox, self.y // oy)

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __pos__(self):
        return Vector2(self.x, self.y)

    def __eq__(self, other):
        try:
            ox, oy = _unpack2(other)
        except (TypeError, ValueError):
            return NotImplemented
        return self.x == ox and self.y == oy

    def __ne__(self, other):
        eq = self.__eq__(other)
        return eq if eq is NotImplemented else not eq

    def __bool__(self):
        return self.x != 0 or self.y != 0

    def __repr__(self):
        return f"<Vector2({self.x}, {self.y})>"

    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)

    def length(self) -> float:
        return _math.hypot(self.x, self.y)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def magnitude(self) -> float:
        return self.length()

    def normalize(self) -> "Vector2":
        m = self.length()
        if m == 0:
            raise ValueError("Cannot normalize a zero-length vector")
        return Vector2(self.x / m, self.y / m)

    def normalize_ip(self) -> None:
        m = self.length()
        if m == 0:
            raise ValueError("Cannot normalize a zero-length vector")
        self.x /= m
        self.y /= m

    def is_normalized(self) -> bool:
        return abs(self.length_squared() - 1.0) < 1e-6

    def dot(self, other) -> float:
        ox, oy = _unpack2(other)
        return self.x * ox + self.y * oy

    def cross(self, other) -> float:
        ox, oy = _unpack2(other)
        return self.x * oy - self.y * ox

    def distance_to(self, other) -> float:
        ox, oy = _unpack2(other)
        return _math.hypot(self.x - ox, self.y - oy)

    def distance_squared_to(self, other) -> float:
        ox, oy = _unpack2(other)
        dx = self.x - ox
        dy = self.y - oy
        return dx * dx + dy * dy

    def angle_to(self, other) -> float:
        """Angle in degrees from self to other."""
        ox, oy = _unpack2(other)
        return _math.degrees(
            _math.atan2(ox * self.y - oy * self.x,
                        ox * self.x + oy * self.y)
        )

    def as_polar(self) -> tuple[float, float]:
        r = self.length()
        theta = _math.degrees(_math.atan2(self.y, self.x))
        return (r, theta)

    def from_polar(self, polar: tuple[float, float]) -> None:
        r, theta = polar
        rad = _math.radians(theta)
        self.x = r * _math.cos(rad)
        self.y = r * _math.sin(rad)

    def rotate(self, angle: float) -> "Vector2":
        """Return rotated copy (angle in degrees)."""
        rad = _math.radians(angle)
        c = _math.cos(rad)
        s = _math.sin(rad)
        return Vector2(self.x * c - self.y * s, self.x * s + self.y * c)

    def rotate_ip(self, angle: float) -> None:
        rad = _math.radians(angle)
        c = _math.cos(rad)
        s = _math.sin(rad)
        self.x, self.y = self.x * c - self.y * s, self.x * s + self.y * c

    def rotate_rad(self, angle: float) -> "Vector2":
        c = _math.cos(angle)
        s = _math.sin(angle)
        return Vector2(self.x * c - self.y * s, self.x * s + self.y * c)

    def rotate_rad_ip(self, angle: float) -> None:
        c = _math.cos(angle)
        s = _math.sin(angle)
        self.x, self.y = self.x * c - self.y * s, self.x * s + self.y * c

    def reflect(self, normal) -> "Vector2":
        nx, ny = _unpack2(normal)
        d = 2 * (self.x * nx + self.y * ny)
        return Vector2(self.x - d * nx, self.y - d * ny)

    def reflect_ip(self, normal) -> None:
        nx, ny = _unpack2(normal)
        d = 2 * (self.x * nx + self.y * ny)
        self.x -= d * nx
        self.y -= d * ny

    def lerp(self, other, t: float) -> "Vector2":
        ox, oy = _unpack2(other)
        return Vector2(self.x + (ox - self.x) * t, self.y + (oy - self.y) * t)

    def slerp(self, other, t: float) -> "Vector2":
        ox, oy = _unpack2(other)
        start_length = self.length()
        end_length = _math.hypot(ox, oy)
        if start_length < 1e-6 or end_length < 1e-6:
            raise ValueError("Cannot slerp with zero-length vector")
        angle = _math.acos(
            max(-1, min(1, (self.x * ox + self.y * oy) / (start_length * end_length)))
        )
        if abs(angle) < 1e-6:
            return self.lerp(other, t)
        sin_angle = _math.sin(angle)
        a = _math.sin((1 - t) * angle) / sin_angle
        b = _math.sin(t * angle) / sin_angle
        return Vector2(a * self.x + b * ox, a * self.y + b * oy)

    def move_towards(self, target, max_distance: float) -> "Vector2":
        ox, oy = _unpack2(target)
        dx = ox - self.x
        dy = oy - self.y
        dist = _math.hypot(dx, dy)
        if dist <= max_distance or dist < 1e-6:
            return Vector2(ox, oy)
        ratio = max_distance / dist
        return Vector2(self.x + dx * ratio, self.y + dy * ratio)

    def move_towards_ip(self, target, max_distance: float) -> None:
        v = self.move_towards(target, max_distance)
        self.x, self.y = v.x, v.y

    def clamp_magnitude(self, max_length: float, min_length: float = 0) -> "Vector2":
        m = self.length()
        if m < 1e-6:
            return Vector2(0, 0)
        if m < min_length:
            return self * (min_length / m)
        if m > max_length:
            return self * (max_length / m)
        return self.copy()

    def clamp_magnitude_ip(self, max_length: float, min_length: float = 0) -> None:
        v = self.clamp_magnitude(max_length, min_length)
        self.x, self.y = v.x, v.y

    def update(self, *args) -> None:
        if len(args) == 1:
            ox, oy = _unpack2(args[0])
        elif len(args) == 2:
            ox, oy = float(args[0]), float(args[1])
        else:
            raise TypeError(f"update takes 1 or 2 arguments, got {len(args)}")
        self.x = ox
        self.y = oy

    def epsilon_compare(self, other, epsilon: float) -> bool:
        ox, oy = _unpack2(other)
        return abs(self.x - ox) < epsilon and abs(self.y - oy) < epsilon


def _unpack2(obj):
    if isinstance(obj, Vector2):
        return obj.x, obj.y
    if isinstance(obj, (tuple, list)):
        return float(obj[0]), float(obj[1])
    raise TypeError(f"Expected a vector-like, got {type(obj)}")


class Vector3:
    """Minimal Vector3 stub — not fully implemented."""

    __slots__ = ("x", "y", "z")

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if isinstance(x, (tuple, list)):
            self.x, self.y, self.z = float(x[0]), float(x[1]), float(x[2])
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)

    def __repr__(self):
        return f"<Vector3({self.x}, {self.y}, {self.z})>"

    def __len__(self):
        return 3

    def __getitem__(self, i):
        return (self.x, self.y, self.z)[i]
