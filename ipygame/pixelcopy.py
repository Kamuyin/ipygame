"""pygame-compatible pixelcopy module."""

from __future__ import annotations

import numpy as np

from ipygame.surface import Surface

__all__ = [
    "surface_to_array",
    "array_to_surface",
    "map_array",
    "make_surface",
]


def surface_to_array(array: np.ndarray, surface: Surface,
                     kind: str = "P", opaque: int = 255,
                     clear: int = 0) -> None:
    """Copy surface pixels into an existing array.

    *kind*: ``'P'`` mapped, ``'R'`` red, ``'G'`` green, ``'B'`` blue,
    ``'A'`` alpha, ``'C'`` colorkey.
    """
    k = kind.upper()
    if k == "P":
        px = surface._pixels
        array[:] = (px[:, :, 0].astype(np.uint32) << 16 |
                    px[:, :, 1].astype(np.uint32) << 8 |
                    px[:, :, 2].astype(np.uint32) |
                    px[:, :, 3].astype(np.uint32) << 24)
    elif k == "R":
        array[:] = surface._pixels[:, :, 0]
    elif k == "G":
        array[:] = surface._pixels[:, :, 1]
    elif k == "B":
        array[:] = surface._pixels[:, :, 2]
    elif k == "A":
        array[:] = surface._pixels[:, :, 3]
    elif k == "C":
        ck = surface.get_colorkey()
        if ck is None:
            array[:] = opaque
        else:
            px = surface._pixels
            match = (
                (px[:, :, 0] == ck[0]) &
                (px[:, :, 1] == ck[1]) &
                (px[:, :, 2] == ck[2])
            )
            array[:] = np.where(match, clear, opaque)
    else:
        raise ValueError(f"Unknown kind: {kind!r}")


def array_to_surface(surface: Surface, array: np.ndarray) -> None:
    """Copy an array into a surface's pixel buffer."""
    if array.ndim == 3:
        if array.shape[2] == 3:
            surface._pixels[:, :, :3] = array.astype(np.uint8)
        elif array.shape[2] == 4:
            surface._pixels[:] = array.astype(np.uint8)
    elif array.ndim == 2:
        arr32 = array.astype(np.uint32)
        surface._pixels[:, :, 0] = ((arr32 >> 16) & 0xFF).astype(np.uint8)
        surface._pixels[:, :, 1] = ((arr32 >> 8) & 0xFF).astype(np.uint8)
        surface._pixels[:, :, 2] = (arr32 & 0xFF).astype(np.uint8)
        surface._pixels[:, :, 3] = ((arr32 >> 24) & 0xFF).astype(np.uint8)


def map_array(array1: np.ndarray, array2: np.ndarray,
              surface: Surface) -> None:
    """Map a (H,W,3) RGB array to a (H,W) mapped-pixel array."""
    if array2.ndim != 3 or array2.shape[2] < 3:
        raise ValueError("Source array must be (H,W,3)")
    array1[:] = (array2[:, :, 0].astype(np.uint32) << 16 |
                 array2[:, :, 1].astype(np.uint32) << 8 |
                 array2[:, :, 2].astype(np.uint32) |
                 np.uint32(0xFF000000))


def make_surface(array: np.ndarray) -> Surface:
    """Create a new Surface from a numpy array."""
    from ipygame.surfarray import make_surface as _make
    return _make(array)
