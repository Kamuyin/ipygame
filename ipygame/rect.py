"""pygame-compatible Rect and FRect classes."""

from __future__ import annotations

import math
from typing import Iterator, Self, Sequence

__all__ = ["Rect", "FRect"]


def _parse_rect_args(args) -> tuple:
    """Return (x, y, w, h) from the flexible overloads pygame supports."""
    if len(args) == 1:
        a = args[0]
        if isinstance(a, (Rect, FRect)):
            return (a.x, a.y, a.w, a.h)
        if hasattr(a, "__len__"):
            if len(a) == 4:
                return tuple(a)
            if len(a) == 2:
                return (*a[0], *a[1])
        raise TypeError(f"Cannot create Rect from {a!r}")
    if len(args) == 2:
        return (*args[0], *args[1])
    if len(args) == 4:
        return tuple(args)
    if len(args) == 0:
        return (0, 0, 0, 0)
    raise TypeError(f"Rect() takes 0, 1, 2, or 4 arguments ({len(args)} given)")


class Rect:
    """Stores rectangular coordinates (int)."""

    __slots__ = ("_x", "_y", "_w", "_h")

    def __init__(self, *args):
        x, y, w, h = _parse_rect_args(args)
        self._x = int(x)
        self._y = int(y)
        self._w = int(w)
        self._h = int(h)

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, v: int) -> None:
        self._x = int(v)

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, v: int) -> None:
        self._y = int(v)

    @property
    def w(self) -> int:
        return self._w

    @w.setter
    def w(self, v: int) -> None:
        self._w = int(v)

    @property
    def h(self) -> int:
        return self._h

    @h.setter
    def h(self, v: int) -> None:
        self._h = int(v)

    width = w
    height = h

    @property
    def width(self) -> int:
        return self._w

    @width.setter
    def width(self, v: int) -> None:
        self._w = int(v)

    @property
    def height(self) -> int:
        return self._h

    @height.setter
    def height(self, v: int) -> None:
        self._h = int(v)

    @property
    def size(self) -> tuple[int, int]:
        return (self._w, self._h)

    @size.setter
    def size(self, v: tuple[int, int]) -> None:
        self._w, self._h = int(v[0]), int(v[1])

    @property
    def top(self) -> int:
        return self._y

    @top.setter
    def top(self, v: int) -> None:
        self._y = int(v)

    @property
    def left(self) -> int:
        return self._x

    @left.setter
    def left(self, v: int) -> None:
        self._x = int(v)

    @property
    def bottom(self) -> int:
        return self._y + self._h

    @bottom.setter
    def bottom(self, v: int) -> None:
        self._y = int(v) - self._h

    @property
    def right(self) -> int:
        return self._x + self._w

    @right.setter
    def right(self, v: int) -> None:
        self._x = int(v) - self._w

    @property
    def topleft(self) -> tuple[int, int]:
        return (self._x, self._y)

    @topleft.setter
    def topleft(self, v: tuple[int, int]) -> None:
        self._x, self._y = int(v[0]), int(v[1])

    @property
    def topright(self) -> tuple[int, int]:
        return (self._x + self._w, self._y)

    @topright.setter
    def topright(self, v: tuple[int, int]) -> None:
        self._x = int(v[0]) - self._w
        self._y = int(v[1])

    @property
    def bottomleft(self) -> tuple[int, int]:
        return (self._x, self._y + self._h)

    @bottomleft.setter
    def bottomleft(self, v: tuple[int, int]) -> None:
        self._x = int(v[0])
        self._y = int(v[1]) - self._h

    @property
    def bottomright(self) -> tuple[int, int]:
        return (self._x + self._w, self._y + self._h)

    @bottomright.setter
    def bottomright(self, v: tuple[int, int]) -> None:
        self._x = int(v[0]) - self._w
        self._y = int(v[1]) - self._h

    @property
    def centerx(self) -> int:
        return self._x + self._w // 2

    @centerx.setter
    def centerx(self, v: int) -> None:
        self._x = int(v) - self._w // 2

    @property
    def centery(self) -> int:
        return self._y + self._h // 2

    @centery.setter
    def centery(self, v: int) -> None:
        self._y = int(v) - self._h // 2

    @property
    def center(self) -> tuple[int, int]:
        return (self.centerx, self.centery)

    @center.setter
    def center(self, v: tuple[int, int]) -> None:
        self.centerx = v[0]
        self.centery = v[1]

    @property
    def midtop(self) -> tuple[int, int]:
        return (self.centerx, self._y)

    @midtop.setter
    def midtop(self, v: tuple[int, int]) -> None:
        self.centerx = v[0]
        self._y = int(v[1])

    @property
    def midbottom(self) -> tuple[int, int]:
        return (self.centerx, self._y + self._h)

    @midbottom.setter
    def midbottom(self, v: tuple[int, int]) -> None:
        self.centerx = v[0]
        self._y = int(v[1]) - self._h

    @property
    def midleft(self) -> tuple[int, int]:
        return (self._x, self.centery)

    @midleft.setter
    def midleft(self, v: tuple[int, int]) -> None:
        self._x = int(v[0])
        self.centery = v[1]

    @property
    def midright(self) -> tuple[int, int]:
        return (self._x + self._w, self.centery)

    @midright.setter
    def midright(self, v: tuple[int, int]) -> None:
        self._x = int(v[0]) - self._w
        self.centery = v[1]

    def move(self, x: int, y: int) -> Rect:
        return Rect(self._x + int(x), self._y + int(y), self._w, self._h)

    def move_ip(self, x: int, y: int) -> None:
        self._x += int(x)
        self._y += int(y)

    def move_to(self, **kwargs) -> Rect:
        r = self.copy()
        for attr, val in kwargs.items():
            setattr(r, attr, val)
        return r

    def inflate(self, x: int, y: int) -> Rect:
        return Rect(self._x - int(x) // 2, self._y - int(y) // 2,
                     self._w + int(x), self._h + int(y))

    def inflate_ip(self, x: int, y: int) -> None:
        self._x -= int(x) // 2
        self._y -= int(y) // 2
        self._w += int(x)
        self._h += int(y)

    def scale_by(self, sx: float, sy: float | None = None) -> Rect:
        if sy is None:
            sy = sx
        nw = int(self._w * sx)
        nh = int(self._h * sy)
        return Rect(self._x + (self._w - nw) // 2,
                     self._y + (self._h - nh) // 2, nw, nh)

    def scale_by_ip(self, sx: float, sy: float | None = None) -> None:
        r = self.scale_by(sx, sy)
        self._x, self._y, self._w, self._h = r._x, r._y, r._w, r._h

    def update(self, *args) -> None:
        x, y, w, h = _parse_rect_args(args)
        self._x, self._y, self._w, self._h = int(x), int(y), int(w), int(h)

    def normalize(self) -> None:
        if self._w < 0:
            self._x += self._w
            self._w = -self._w
        if self._h < 0:
            self._y += self._h
            self._h = -self._h

    def clamp(self, other) -> Rect:
        o = Rect(other)
        x, y = self._x, self._y
        if self._w >= o._w:
            x = o._x + o._w // 2 - self._w // 2
        elif x < o._x:
            x = o._x
        elif x + self._w > o._x + o._w:
            x = o._x + o._w - self._w
        if self._h >= o._h:
            y = o._y + o._h // 2 - self._h // 2
        elif y < o._y:
            y = o._y
        elif y + self._h > o._y + o._h:
            y = o._y + o._h - self._h
        return Rect(x, y, self._w, self._h)

    def clamp_ip(self, other) -> None:
        r = self.clamp(other)
        self._x, self._y = r._x, r._y

    def clip(self, other) -> Rect:
        o = Rect(other)
        x = max(self._x, o._x)
        y = max(self._y, o._y)
        r = min(self._x + self._w, o._x + o._w)
        b = min(self._y + self._h, o._y + o._h)
        w = max(0, r - x)
        h = max(0, b - y)
        return Rect(x, y, w, h)

    def clipline(self, *args) -> tuple[tuple[int, int], tuple[int, int]] | tuple[()]:
        """Cohen-Sutherland line clipping."""
        if len(args) == 2:
            (x1, y1), (x2, y2) = args
        elif len(args) == 4:
            x1, y1, x2, y2 = args
        elif len(args) == 1 and hasattr(args[0], "__len__") and len(args[0]) == 4:
            x1, y1, x2, y2 = args[0]
        else:
            raise TypeError("clipline requires line coordinates")

        INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8
        xmin, ymin = self._x, self._y
        xmax, ymax = self._x + self._w - 1, self._y + self._h - 1

        def _code(x, y):
            c = INSIDE
            if x < xmin:   c |= LEFT
            elif x > xmax: c |= RIGHT
            if y < ymin:   c |= TOP
            elif y > ymax: c |= BOTTOM
            return c

        c1, c2 = _code(x1, y1), _code(x2, y2)
        while True:
            if not (c1 | c2):
                return ((int(x1), int(y1)), (int(x2), int(y2)))
            if c1 & c2:
                return ()
            c = c1 or c2
            if c & TOP:
                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1) if y2 != y1 else x1
                y = ymin
            elif c & BOTTOM:
                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1) if y2 != y1 else x1
                y = ymax
            elif c & RIGHT:
                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1) if x2 != x1 else y1
                x = xmax
            else:
                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1) if x2 != x1 else y1
                x = xmin
            if c == c1:
                x1, y1, c1 = x, y, _code(x, y)
            else:
                x2, y2, c2 = x, y, _code(x, y)

    def union(self, other) -> Rect:
        o = Rect(other)
        x = min(self._x, o._x)
        y = min(self._y, o._y)
        r = max(self._x + self._w, o._x + o._w)
        b = max(self._y + self._h, o._y + o._h)
        return Rect(x, y, r - x, b - y)

    def union_ip(self, other) -> None:
        r = self.union(other)
        self._x, self._y, self._w, self._h = r._x, r._y, r._w, r._h

    def unionall(self, others: Sequence) -> Rect:
        r = self.copy()
        for o in others:
            r = r.union(o)
        return r

    def unionall_ip(self, others: Sequence) -> None:
        r = self.unionall(others)
        self._x, self._y, self._w, self._h = r._x, r._y, r._w, r._h

    def fit(self, other) -> Rect:
        """Scale and center self to fit inside *other*, preserving aspect ratio."""
        o = Rect(other)
        ratio = max(self._w / o._w if o._w else 1,
                    self._h / o._h if o._h else 1)
        nw = int(self._w / ratio) if ratio else self._w
        nh = int(self._h / ratio) if ratio else self._h
        return Rect(o._x + (o._w - nw) // 2, o._y + (o._h - nh) // 2, nw, nh)

    def contains(self, other) -> bool:
        o = Rect(other)
        return (self._x <= o._x and
                self._y <= o._y and
                self._x + self._w >= o._x + o._w and
                self._y + self._h >= o._y + o._h and
                self._w > 0 and self._h > 0)

    def collidepoint(self, *args) -> bool:
        if len(args) == 1:
            x, y = args[0]
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError("collidepoint requires (x,y)")
        return (self._x <= x < self._x + self._w and
                self._y <= y < self._y + self._h)

    def colliderect(self, other) -> bool:
        o = Rect(other)
        return (self._x < o._x + o._w and
                self._x + self._w > o._x and
                self._y < o._y + o._h and
                self._y + self._h > o._y)

    def collidelist(self, rects: Sequence) -> int:
        for i, r in enumerate(rects):
            if self.colliderect(r):
                return i
        return -1

    def collidelistall(self, rects: Sequence) -> list[int]:
        return [i for i, r in enumerate(rects) if self.colliderect(r)]

    def collidedict(self, d: dict, use_values: bool = True) -> tuple | None:
        for k, v in d.items():
            target = v if use_values else k
            if self.colliderect(target):
                return (k, v)
        return None

    def collidedictall(self, d: dict, use_values: bool = True) -> list[tuple]:
        result = []
        for k, v in d.items():
            target = v if use_values else k
            if self.colliderect(target):
                result.append((k, v))
        return result

    def collideobjects(self, objects, key=None):
        for obj in objects:
            r = key(obj) if key else obj
            if self.colliderect(r):
                return obj
        return None

    def collideobjectsall(self, objects, key=None) -> list:
        result = []
        for obj in objects:
            r = key(obj) if key else obj
            if self.colliderect(r):
                result.append(obj)
        return result

    def copy(self) -> Rect:
        return Rect(self._x, self._y, self._w, self._h)

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index):
        return (self._x, self._y, self._w, self._h)[index]

    def __iter__(self) -> Iterator[int]:
        yield self._x
        yield self._y
        yield self._w
        yield self._h

    def __contains__(self, item) -> bool:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            return self.collidepoint(item)
        return False

    def __bool__(self) -> bool:
        return self._w != 0 and self._h != 0

    def __eq__(self, other: object) -> bool:
        try:
            o = Rect(other)
            return (self._x == o._x and self._y == o._y and
                    self._w == o._w and self._h == o._h)
        except Exception:
            return NotImplemented

    def __hash__(self):
        raise TypeError("unhashable type: 'Rect'")

    def __repr__(self) -> str:
        return f"Rect({self._x}, {self._y}, {self._w}, {self._h})"


