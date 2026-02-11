from __future__ import annotations

import math
from typing import Iterator, Self, Sequence, SupportsIndex

from ipygame.colordict import THECOLORS

__all__ = ["Color"]


def _clamp(v: int, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, int(v)))


class Color:
    __slots__ = ("_r", "_g", "_b", "_a")

    def __init__(self, *args):
        if len(args) == 1:
            val = args[0]
            if isinstance(val, Color):
                self._r, self._g, self._b, self._a = val._r, val._g, val._b, val._a
            elif isinstance(val, str):
                self._from_string(val)
            elif isinstance(val, int):
                self._r = (val >> 24) & 0xFF
                self._g = (val >> 16) & 0xFF
                self._b = (val >> 8) & 0xFF
                self._a = val & 0xFF
            elif isinstance(val, (tuple, list)):
                self._from_sequence(val)
            else:
                raise TypeError(f"invalid color argument: {val!r}")
        elif 3 <= len(args) <= 4:
            self._from_sequence(args)
        else:
            raise TypeError(
                f"Color() takes 1, 3, or 4 arguments ({len(args)} given)"
            )

    def _from_string(self, s: str) -> None:
        s = s.strip()
        if s.startswith("#"):
            h = s[1:]
            if len(h) == 6:
                self._r = int(h[0:2], 16)
                self._g = int(h[2:4], 16)
                self._b = int(h[4:6], 16)
                self._a = 255
            elif len(h) == 8:
                self._r = int(h[0:2], 16)
                self._g = int(h[2:4], 16)
                self._b = int(h[4:6], 16)
                self._a = int(h[6:8], 16)
            else:
                raise ValueError(f"invalid hex color: {s!r}")
        elif s.startswith("0x") or s.startswith("0X"):
            v = int(s, 16)
            self._r = (v >> 24) & 0xFF
            self._g = (v >> 16) & 0xFF
            self._b = (v >> 8) & 0xFF
            self._a = v & 0xFF
        else:
            key = s.lower().replace(" ", "")
            if key not in THECOLORS:
                raise ValueError(f"unknown color name: {s!r}")
            rgba = THECOLORS[key]
            self._r, self._g, self._b, self._a = rgba[0], rgba[1], rgba[2], rgba[3]

    def _from_sequence(self, seq: Sequence) -> None:
        if len(seq) == 3:
            self._r = _clamp(seq[0])
            self._g = _clamp(seq[1])
            self._b = _clamp(seq[2])
            self._a = 255
        elif len(seq) == 4:
            self._r = _clamp(seq[0])
            self._g = _clamp(seq[1])
            self._b = _clamp(seq[2])
            self._a = _clamp(seq[3])
        else:
            raise ValueError(f"Color requires 3 or 4 components, got {len(seq)}")

    @property
    def r(self) -> int:
        return self._r

    @r.setter
    def r(self, value: int) -> None:
        self._r = _clamp(value)

    @property
    def g(self) -> int:
        return self._g

    @g.setter
    def g(self, value: int) -> None:
        self._g = _clamp(value)

    @property
    def b(self) -> int:
        return self._b

    @b.setter
    def b(self, value: int) -> None:
        self._b = _clamp(value)

    @property
    def a(self) -> int:
        return self._a

    @a.setter
    def a(self, value: int) -> None:
        self._a = _clamp(value)

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index: SupportsIndex | slice):
        t = (self._r, self._g, self._b, self._a)
        return t[index]

    def __setitem__(self, index: SupportsIndex, value: int) -> None:
        idx = index.__index__()
        if idx < 0:
            idx += 4
        if not 0 <= idx < 4:
            raise IndexError("Color index out of range")
        v = _clamp(value)
        if idx == 0:
            self._r = v
        elif idx == 1:
            self._g = v
        elif idx == 2:
            self._b = v
        else:
            self._a = v

    def __iter__(self) -> Iterator[int]:
        yield self._r
        yield self._g
        yield self._b
        yield self._a

    def __contains__(self, item: object) -> bool:
        return item in (self._r, self._g, self._b, self._a)

    @property
    def cmy(self) -> tuple[float, float, float]:
        """CMY representation (0.0 – 1.0 each)."""
        return (1.0 - self._r / 255.0,
                1.0 - self._g / 255.0,
                1.0 - self._b / 255.0)

    @cmy.setter
    def cmy(self, value: tuple[float, float, float]) -> None:
        c, m, y = value
        self._r = _clamp(round((1.0 - c) * 255))
        self._g = _clamp(round((1.0 - m) * 255))
        self._b = _clamp(round((1.0 - y) * 255))

    @classmethod
    def from_cmy(cls, c: float, m: float, y: float) -> Self:
        obj = cls.__new__(cls)
        obj._r = _clamp(round((1.0 - c) * 255))
        obj._g = _clamp(round((1.0 - m) * 255))
        obj._b = _clamp(round((1.0 - y) * 255))
        obj._a = 255
        return obj

    @property
    def hsva(self) -> tuple[float, float, float, float]:
        """(hue 0-360, sat 0-100, value 0-100, alpha 0-100)."""
        r, g, b = self._r / 255.0, self._g / 255.0, self._b / 255.0
        mx, mn = max(r, g, b), min(r, g, b)
        d = mx - mn
        # Value
        v = mx * 100.0
        # Saturation
        s = 0.0 if mx == 0 else (d / mx) * 100.0
        # Hue
        if d == 0:
            h = 0.0
        elif mx == r:
            h = 60.0 * (((g - b) / d) % 6)
        elif mx == g:
            h = 60.0 * (((b - r) / d) + 2)
        else:
            h = 60.0 * (((r - g) / d) + 4)
        if h < 0:
            h += 360.0
        return (h, s, v, self._a / 255.0 * 100.0)

    @hsva.setter
    def hsva(self, value: tuple[float, float, float, float]) -> None:
        h, s, v, a = value
        c = self._from_hsva_vals(h, s, v, a)
        self._r, self._g, self._b, self._a = c._r, c._g, c._b, c._a

    @classmethod
    def from_hsva(cls, h: float, s: float, v: float, a: float = 100.0) -> Self:
        return cls._from_hsva_vals(h, s, v, a)

    @classmethod
    def _from_hsva_vals(cls, h: float, s: float, v: float, a: float) -> Self:
        s /= 100.0
        v /= 100.0
        c = v * s
        x = c * (1 - abs((h / 60.0) % 2 - 1))
        m = v - c
        if h < 60:
            r1, g1, b1 = c, x, 0.0
        elif h < 120:
            r1, g1, b1 = x, c, 0.0
        elif h < 180:
            r1, g1, b1 = 0.0, c, x
        elif h < 240:
            r1, g1, b1 = 0.0, x, c
        elif h < 300:
            r1, g1, b1 = x, 0.0, c
        else:
            r1, g1, b1 = c, 0.0, x
        obj = cls.__new__(cls)
        obj._r = _clamp(round((r1 + m) * 255))
        obj._g = _clamp(round((g1 + m) * 255))
        obj._b = _clamp(round((b1 + m) * 255))
        obj._a = _clamp(round(a / 100.0 * 255))
        return obj

    @property
    def hsla(self) -> tuple[float, float, float, float]:
        """(hue 0-360, sat 0-100, lightness 0-100, alpha 0-100)."""
        r, g, b = self._r / 255.0, self._g / 255.0, self._b / 255.0
        mx, mn = max(r, g, b), min(r, g, b)
        d = mx - mn
        l = (mx + mn) / 2.0
        if d == 0:
            h = s = 0.0
        else:
            s = d / (1 - abs(2 * l - 1)) if (1 - abs(2 * l - 1)) != 0 else 0.0
            if mx == r:
                h = 60.0 * (((g - b) / d) % 6)
            elif mx == g:
                h = 60.0 * (((b - r) / d) + 2)
            else:
                h = 60.0 * (((r - g) / d) + 4)
        if h < 0:
            h += 360.0
        return (h, s * 100.0, l * 100.0, self._a / 255.0 * 100.0)

    @hsla.setter
    def hsla(self, value: tuple[float, float, float, float]) -> None:
        h, s, l, a = value
        c = self.from_hsla(h, s, l, a)
        self._r, self._g, self._b, self._a = c._r, c._g, c._b, c._a

    @classmethod
    def from_hsla(cls, h: float, s: float, l: float, a: float = 100.0) -> Self:
        s /= 100.0
        l /= 100.0
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60.0) % 2 - 1))
        m = l - c / 2.0
        if h < 60:
            r1, g1, b1 = c, x, 0.0
        elif h < 120:
            r1, g1, b1 = x, c, 0.0
        elif h < 180:
            r1, g1, b1 = 0.0, c, x
        elif h < 240:
            r1, g1, b1 = 0.0, x, c
        elif h < 300:
            r1, g1, b1 = x, 0.0, c
        else:
            r1, g1, b1 = c, 0.0, x
        obj = cls.__new__(cls)
        obj._r = _clamp(round((r1 + m) * 255))
        obj._g = _clamp(round((g1 + m) * 255))
        obj._b = _clamp(round((b1 + m) * 255))
        obj._a = _clamp(round(a / 100.0 * 255))
        return obj

    @property
    def i1i2i3(self) -> tuple[float, float, float]:
        r, g, b = self._r / 255.0, self._g / 255.0, self._b / 255.0
        return ((r + g + b) / 3.0,
                (r - b) / 2.0,
                (2 * g - r - b) / 4.0)

    @classmethod
    def from_i1i2i3(cls, i1: float, i2: float, i3: float) -> Self:
        r = i1 + i2 - 2 * i3 / 3.0
        b = i1 - i2 - 2 * i3 / 3.0
        g = i1 + 4 * i3 / 3.0
        obj = cls.__new__(cls)
        obj._r = _clamp(round(r * 255))
        obj._g = _clamp(round(g * 255))
        obj._b = _clamp(round(b * 255))
        obj._a = 255
        return obj

    @property
    def normalized(self) -> tuple[float, float, float, float]:
        return (self._r / 255.0, self._g / 255.0, self._b / 255.0, self._a / 255.0)

    @normalized.setter
    def normalized(self, value: tuple[float, float, float, float]) -> None:
        r, g, b, a = value
        self._r = _clamp(round(r * 255))
        self._g = _clamp(round(g * 255))
        self._b = _clamp(round(b * 255))
        self._a = _clamp(round(a * 255))

    @classmethod
    def from_normalized(cls, r: float, g: float, b: float, a: float = 1.0) -> Self:
        obj = cls.__new__(cls)
        obj._r = _clamp(round(r * 255))
        obj._g = _clamp(round(g * 255))
        obj._b = _clamp(round(b * 255))
        obj._a = _clamp(round(a * 255))
        return obj

    @property
    def hex(self) -> str:
        return f"#{self._r:02X}{self._g:02X}{self._b:02X}{self._a:02X}"

    @classmethod
    def from_hex(cls, h: str) -> Self:
        return cls(h)

    def normalize(self) -> tuple[float, float, float, float]:
        return self.normalized

    def correct_gamma(self, gamma: float) -> Color:
        inv = 1.0 / gamma
        return Color(
            _clamp(round(pow(self._r / 255.0, inv) * 255)),
            _clamp(round(pow(self._g / 255.0, inv) * 255)),
            _clamp(round(pow(self._b / 255.0, inv) * 255)),
            self._a,
        )

    def lerp(self, other: Color | tuple, t: float) -> Color:
        if not isinstance(other, Color):
            other = Color(other)
        return Color(
            _clamp(round(self._r + (other._r - self._r) * t)),
            _clamp(round(self._g + (other._g - self._g) * t)),
            _clamp(round(self._b + (other._b - self._b) * t)),
            _clamp(round(self._a + (other._a - self._a) * t)),
        )

    def grayscale(self) -> Color:
        grey = _clamp(round(0.299 * self._r + 0.587 * self._g + 0.114 * self._b))
        return Color(grey, grey, grey, self._a)

    def premul_alpha(self) -> Color:
        af = self._a / 255.0
        return Color(
            _clamp(round(self._r * af)),
            _clamp(round(self._g * af)),
            _clamp(round(self._b * af)),
            self._a,
        )

    def update(self, *args) -> None:
        tmp = Color(*args)
        self._r, self._g, self._b, self._a = tmp._r, tmp._g, tmp._b, tmp._a

    def __add__(self, other: Color | tuple) -> Color:
        if not isinstance(other, Color):
            other = Color(other)
        return Color(
            min(self._r + other._r, 255),
            min(self._g + other._g, 255),
            min(self._b + other._b, 255),
            min(self._a + other._a, 255),
        )

    def __sub__(self, other: Color | tuple) -> Color:
        if not isinstance(other, Color):
            other = Color(other)
        return Color(
            max(self._r - other._r, 0),
            max(self._g - other._g, 0),
            max(self._b - other._b, 0),
            max(self._a - other._a, 0),
        )

    def __mul__(self, other: Color | tuple) -> Color:
        if not isinstance(other, Color):
            other = Color(other)
        return Color(
            _clamp((self._r * other._r) // 256),
            _clamp((self._g * other._g) // 256),
            _clamp((self._b * other._b) // 256),
            _clamp((self._a * other._a) // 256),
        )

    def __floordiv__(self, other: Color | tuple) -> Color:
        if not isinstance(other, Color):
            other = Color(other)
        return Color(
            self._r // other._r if other._r else 0,
            self._g // other._g if other._g else 0,
            self._b // other._b if other._b else 0,
            self._a // other._a if other._a else 0,
        )

    def __mod__(self, other: Color | tuple) -> Color:
        if not isinstance(other, Color):
            other = Color(other)
        return Color(
            self._r % other._r if other._r else 0,
            self._g % other._g if other._g else 0,
            self._b % other._b if other._b else 0,
            self._a % other._a if other._a else 0,
        )

    def __invert__(self) -> Color:
        return Color(255 - self._r, 255 - self._g, 255 - self._b, 255 - self._a)

    # Comparison and hashing

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return (self._r == other._r and self._g == other._g
                    and self._b == other._b and self._a == other._a)
        if isinstance(other, (tuple, list)) and len(other) in (3, 4):
            return tuple(self) == (tuple(other) if len(other) == 4
                                   else (*other, 255))
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._r, self._g, self._b, self._a))

    def __bool__(self) -> bool:
        return True

    def __int__(self) -> int:
        return (self._r << 24) | (self._g << 16) | (self._b << 8) | self._a

    def __repr__(self) -> str:
        return f"Color({self._r}, {self._g}, {self._b}, {self._a})"


    _SWIZZLE_MAP = {"r": 0, "g": 1, "b": 2, "a": 3}

    def __getattr__(self, name: str):
        if 1 < len(name) <= 4 and all(c in self._SWIZZLE_MAP for c in name):
            vals = tuple(self[self._SWIZZLE_MAP[c]] for c in name)
            return vals
        raise AttributeError(f"'Color' object has no attribute {name!r}")

    # Helper methods

    def _as_rgba_tuple(self) -> tuple[int, int, int, int]:
        return (self._r, self._g, self._b, self._a)

    def _as_css(self) -> str:
        """Return a CSS-compatible rgba() string."""
        if self._a == 255:
            return f"rgb({self._r},{self._g},{self._b})"
        return f"rgba({self._r},{self._g},{self._b},{self._a / 255:.3f})"
