"""pygame-compatible image module."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO, Union

import numpy as np

from ipygame.surface import Surface

__all__ = [
    "load",
    "save",
    "get_extended",
    "tobytes",
    "tostring",
    "frombytes",
    "fromstring",
    "frombuffer",
    "load_basic",
    "load_extended",
    "save_extended",
]

FileLike = Union[str, Path, BinaryIO]


def _ensure_pil():
    try:
        from PIL import Image
        return Image
    except ImportError:
        raise ImportError(
            "Pillow is required for ipygame.image. "
            "Install it with: pip install Pillow"
        )


def load(file: FileLike, namehint: str = "") -> Surface:
    """Load an image from a file path or file-like object."""
    Image = _ensure_pil()
    img = Image.open(file)
    img = img.convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]
    surf = Surface((w, h))
    surf._pixels[:] = arr
    return surf


def load_basic(file: FileLike) -> Surface:
    """Load a BMP image."""
    return load(file)


def load_extended(file: FileLike, namehint: str = "") -> Surface:
    """Load an image with extended format support."""
    return load(file, namehint)


def load_sized_svg(file: FileLike, size: tuple[int, int]) -> Surface:
    """Load an SVG rasterized at the given size.

    Requires the ``cairosvg`` package. Falls back to Pillow if available.
    """
    try:
        import cairosvg
    except ImportError:
        raise NotImplementedError(
            "SVG loading requires the cairosvg package: pip install cairosvg"
        )
    if isinstance(file, (str, Path)):
        png_data = cairosvg.svg2png(url=str(file),
                                     output_width=size[0],
                                     output_height=size[1])
    else:
        svg_data = file.read()
        png_data = cairosvg.svg2png(bytestring=svg_data,
                                     output_width=size[0],
                                     output_height=size[1])
    Image = _ensure_pil()
    img = Image.open(io.BytesIO(png_data)).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]
    surf = Surface((w, h))
    surf._pixels[:] = arr
    return surf


def save(surface: Surface, file: FileLike, namehint: str = "") -> None:
    """Save a Surface to a file (PNG, JPEG, BMP, TGA)."""
    Image = _ensure_pil()
    img = Image.fromarray(surface._pixels, "RGBA")

    fmt = None
    if isinstance(file, (str, Path)):
        ext = Path(file).suffix.lower()
        _FMT_MAP = {
            ".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG",
            ".bmp": "BMP", ".tga": "TGA",
        }
        fmt = _FMT_MAP.get(ext, "PNG")
    elif namehint:
        ext = Path(namehint).suffix.lower()
        _FMT_MAP = {
            ".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG",
            ".bmp": "BMP", ".tga": "TGA",
        }
        fmt = _FMT_MAP.get(ext, "PNG")

    if fmt == "JPEG":
        img = img.convert("RGB")

    img.save(file, format=fmt or "PNG")


def save_extended(surface: Surface, file: FileLike, namehint: str = "") -> None:
    """Save a Surface using extended format support."""
    save(surface, file, namehint)


def get_extended() -> bool:
    """Return True if extended image formats are available."""
    try:
        _ensure_pil()
        return True
    except ImportError:
        return False


def get_sdl_image_version(linked: bool = True):
    """Return None — SDL_image is not used."""
    return None


def tobytes(surface: Surface, format: str = "RGBA",
            flipped: bool = False, pitch: int = -1) -> bytes:
    """Transfer Surface pixels to a byte string."""
    pixels = surface._pixels
    if flipped:
        pixels = pixels[::-1]

    fmt = format.upper()
    if fmt == "RGBA":
        return pixels.tobytes()
    elif fmt == "ARGB":
        return pixels[:, :, [3, 0, 1, 2]].tobytes()
    elif fmt == "BGRA":
        return pixels[:, :, [2, 1, 0, 3]].tobytes()
    elif fmt == "ABGR":
        return pixels[:, :, [3, 2, 1, 0]].tobytes()
    elif fmt == "RGB":
        return pixels[:, :, :3].tobytes()
    elif fmt == "RGBX":
        return pixels.tobytes()
    elif fmt == "P":
        gray = (pixels[:, :, 0].astype(np.uint16) * 299 +
                pixels[:, :, 1].astype(np.uint16) * 587 +
                pixels[:, :, 2].astype(np.uint16) * 114) // 1000
        return gray.astype(np.uint8).tobytes()
    else:
        raise ValueError(f"Unsupported format: {format}")


def tostring(surface: Surface, format: str = "RGBA",
             flipped: bool = False, pitch: int = -1) -> bytes:
    """Deprecated — use ``tobytes``."""
    return tobytes(surface, format, flipped, pitch)


def frombytes(data: bytes, size: tuple[int, int],
              format: str = "RGBA", flipped: bool = False,
              pitch: int = -1) -> Surface:
    """Create a Surface from a byte buffer."""
    w, h = size
    fmt = format.upper()

    if fmt == "RGBA":
        arr = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4)).copy()
    elif fmt == "RGB":
        raw = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 3))
        arr = np.empty((h, w, 4), dtype=np.uint8)
        arr[:, :, :3] = raw
        arr[:, :, 3] = 255
    elif fmt == "ARGB":
        raw = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4))
        arr = raw[:, :, [1, 2, 3, 0]].copy()
    elif fmt == "BGRA":
        raw = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4))
        arr = raw[:, :, [2, 1, 0, 3]].copy()
    elif fmt == "ABGR":
        raw = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4))
        arr = raw[:, :, [3, 2, 1, 0]].copy()
    elif fmt == "RGBX":
        arr = np.frombuffer(data, dtype=np.uint8).reshape((h, w, 4)).copy()
        arr[:, :, 3] = 255
    else:
        raise ValueError(f"Unsupported format: {format}")

    if flipped:
        arr = arr[::-1].copy()

    surf = Surface((w, h))
    surf._pixels[:] = arr
    return surf


def fromstring(data: bytes, size: tuple[int, int],
               format: str = "RGBA", flipped: bool = False,
               pitch: int = -1) -> Surface:
    """Deprecated — use ``frombytes``."""
    return frombytes(data, size, format, flipped, pitch)


def frombuffer(data, size: tuple[int, int],
               format: str = "RGBA", pitch: int = -1) -> Surface:
    """Create a Surface from a buffer object (data is copied)."""
    if isinstance(data, (bytes, bytearray)):
        raw = data
    else:
        raw = bytes(data)
    return frombytes(raw, size, format)