class FRect:
    """Stores rectangular coordinates (float)."""

    __slots__ = ("_x", "_y", "_w", "_h")

    def __init__(self, *args):
        x, y, w, h = _parse_rect_args(args)
        self._x = float(x)
        self._y = float(y)
        self._w = float(w)
        self._h = float(h)

    @property
    def x(self) -> float:
        return self._x
    @x.setter
    def x(self, v) -> None:
        self._x = float(v)

    @property
    def y(self) -> float:
        return self._y
    @y.setter
    def y(self, v) -> None:
        self._y = float(v)

    @property
    def w(self) -> float:
        return self._w
    @w.setter
    def w(self, v) -> None:
        self._w = float(v)

    @property
    def h(self) -> float:
        return self._h
    @h.setter
    def h(self, v) -> None:
        self._h = float(v)

    @property
    def width(self) -> float:
        return self._w
    @width.setter
    def width(self, v) -> None:
        self._w = float(v)

    @property
    def height(self) -> float:
        return self._h
    @height.setter
    def height(self, v) -> None:
        self._h = float(v)

    @property
    def size(self) -> tuple[float, float]:
        return (self._w, self._h)
    @size.setter
    def size(self, v) -> None:
        self._w, self._h = float(v[0]), float(v[1])

    @property
    def top(self) -> float:
        return self._y
    @top.setter
    def top(self, v) -> None:
        self._y = float(v)

    @property
    def left(self) -> float:
        return self._x
    @left.setter
    def left(self, v) -> None:
        self._x = float(v)

    @property
    def bottom(self) -> float:
        return self._y + self._h
    @bottom.setter
    def bottom(self, v) -> None:
        self._y = float(v) - self._h

    @property
    def right(self) -> float:
        return self._x + self._w
    @right.setter
    def right(self, v) -> None:
        self._x = float(v) - self._w

    @property
    def topleft(self) -> tuple[float, float]:
        return (self._x, self._y)
    @topleft.setter
    def topleft(self, v) -> None:
        self._x, self._y = float(v[0]), float(v[1])

    @property
    def topright(self) -> tuple[float, float]:
        return (self._x + self._w, self._y)
    @topright.setter
    def topright(self, v) -> None:
        self._x = float(v[0]) - self._w; self._y = float(v[1])

    @property
    def bottomleft(self) -> tuple[float, float]:
        return (self._x, self._y + self._h)
    @bottomleft.setter
    def bottomleft(self, v) -> None:
        self._x = float(v[0]); self._y = float(v[1]) - self._h

    @property
    def bottomright(self) -> tuple[float, float]:
        return (self._x + self._w, self._y + self._h)
    @bottomright.setter
    def bottomright(self, v) -> None:
        self._x = float(v[0]) - self._w; self._y = float(v[1]) - self._h

    @property
    def centerx(self) -> float:
        return self._x + self._w / 2.0
    @centerx.setter
    def centerx(self, v) -> None:
        self._x = float(v) - self._w / 2.0

    @property
    def centery(self) -> float:
        return self._y + self._h / 2.0
    @centery.setter
    def centery(self, v) -> None:
        self._y = float(v) - self._h / 2.0

    @property
    def center(self) -> tuple[float, float]:
        return (self.centerx, self.centery)
    @center.setter
    def center(self, v) -> None:
        self.centerx = v[0]; self.centery = v[1]

    @property
    def midtop(self) -> tuple[float, float]:
        return (self.centerx, self._y)
    @midtop.setter
    def midtop(self, v) -> None:
        self.centerx = v[0]; self._y = float(v[1])

    @property
    def midbottom(self) -> tuple[float, float]:
        return (self.centerx, self._y + self._h)
    @midbottom.setter
    def midbottom(self, v) -> None:
        self.centerx = v[0]; self._y = float(v[1]) - self._h

    @property
    def midleft(self) -> tuple[float, float]:
        return (self._x, self.centery)
    @midleft.setter
    def midleft(self, v) -> None:
        self._x = float(v[0]); self.centery = v[1]

    @property
    def midright(self) -> tuple[float, float]:
        return (self._x + self._w, self.centery)
    @midright.setter
    def midright(self, v) -> None:
        self._x = float(v[0]) - self._w; self.centery = v[1]

    def move(self, x, y) -> FRect:
        return FRect(self._x + x, self._y + y, self._w, self._h)

    def move_ip(self, x, y) -> None:
        self._x += x; self._y += y

    def move_to(self, **kwargs) -> FRect:
        r = self.copy()
        for attr, val in kwargs.items():
            setattr(r, attr, val)
        return r

    def inflate(self, x, y) -> FRect:
        return FRect(self._x - x / 2.0, self._y - y / 2.0,
                      self._w + x, self._h + y)

    def inflate_ip(self, x, y) -> None:
        self._x -= x / 2.0; self._y -= y / 2.0
        self._w += x; self._h += y

    def scale_by(self, sx, sy=None) -> FRect:
        if sy is None:
            sy = sx
        nw = self._w * sx
        nh = self._h * sy
        return FRect(self._x + (self._w - nw) / 2.0,
                      self._y + (self._h - nh) / 2.0, nw, nh)

    def scale_by_ip(self, sx, sy=None) -> None:
        r = self.scale_by(sx, sy)
        self._x, self._y, self._w, self._h = r._x, r._y, r._w, r._h

    def update(self, *args) -> None:
        x, y, w, h = _parse_rect_args(args)
        self._x, self._y = float(x), float(y)
        self._w, self._h = float(w), float(h)

    def normalize(self) -> None:
        if self._w < 0:
            self._x += self._w; self._w = -self._w
        if self._h < 0:
            self._y += self._h; self._h = -self._h

    def clamp(self, other) -> FRect:
        o = FRect(other)
        x, y = self._x, self._y
        if self._w >= o._w:
            x = o._x + o._w / 2 - self._w / 2
        elif x < o._x:
            x = o._x
        elif x + self._w > o._x + o._w:
            x = o._x + o._w - self._w
        if self._h >= o._h:
            y = o._y + o._h / 2 - self._h / 2
        elif y < o._y:
            y = o._y
        elif y + self._h > o._y + o._h:
            y = o._y + o._h - self._h
        return FRect(x, y, self._w, self._h)

    def clamp_ip(self, other) -> None:
        r = self.clamp(other)
        self._x, self._y = r._x, r._y

    def clip(self, other) -> FRect:
        o = FRect(other)
        x = max(self._x, o._x)
        y = max(self._y, o._y)
        r = min(self._x + self._w, o._x + o._w)
        b = min(self._y + self._h, o._y + o._h)
        return FRect(x, y, max(0, r - x), max(0, b - y))

    def union(self, other) -> FRect:
        o = FRect(other)
        x = min(self._x, o._x)
        y = min(self._y, o._y)
        r = max(self._x + self._w, o._x + o._w)
        b = max(self._y + self._h, o._y + o._h)
        return FRect(x, y, r - x, b - y)

    def union_ip(self, other) -> None:
        r = self.union(other)
        self._x, self._y, self._w, self._h = r._x, r._y, r._w, r._h

    def unionall(self, others) -> FRect:
        r = self.copy()
        for o in others:
            r = r.union(o)
        return r

    def unionall_ip(self, others) -> None:
        r = self.unionall(others)
        self._x, self._y, self._w, self._h = r._x, r._y, r._w, r._h

    def fit(self, other) -> FRect:
        o = FRect(other)
        ratio = max(self._w / o._w if o._w else 1,
                    self._h / o._h if o._h else 1)
        nw = self._w / ratio if ratio else self._w
        nh = self._h / ratio if ratio else self._h
        return FRect(o._x + (o._w - nw) / 2, o._y + (o._h - nh) / 2, nw, nh)

    def contains(self, other) -> bool:
        o = FRect(other)
        return (self._x <= o._x and self._y <= o._y and
                self._x + self._w >= o._x + o._w and
                self._y + self._h >= o._y + o._h and
                self._w > 0 and self._h > 0)

    def collidepoint(self, *args) -> bool:
        if len(args) == 1:
            x, y = args[0]
        elif len(args) == 2:
            x, y = args
        else:
            raise TypeError("collidepoint requires (x,y)")
        return (self._x <= x < self._x + self._w and
                self._y <= y < self._y + self._h)

    def colliderect(self, other) -> bool:
        o = FRect(other)
        return (self._x < o._x + o._w and self._x + self._w > o._x and
                self._y < o._y + o._h and self._y + self._h > o._y)

    def collidelist(self, rects) -> int:
        for i, r in enumerate(rects):
            if self.colliderect(r):
                return i
        return -1

    def collidelistall(self, rects) -> list[int]:
        return [i for i, r in enumerate(rects) if self.colliderect(r)]

    def copy(self) -> FRect:
        return FRect(self._x, self._y, self._w, self._h)

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index):
        return (self._x, self._y, self._w, self._h)[index]

    def __iter__(self):
        yield self._x; yield self._y; yield self._w; yield self._h

    def __contains__(self, item) -> bool:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            return self.collidepoint(item)
        return False

    def __bool__(self) -> bool:
        return self._w != 0 and self._h != 0

    def __eq__(self, other: object) -> bool:
        try:
            o = FRect(other)
            return (self._x == o._x and self._y == o._y and
                    self._w == o._w and self._h == o._h)
        except Exception:
            return NotImplemented

    def __hash__(self):
        raise TypeError("unhashable type: 'FRect'")

    def __repr__(self) -> str:
        return f"FRect({self._x}, {self._y}, {self._w}, {self._h})"
