"""pygame-compatible Surface class."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from ipygame.color import Color
from ipygame.rect import Rect, FRect

__all__ = ["Surface"]


def _color_to_rgba(c) -> tuple[int, int, int, int]:
    if isinstance(c, Color):
        return c._as_rgba_tuple()
    if isinstance(c, str):
        return Color(c)._as_rgba_tuple()
    if isinstance(c, int):
        return Color(c)._as_rgba_tuple()
    if isinstance(c, (tuple, list)):
        if len(c) == 3:
            return (int(c[0]), int(c[1]), int(c[2]), 255)
        if len(c) == 4:
            return (int(c[0]), int(c[1]), int(c[2]), int(c[3]))
    raise TypeError(f"invalid color: {c!r}")


class Surface:
    """A 2-D image stored as a NumPy RGBA pixel buffer.

    Parameters
    ----------
    size : (int, int)
        Width and height of the surface.
    flags : int
        Surface flags (currently unused; kept for API compatibility).
    depth : int
        Bit depth (always treated as 32).
    """

    __slots__ = (
        "_pixels",
        "_flags",
        "_clip",
        "_colorkey",
        "_alpha",
        "_is_display",
        "_locked",
        "_parent",
    )

    def __init__(
        self,
        size: tuple[int, int] = (0, 0),
        flags: int = 0,
        depth: int = 32,
        *,
        _pixels: np.ndarray | None = None,
        _parent: "Surface | None" = None,
    ):
        w, h = int(size[0]), int(size[1])
        if _pixels is not None:
            self._pixels = _pixels
        else:
            self._pixels = np.zeros((h, w, 4), dtype=np.uint8)
        self._flags = flags
        self._clip = None
        self._colorkey = None
        self._alpha = None
        self._is_display = False
        self._locked = 0
        self._parent = _parent

    @property
    def width(self) -> int:
        return self._pixels.shape[1]

    @property
    def height(self) -> int:
        return self._pixels.shape[0]

    @property
    def size(self) -> tuple[int, int]:
        return (self._pixels.shape[1], self._pixels.shape[0])

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def get_size(self) -> tuple[int, int]:
        return self.size

    def get_rect(self, **kwargs) -> Rect:
        r = Rect(0, 0, self.width, self.height)
        for attr, value in kwargs.items():
            setattr(r, attr, value)
        return r

    def get_frect(self, **kwargs) -> FRect:
        r = FRect(0, 0, self.width, self.height)
        for attr, value in kwargs.items():
            setattr(r, attr, value)
        return r

    def get_bitsize(self) -> int:
        return 32

    def get_bytesize(self) -> int:
        return 4

    def get_flags(self) -> int:
        return self._flags

    def get_pitch(self) -> int:
        return self.width * 4

    def get_masks(self) -> tuple[int, int, int, int]:
        return (0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF)

    def get_shifts(self) -> tuple[int, int, int, int]:
        return (24, 16, 8, 0)

    def get_losses(self) -> tuple[int, int, int, int]:
        return (0, 0, 0, 0)

    def get_at(self, pos) -> Color:
        x, y = int(pos[0]), int(pos[1])
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"pixel index ({x}, {y}) out of range")
        px = self._pixels[y, x]
        return Color(int(px[0]), int(px[1]), int(px[2]), int(px[3]))

    def set_at(self, pos, color) -> None:
        x, y = int(pos[0]), int(pos[1])
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"pixel index ({x}, {y}) out of range")
        r, g, b, a = _color_to_rgba(color)
        self._pixels[y, x] = (r, g, b, a)

    def get_at_mapped(self, pos) -> int:
        c = self.get_at(pos)
        return int(c)

    def map_rgb(self, color) -> int:
        r, g, b, a = _color_to_rgba(color)
        return (r << 24) | (g << 16) | (b << 8) | a

    def unmap_rgb(self, mapped: int) -> Color:
        return Color(mapped)

    def fill(self, color, rect=None, special_flags: int = 0) -> Rect:
        """Fill the surface (or a sub-region) with *color*."""
        r, g, b, a = _color_to_rgba(color)
        if rect is not None:
            area = Rect(rect)
        else:
            area = Rect(0, 0, self.width, self.height)

        area = area.clip(Rect(0, 0, self.width, self.height))
        if self._clip:
            area = area.clip(self._clip)
        if area.w <= 0 or area.h <= 0:
            return area

        x, y, w, h = area
        self._pixels[y:y + h, x:x + w] = (r, g, b, a)
        return area

    def blit(
        self,
        source: "Surface",
        dest=(0, 0),
        area=None,
        special_flags: int = 0,
    ) -> Rect:
        """Draw *source* onto this surface at *dest*."""
        if isinstance(dest, (Rect, FRect)):
            dx, dy = int(dest.x), int(dest.y)
        elif hasattr(dest, "__len__") and len(dest) >= 2:
            dx, dy = int(dest[0]), int(dest[1])
        else:
            raise TypeError(f"invalid dest: {dest!r}")

        if area is not None:
            sa = Rect(area)
        else:
            sa = Rect(0, 0, source.width, source.height)

        sa = sa.clip(Rect(0, 0, source.width, source.height))

        dr = Rect(dx, dy, sa.w, sa.h)
        clip_rect = self._clip if self._clip else Rect(0, 0, self.width, self.height)
        visible = dr.clip(clip_rect)
        if visible.w <= 0 or visible.h <= 0:
            return Rect(dx, dy, 0, 0)

        sx = sa.x + (visible.x - dx)
        sy = sa.y + (visible.y - dy)

        src_region = source._pixels[sy:sy + visible.h, sx:sx + visible.w]

        if special_flags == 0:
            src_alpha = src_region[:, :, 3:4].astype(np.float32) / 255.0
            dst_region = self._pixels[visible.y:visible.y + visible.h,
                                       visible.x:visible.x + visible.w]
            dst_alpha = 1.0 - src_alpha

            if source._colorkey is not None:
                ck = np.array(source._colorkey[:3], dtype=np.uint8)
                mask = np.all(src_region[:, :, :3] == ck, axis=2, keepdims=True)
                src_alpha = np.where(mask, 0.0, src_alpha)
                dst_alpha = 1.0 - src_alpha

            blended = (src_region[:, :, :3].astype(np.float32) * src_alpha
                       + dst_region[:, :, :3].astype(np.float32) * dst_alpha)
            self._pixels[visible.y:visible.y + visible.h,
                          visible.x:visible.x + visible.w, :3] = blended.astype(np.uint8)
            new_alpha = np.maximum(src_region[:, :, 3], dst_region[:, :, 3])
            self._pixels[visible.y:visible.y + visible.h,
                          visible.x:visible.x + visible.w, 3] = new_alpha
        else:
            self._pixels[visible.y:visible.y + visible.h,
                          visible.x:visible.x + visible.w] = src_region

        return Rect(visible)

    def blits(
        self,
        blit_sequence,
        doreturn: bool = True,
    ) -> list[Rect] | None:
        results = []
        for item in blit_sequence:
            if isinstance(item, tuple):
                r = self.blit(*item)
            else:
                raise TypeError(f"invalid blit argument: {item!r}")
            results.append(r)
        return results if doreturn else None

    def fblits(self, blit_sequence, special_flags: int = 0) -> None:
        for source, dest in blit_sequence:
            self.blit(source, dest, special_flags=special_flags)

    def convert(self, *args) -> "Surface":
        """Return a copy (everything is 32-bit RGBA in ipygame)."""
        return self.copy()

    def convert_alpha(self, *args) -> "Surface":
        """Return a copy (everything is 32-bit RGBA in ipygame)."""
        return self.copy()

    def copy(self) -> "Surface":
        s = Surface.__new__(Surface)
        s._pixels = self._pixels.copy()
        s._flags = self._flags
        s._clip = self._clip.copy() if self._clip else None
        s._colorkey = self._colorkey
        s._alpha = self._alpha
        s._is_display = False
        s._locked = 0
        s._parent = None
        return s

    def subsurface(self, rect) -> "Surface":
        """Return a Surface sharing pixels with a region of this Surface."""
        area = Rect(rect)
        area = area.clip(Rect(0, 0, self.width, self.height))
        sub_pixels = self._pixels[area.y:area.y + area.h,
                                   area.x:area.x + area.w]
        s = Surface.__new__(Surface)
        s._pixels = sub_pixels  # numpy view — shared memory
        s._flags = self._flags
        s._clip = None
        s._colorkey = self._colorkey
        s._alpha = self._alpha
        s._is_display = False
        s._locked = 0
        s._parent = self
        return s

    def scroll(self, dx: int = 0, dy: int = 0) -> None:
        if dx == 0 and dy == 0:
            return
        self._pixels[:] = np.roll(self._pixels, (dy, dx), axis=(0, 1))

    def set_colorkey(self, color=None, flags: int = 0) -> None:
        if color is None:
            self._colorkey = None
        else:
            self._colorkey = _color_to_rgba(color)

    def get_colorkey(self) -> tuple[int, int, int, int] | None:
        return self._colorkey

    def set_alpha(self, value: int | None = None, flags: int = 0) -> None:
        self._alpha = value

    def get_alpha(self) -> int | None:
        return self._alpha

    def set_clip(self, rect=None) -> None:
        if rect is None:
            self._clip = None
        else:
            self._clip = Rect(rect).clip(Rect(0, 0, self.width, self.height))

    def get_clip(self) -> Rect:
        if self._clip is not None:
            return self._clip.copy()
        return Rect(0, 0, self.width, self.height)

    def lock(self) -> None:
        self._locked += 1

    def unlock(self) -> None:
        self._locked = max(0, self._locked - 1)

    def mustlock(self) -> bool:
        return False

    def get_locked(self) -> bool:
        return self._locked > 0

    def get_locks(self) -> tuple:
        return ()

    def get_view(self, kind: str = "2") -> memoryview:
        return memoryview(self._pixels)

    def get_buffer(self) -> memoryview:
        return memoryview(self._pixels)

    def get_bounding_rect(self, min_alpha: int = 1) -> Rect:
        """Return the smallest Rect containing all pixels with alpha >= *min_alpha*."""
        alpha = self._pixels[:, :, 3]
        rows = np.any(alpha >= min_alpha, axis=1)
        cols = np.any(alpha >= min_alpha, axis=0)
        if not rows.any():
            return Rect(0, 0, 0, 0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        return Rect(int(cmin), int(rmin),
                     int(cmax - cmin + 1), int(rmax - rmin + 1))

    def premul_alpha(self) -> "Surface":
        s = self.copy()
        af = s._pixels[:, :, 3:4].astype(np.float32) / 255.0
        s._pixels[:, :, :3] = (s._pixels[:, :, :3].astype(np.float32) * af).astype(np.uint8)
        return s

    def premul_alpha_ip(self) -> None:
        af = self._pixels[:, :, 3:4].astype(np.float32) / 255.0
        self._pixels[:, :, :3] = (self._pixels[:, :, :3].astype(np.float32) * af).astype(np.uint8)

    def __repr__(self) -> str:
        return f"<Surface({self.width}x{self.height}x32)>"
