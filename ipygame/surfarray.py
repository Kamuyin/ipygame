"""pygame-compatible surfarray module."""

from __future__ import annotations

import numpy as np

from ipygame.surface import Surface

__all__ = [
    "array2d",
    "pixels2d",
    "array3d",
    "pixels3d",
    "array_alpha",
    "pixels_alpha",
    "array_red",
    "pixels_red",
    "array_green",
    "pixels_green",
    "array_blue",
    "pixels_blue",
    "array_colorkey",
    "make_surface",
    "blit_array",
    "map_array",
    "array_to_surface",
    "surface_to_array",
]


def _pack_rgb(pixels: np.ndarray) -> np.ndarray:
    return (pixels[:, :, 0].astype(np.uint32) << 16 |
            pixels[:, :, 1].astype(np.uint32) << 8 |
            pixels[:, :, 2].astype(np.uint32) |
            pixels[:, :, 3].astype(np.uint32) << 24)


def array2d(surface: Surface) -> np.ndarray:
    """Copy pixel data as a 2D array of mapped colors (uint32)."""
    return _pack_rgb(surface._pixels)


def pixels2d(surface: Surface) -> np.ndarray:
    """Return a 2D reference to surface pixels (copy — true sharing not possible)."""
    # True pixel sharing requires same memory layout; we return a copy.
    return array2d(surface)


def array3d(surface: Surface) -> np.ndarray:
    """Copy RGB data as a (H,W,3) array."""
    return surface._pixels[:, :, :3].copy()


def pixels3d(surface: Surface) -> np.ndarray:
    """Return a (H,W,3) view into the surface's RGB channels.

    Modifications to the returned array will modify the surface.
    """
    return surface._pixels[:, :, :3]


def array_alpha(surface: Surface) -> np.ndarray:
    """Copy alpha channel as a (H,W) array."""
    return surface._pixels[:, :, 3].copy()


def pixels_alpha(surface: Surface) -> np.ndarray:
    """Return a view into the surface's alpha channel."""
    return surface._pixels[:, :, 3]


def array_red(surface: Surface) -> np.ndarray:
    return surface._pixels[:, :, 0].copy()


def pixels_red(surface: Surface) -> np.ndarray:
    return surface._pixels[:, :, 0]


def array_green(surface: Surface) -> np.ndarray:
    return surface._pixels[:, :, 1].copy()


def pixels_green(surface: Surface) -> np.ndarray:
    return surface._pixels[:, :, 1]


def array_blue(surface: Surface) -> np.ndarray:
    return surface._pixels[:, :, 2].copy()


def pixels_blue(surface: Surface) -> np.ndarray:
    return surface._pixels[:, :, 2]


def array_colorkey(surface: Surface) -> np.ndarray:
    """Return a 2D array where colorkey-pixels are 0, others 255."""
    ck = surface.get_colorkey()
    if ck is None:
        return np.full((surface.height, surface.width), 255, dtype=np.uint8)
    px = surface._pixels
    match = (
        (px[:, :, 0] == ck[0]) &
        (px[:, :, 1] == ck[1]) &
        (px[:, :, 2] == ck[2])
    )
    result = np.full((surface.height, surface.width), 255, dtype=np.uint8)
    result[match] = 0
    return result


def make_surface(array: np.ndarray) -> Surface:
    """Create a new Surface from a numpy array.

    Accepts (H,W,3) RGB, (H,W,4) RGBA, or (H,W) mapped uint32.
    """
    if array.ndim == 2:
        h, w = array.shape
        surf = Surface((w, h))
        arr32 = array.astype(np.uint32)
        surf._pixels[:, :, 0] = ((arr32 >> 16) & 0xFF).astype(np.uint8)
        surf._pixels[:, :, 1] = ((arr32 >> 8) & 0xFF).astype(np.uint8)
        surf._pixels[:, :, 2] = (arr32 & 0xFF).astype(np.uint8)
        surf._pixels[:, :, 3] = ((arr32 >> 24) & 0xFF).astype(np.uint8)
        return surf
    elif array.ndim == 3:
        h, w = array.shape[:2]
        surf = Surface((w, h))
        if array.shape[2] == 3:
            surf._pixels[:, :, :3] = array.astype(np.uint8)
            surf._pixels[:, :, 3] = 255
        elif array.shape[2] == 4:
            surf._pixels[:] = array.astype(np.uint8)
        else:
            raise ValueError(f"Expected 3 or 4 channels, got {array.shape[2]}")
        return surf
    else:
        raise ValueError(f"Expected 2D or 3D array, got {array.ndim}D")


def blit_array(surface: Surface, array: np.ndarray) -> None:
    """Blit an array directly onto a surface."""
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


def map_array(surface: Surface, array: np.ndarray) -> np.ndarray:
    """Map a (H,W,3) RGB array to a (H,W) mapped-pixel array."""
    if array.ndim != 3 or array.shape[2] < 3:
        raise ValueError("Expected (H,W,3) array")
    return (array[:, :, 0].astype(np.uint32) << 16 |
            array[:, :, 1].astype(np.uint32) << 8 |
            array[:, :, 2].astype(np.uint32) |
            np.uint32(0xFF000000))


def surface_to_array(array: np.ndarray, surface: Surface,
                     kind: str = "P", opaque: int = 255,
                     clear: int = 0) -> None:
    """Copy surface pixels into an existing array."""
    k = kind.upper()
    if k == "P":
        array[:] = _pack_rgb(surface._pixels)
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


def array_to_surface(surface: Surface, array: np.ndarray) -> None:
    """Copy an array into a surface."""
    blit_array(surface, array)
