"""pygame-compatible mask module."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from ipygame.rect import Rect
from ipygame.surface import Surface
from ipygame.color import Color

__all__ = [
    "Mask",
    "from_surface",
    "from_threshold",
]


def from_surface(surface: Surface, threshold: int = 127) -> "Mask":
    """Create a Mask from a Surface's alpha channel."""
    alpha = surface._pixels[:, :, 3]
    m = Mask(surface.get_size())
    m._bits[:] = alpha > threshold
    return m


def from_threshold(surface: Surface, color, threshold=(0, 0, 0, 255),
                   other_surface: Surface | None = None,
                   palette_colors: int = 1) -> "Mask":
    """Create a Mask from a Surface using a color threshold."""
    c = Color(color) if not isinstance(color, Color) else color
    t = Color(threshold) if not isinstance(threshold, Color) else threshold
    px = surface._pixels.astype(np.int16)
    target = np.array([c.r, c.g, c.b, c.a], dtype=np.int16)
    thresh = np.array([t.r, t.g, t.b, t.a], dtype=np.int16)
    diff = np.abs(px - target)
    within = np.all(diff <= thresh, axis=2)
    m = Mask(surface.get_size())
    m._bits[:] = within
    return m


class Mask:
    """2D bit mask for pixel-perfect collision detection."""

    def __init__(self, size: tuple[int, int], fill: bool = False):
        w, h = int(size[0]), int(size[1])
        self._w = w
        self._h = h
        self._bits = np.full((h, w), fill, dtype=bool)

    def __repr__(self) -> str:
        return f"<Mask({self._w}x{self._h})>"

    def get_size(self) -> tuple[int, int]:
        return (self._w, self._h)

    def get_rect(self, **kwargs) -> Rect:
        r = Rect(0, 0, self._w, self._h)
        for k, v in kwargs.items():
            setattr(r, k, v)
        return r

    def get_at(self, pos) -> int:
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self._w and 0 <= y < self._h:
            return int(self._bits[y, x])
        raise IndexError(f"position ({x}, {y}) out of bounds")

    def set_at(self, pos, value: int = 1) -> None:
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self._w and 0 <= y < self._h:
            self._bits[y, x] = bool(value)
        else:
            raise IndexError(f"position ({x}, {y}) out of bounds")

    def fill(self) -> None:
        self._bits[:] = True

    def clear(self) -> None:
        self._bits[:] = False

    def invert(self) -> None:
        self._bits = ~self._bits

    def count(self) -> int:
        return int(self._bits.sum())

    def overlap(self, other: "Mask", offset: tuple[int, int]) -> tuple[int, int] | None:
        """Return the first overlapping bit position, or None."""
        ox, oy = int(offset[0]), int(offset[1])
        x1 = max(0, ox)
        y1 = max(0, oy)
        x2 = min(self._w, other._w + ox)
        y2 = min(self._h, other._h + oy)
        if x1 >= x2 or y1 >= y2:
            return None
        self_slice = self._bits[y1:y2, x1:x2]
        other_slice = other._bits[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
        overlap = self_slice & other_slice
        indices = np.argwhere(overlap)
        if len(indices) == 0:
            return None
        ry, rx = indices[0]
        return (int(rx + x1), int(ry + y1))

    def overlap_area(self, other: "Mask", offset: tuple[int, int]) -> int:
        """Count overlapping set bits."""
        ox, oy = int(offset[0]), int(offset[1])
        x1, y1 = max(0, ox), max(0, oy)
        x2 = min(self._w, other._w + ox)
        y2 = min(self._h, other._h + oy)
        if x1 >= x2 or y1 >= y2:
            return 0
        s = self._bits[y1:y2, x1:x2]
        o = other._bits[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
        return int((s & o).sum())

    def overlap_mask(self, other: "Mask", offset: tuple[int, int]) -> "Mask":
        """Return a Mask of overlapping bits."""
        result = Mask(self.get_size())
        ox, oy = int(offset[0]), int(offset[1])
        x1, y1 = max(0, ox), max(0, oy)
        x2 = min(self._w, other._w + ox)
        y2 = min(self._h, other._h + oy)
        if x1 < x2 and y1 < y2:
            s = self._bits[y1:y2, x1:x2]
            o = other._bits[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
            result._bits[y1:y2, x1:x2] = s & o
        return result

    def draw(self, other: "Mask", offset: tuple[int, int]) -> None:
        """OR another mask onto this mask."""
        ox, oy = int(offset[0]), int(offset[1])
        x1, y1 = max(0, ox), max(0, oy)
        x2 = min(self._w, other._w + ox)
        y2 = min(self._h, other._h + oy)
        if x1 < x2 and y1 < y2:
            o = other._bits[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
            self._bits[y1:y2, x1:x2] |= o

    def erase(self, other: "Mask", offset: tuple[int, int]) -> None:
        """Clear bits where *other* has bits set."""
        ox, oy = int(offset[0]), int(offset[1])
        x1, y1 = max(0, ox), max(0, oy)
        x2 = min(self._w, other._w + ox)
        y2 = min(self._h, other._h + oy)
        if x1 < x2 and y1 < y2:
            o = other._bits[y1 - oy:y2 - oy, x1 - ox:x2 - ox]
            self._bits[y1:y2, x1:x2] &= ~o

    def centroid(self) -> tuple[int, int]:
        """Return the centroid of set bits."""
        indices = np.argwhere(self._bits)
        if len(indices) == 0:
            return (0, 0)
        return (int(indices[:, 1].mean()), int(indices[:, 0].mean()))

    def angle(self) -> float:
        """Return the orientation angle of set bits in degrees."""
        indices = np.argwhere(self._bits)
        if len(indices) < 2:
            return 0.0
        ys, xs = indices[:, 0].astype(float), indices[:, 1].astype(float)
        cx, cy = xs.mean(), ys.mean()
        xs -= cx
        ys -= cy
        import math
        cov_xx = (xs * xs).sum()
        cov_xy = (xs * ys).sum()
        cov_yy = (ys * ys).sum()
        theta = 0.5 * math.atan2(2 * cov_xy, cov_xx - cov_yy)
        return math.degrees(theta)

    def outline(self, every: int = 1) -> list[tuple[int, int]]:
        """Return a list of points on the outline of the mask."""
        # Simple edge detection: any set bit adjacent to an unset bit
        padded = np.pad(self._bits, 1, constant_values=False)
        edge = self._bits & ~(
            padded[:-2, 1:-1] & padded[2:, 1:-1] &
            padded[1:-1, :-2] & padded[1:-1, 2:]
        )
        indices = np.argwhere(edge)
        return [(int(x), int(y)) for y, x in indices[::every]]

    def scale(self, size: tuple[int, int]) -> "Mask":
        """Return a scaled copy of the mask."""
        from PIL import Image
        w, h = int(size[0]), int(size[1])
        img = Image.fromarray(self._bits.astype(np.uint8) * 255, "L")
        img = img.resize((w, h), Image.NEAREST)
        m = Mask((w, h))
        m._bits = np.array(img, dtype=np.uint8) > 127
        return m

    def connected_component(self, pos=None) -> "Mask":
        """Return the connected component containing *pos* (or the largest)."""
        from scipy import ndimage
        labels, n = ndimage.label(self._bits)
        if pos is not None:
            x, y = int(pos[0]), int(pos[1])
            if 0 <= x < self._w and 0 <= y < self._h:
                label = labels[y, x]
                if label == 0:
                    return Mask(self.get_size())
                m = Mask(self.get_size())
                m._bits = labels == label
                return m
        if n == 0:
            return Mask(self.get_size())
        counts = np.bincount(labels.ravel())
        counts[0] = 0
        largest = counts.argmax()
        m = Mask(self.get_size())
        m._bits = labels == largest
        return m

    def connected_components(self, minimum: int = 0) -> list["Mask"]:
        """Return all connected components."""
        from scipy import ndimage
        labels, n = ndimage.label(self._bits)
        result = []
        for i in range(1, n + 1):
            bits = labels == i
            if bits.sum() >= minimum:
                m = Mask(self.get_size())
                m._bits = bits
                result.append(m)
        return result

    def get_bounding_rects(self) -> list[Rect]:
        """Return bounding rects for each connected component."""
        from scipy import ndimage
        labels, n = ndimage.label(self._bits)
        rects = []
        for i in range(1, n + 1):
            ys, xs = np.where(labels == i)
            if len(xs) == 0:
                continue
            x1, x2 = int(xs.min()), int(xs.max()) + 1
            y1, y2 = int(ys.min()), int(ys.max()) + 1
            rects.append(Rect(x1, y1, x2 - x1, y2 - y1))
        return rects

    def convolve(self, other: "Mask", output: "Mask | None" = None,
                 offset: tuple[int, int] = (0, 0)) -> "Mask":
        """Convolve this mask with another."""
        from scipy.signal import fftconvolve
        result_w = self._w + other._w - 1
        result_h = self._h + other._h - 1
        conv = fftconvolve(self._bits.astype(float),
                           other._bits.astype(float), mode='full')
        if output is None:
            output = Mask((result_w, result_h))
        out_h, out_w = output._bits.shape
        ox, oy = int(offset[0]), int(offset[1])
        # Copy the relevant portion
        for y in range(out_h):
            for x in range(out_w):
                cy, cx = y - oy, x - ox
                if 0 <= cy < result_h and 0 <= cx < result_w:
                    output._bits[y, x] = conv[cy, cx] > 0.5
        return output

    def to_surface(self, surface: Surface | None = None,
                   setsurface: Surface | None = None,
                   unsetsurface: Surface | None = None,
                   setcolor=(255, 255, 255, 255),
                   unsetcolor=(0, 0, 0, 255),
                   dest=(0, 0)) -> Surface:
        """Render the mask onto a Surface."""
        if surface is None:
            surface = Surface(self.get_size())
        sc = Color(setcolor) if setcolor is not None else None
        uc = Color(unsetcolor) if unsetcolor is not None else None
        dx, dy = int(dest[0]), int(dest[1])

        for y in range(self._h):
            for x in range(self._w):
                tx, ty = x + dx, y + dy
                if 0 <= tx < surface.width and 0 <= ty < surface.height:
                    if self._bits[y, x]:
                        if setsurface is not None and x < setsurface.width and y < setsurface.height:
                            surface._pixels[ty, tx] = setsurface._pixels[y, x]
                        elif sc is not None:
                            surface._pixels[ty, tx] = [sc.r, sc.g, sc.b, sc.a]
                    else:
                        if unsetsurface is not None and x < unsetsurface.width and y < unsetsurface.height:
                            surface._pixels[ty, tx] = unsetsurface._pixels[y, x]
                        elif uc is not None:
                            surface._pixels[ty, tx] = [uc.r, uc.g, uc.b, uc.a]
        return surface

    def copy(self) -> "Mask":
        m = Mask(self.get_size())
        m._bits[:] = self._bits
        return m

    def __copy__(self) -> "Mask":
        return self.copy()
