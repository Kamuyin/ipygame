"""pygame-compatible transform module."""

from __future__ import annotations

import math as _math
from typing import Sequence

import numpy as np

from ipygame.surface import Surface
from ipygame.color import Color

__all__ = [
    "flip",
    "scale",
    "scale_by",
    "rotate",
    "rotozoom",
    "scale2x",
    "smoothscale",
    "smoothscale_by",
    "get_smoothscale_backend",
    "set_smoothscale_backend",
    "chop",
    "average_surfaces",
    "average_color",
    "invert",
    "grayscale",
    "threshold",
    "laplacian",
    "box_blur",
    "gaussian_blur",
    "solid_overlay",
    "hsl",
    "pixelate",
]


def _pil_image():
    from PIL import Image
    return Image


def flip(surface: Surface, flip_x: bool, flip_y: bool) -> Surface:
    """Flip a Surface horizontally, vertically, or both."""
    px = surface._pixels
    if flip_x:
        px = px[:, ::-1]
    if flip_y:
        px = px[::-1]
    out = Surface((px.shape[1], px.shape[0]))
    out._pixels[:] = px
    return out


def scale(surface: Surface, size, dest_surface: Surface | None = None) -> Surface:
    """Resize to *size* (w, h) using nearest-neighbor."""
    Image = _pil_image()
    w, h = int(size[0]), int(size[1])
    if w <= 0 or h <= 0:
        return Surface((max(w, 0), max(h, 0)))
    img = Image.fromarray(surface._pixels, "RGBA")
    img = img.resize((w, h), Image.NEAREST)
    arr = np.array(img, dtype=np.uint8)
    if dest_surface is not None and dest_surface.get_size() == (w, h):
        dest_surface._pixels[:] = arr
        return dest_surface
    out = Surface((w, h))
    out._pixels[:] = arr
    return out


def scale_by(surface: Surface, factor, dest_surface: Surface | None = None) -> Surface:
    """Resize by a scalar factor or (fx, fy) tuple."""
    if isinstance(factor, (int, float)):
        fx = fy = factor
    else:
        fx, fy = factor
    w = max(1, int(surface.width * fx))
    h = max(1, int(surface.height * fy))
    return scale(surface, (w, h), dest_surface)


def rotate(surface: Surface, angle: float) -> Surface:
    """Rotate the Surface counterclockwise by *angle* degrees."""
    Image = _pil_image()
    img = Image.fromarray(surface._pixels, "RGBA")
    rotated = img.rotate(angle, resample=Image.NEAREST, expand=True)
    arr = np.array(rotated, dtype=np.uint8)
    out = Surface((arr.shape[1], arr.shape[0]))
    out._pixels[:] = arr
    return out


def rotozoom(surface: Surface, angle: float, scale_factor: float) -> Surface:
    """Filtered rotate and scale."""
    Image = _pil_image()
    img = Image.fromarray(surface._pixels, "RGBA")
    if scale_factor != 1.0:
        nw = max(1, int(img.width * abs(scale_factor)))
        nh = max(1, int(img.height * abs(scale_factor)))
        img = img.resize((nw, nh), Image.BILINEAR)
    rotated = img.rotate(angle, resample=Image.BILINEAR, expand=True)
    arr = np.array(rotated, dtype=np.uint8)
    out = Surface((arr.shape[1], arr.shape[0]))
    out._pixels[:] = arr
    return out


def scale2x(surface: Surface, dest_surface: Surface | None = None) -> Surface:
    """Double the size of the Surface."""
    return scale(surface, (surface.width * 2, surface.height * 2), dest_surface)


def smoothscale(surface: Surface, size, dest_surface: Surface | None = None) -> Surface:
    """Resize with bilinear filtering."""
    Image = _pil_image()
    w, h = int(size[0]), int(size[1])
    if w <= 0 or h <= 0:
        return Surface((max(w, 0), max(h, 0)))
    img = Image.fromarray(surface._pixels, "RGBA")
    img = img.resize((w, h), Image.BILINEAR)
    arr = np.array(img, dtype=np.uint8)
    if dest_surface is not None and dest_surface.get_size() == (w, h):
        dest_surface._pixels[:] = arr
        return dest_surface
    out = Surface((w, h))
    out._pixels[:] = arr
    return out


def smoothscale_by(surface: Surface, factor,
                   dest_surface: Surface | None = None) -> Surface:
    """Smooth resize by a scalar factor or (fx, fy) tuple."""
    if isinstance(factor, (int, float)):
        fx = fy = factor
    else:
        fx, fy = factor
    w = max(1, int(surface.width * fx))
    h = max(1, int(surface.height * fy))
    return smoothscale(surface, (w, h), dest_surface)


def get_smoothscale_backend() -> str:
    return "GENERIC"


def set_smoothscale_backend(backend: str) -> None:
    pass


def chop(surface: Surface, rect) -> Surface:
    """Remove an interior rectangle; the remaining areas collapse together."""
    from ipygame.rect import Rect
    r = Rect(rect)
    px = surface._pixels
    h, w = px.shape[:2]
    top = px[:r.top, :] if r.top > 0 else np.empty((0, w, 4), dtype=np.uint8)
    bottom = px[r.bottom:, :] if r.bottom < h else np.empty((0, w, 4), dtype=np.uint8)
    middle_rows = np.vstack([top, bottom]) if (top.shape[0] + bottom.shape[0]) > 0 else np.empty((0, w, 4), dtype=np.uint8)

    left = middle_rows[:, :r.left] if r.left > 0 else np.empty((middle_rows.shape[0], 0, 4), dtype=np.uint8)
    right = middle_rows[:, r.right:] if r.right < w else np.empty((middle_rows.shape[0], 0, 4), dtype=np.uint8)
    result = np.hstack([left, right]) if (left.shape[1] + right.shape[1]) > 0 else np.empty((middle_rows.shape[0], 0, 4), dtype=np.uint8)

    nh, nw = result.shape[:2]
    out = Surface((nw, nh))
    if nw > 0 and nh > 0:
        out._pixels[:] = result
    return out


def invert(surface: Surface, dest_surface: Surface | None = None) -> Surface:
    """Invert RGB values (alpha unchanged)."""
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    out._pixels[:, :, :3] = 255 - surface._pixels[:, :, :3]
    out._pixels[:, :, 3] = surface._pixels[:, :, 3]
    return out


def grayscale(surface: Surface, dest_surface: Surface | None = None) -> Surface:
    """Convert to grayscale."""
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    px = surface._pixels
    gray = (px[:, :, 0].astype(np.uint16) * 299 +
            px[:, :, 1].astype(np.uint16) * 587 +
            px[:, :, 2].astype(np.uint16) * 114) // 1000
    gray8 = gray.astype(np.uint8)
    out._pixels[:, :, 0] = gray8
    out._pixels[:, :, 1] = gray8
    out._pixels[:, :, 2] = gray8
    out._pixels[:, :, 3] = px[:, :, 3]
    return out


def solid_overlay(surface: Surface, color,
                  dest_surface: Surface | None = None,
                  keep_alpha: bool = False) -> Surface:
    """Replace all non-transparent pixels with a solid color."""
    c = Color(color) if not isinstance(color, Color) else color
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    mask = surface._pixels[:, :, 3] > 0
    out._pixels[:, :, 0] = np.where(mask, c.r, 0)
    out._pixels[:, :, 1] = np.where(mask, c.g, 0)
    out._pixels[:, :, 2] = np.where(mask, c.b, 0)
    if keep_alpha:
        out._pixels[:, :, 3] = surface._pixels[:, :, 3]
    else:
        out._pixels[:, :, 3] = np.where(mask, c.a, 0)
    return out


def average_color(surface: Surface, rect=None,
                  consider_alpha: bool = False) -> tuple[int, int, int, int]:
    """Get the average RGBA color of a surface or sub-region."""
    if rect is not None:
        from ipygame.rect import Rect
        r = Rect(rect)
        px = surface._pixels[r.top:r.bottom, r.left:r.right]
    else:
        px = surface._pixels
    if px.size == 0:
        return (0, 0, 0, 0)
    if consider_alpha:
        alpha = px[:, :, 3].astype(np.float64)
        total_alpha = alpha.sum()
        if total_alpha < 1e-6:
            return (0, 0, 0, 0)
        r = (px[:, :, 0].astype(np.float64) * alpha).sum() / total_alpha
        g = (px[:, :, 1].astype(np.float64) * alpha).sum() / total_alpha
        b = (px[:, :, 2].astype(np.float64) * alpha).sum() / total_alpha
        a = total_alpha / px[:, :, 3].size
        return (int(r), int(g), int(b), int(a))
    means = px.reshape(-1, 4).mean(axis=0)
    return tuple(int(m) for m in means)  # type: ignore[return-value]


def average_surfaces(surfaces: Sequence[Surface],
                     dest_surface: Surface | None = None,
                     palette_colors: int = 1) -> Surface:
    """Average the colors of multiple same-size surfaces."""
    if not surfaces:
        raise ValueError("need at least one surface")
    size = surfaces[0].get_size()
    acc = surfaces[0]._pixels.astype(np.float64)
    for s in surfaces[1:]:
        acc += s._pixels.astype(np.float64)
    acc /= len(surfaces)
    out = dest_surface if dest_surface is not None else Surface(size)
    out._pixels[:] = acc.astype(np.uint8)
    return out


def threshold(dest_surface, surface: Surface, search_color,
              threshold_color=(0, 0, 0, 255), set_color=(0, 0, 0, 0),
              set_behavior: int = 1, other_surface: Surface | None = None,
              inverse: bool = False) -> int:
    """Find/set pixels within a color threshold. Returns count of matching pixels."""
    sc = Color(search_color)
    tc = Color(threshold_color)
    px = surface._pixels.astype(np.int16)
    diff = np.abs(px - np.array([sc.r, sc.g, sc.b, sc.a], dtype=np.int16))
    within = np.all(diff <= np.array([tc.r, tc.g, tc.b, tc.a], dtype=np.int16), axis=2)
    if inverse:
        within = ~within
    count = int(within.sum())
    if dest_surface is not None and set_behavior == 1:
        sc_arr = np.array([*Color(set_color)], dtype=np.uint8)
        dest_surface._pixels[within] = sc_arr
    return count


def box_blur(surface: Surface, radius: int,
             repeat_edge_pixels: bool = True,
             dest_surface: Surface | None = None) -> Surface:
    """Apply a box blur with the given pixel radius."""
    Image = _pil_image()
    from PIL import ImageFilter
    img = Image.fromarray(surface._pixels, "RGBA")
    blurred = img.filter(ImageFilter.BoxBlur(radius))
    arr = np.array(blurred, dtype=np.uint8)
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    out._pixels[:] = arr
    return out


def gaussian_blur(surface: Surface, radius: int,
                  repeat_edge_pixels: bool = True,
                  dest_surface: Surface | None = None) -> Surface:
    """Apply a Gaussian blur with the given pixel radius."""
    Image = _pil_image()
    from PIL import ImageFilter
    img = Image.fromarray(surface._pixels, "RGBA")
    blurred = img.filter(ImageFilter.GaussianBlur(radius))
    arr = np.array(blurred, dtype=np.uint8)
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    out._pixels[:] = arr
    return out


def laplacian(surface: Surface,
              dest_surface: Surface | None = None) -> Surface:
    """Edge-detection via Laplacian filter."""
    Image = _pil_image()
    from PIL import ImageFilter
    img = Image.fromarray(surface._pixels, "RGBA")
    rgb = img.convert("RGB").filter(ImageFilter.Kernel(
        (3, 3), [-1, -1, -1, -1, 8, -1, -1, -1, -1], scale=1, offset=128
    ))
    result = rgb.convert("RGBA")
    r, g, b, a = img.split()
    result.putalpha(a)
    arr = np.array(result, dtype=np.uint8)
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    out._pixels[:] = arr
    return out


def hsl(surface: Surface, hue: float = 0, saturation: float = 0,
        lightness: float = 0,
        dest_surface: Surface | None = None) -> Surface:
    """Adjust HSL of a surface. Values are offsets."""
    Image = _pil_image()
    from PIL import ImageEnhance
    img = Image.fromarray(surface._pixels, "RGBA")
    if saturation != 0:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.0 + saturation / 100.0)
    if lightness != 0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.0 + lightness / 100.0)
    if hue != 0:
        arr = np.array(img, dtype=np.uint8)
        import colorsys
        h_arr, w_arr = arr.shape[:2]
        flat = arr.reshape(-1, 4)
        for i in range(len(flat)):
            r, g, b, a = flat[i]
            h_val, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            h_val = (h_val + hue / 360.0) % 1.0
            rn, gn, bn = colorsys.hsv_to_rgb(h_val, s, v)
            flat[i] = [int(rn * 255), int(gn * 255), int(bn * 255), a]
        arr = flat.reshape(h_arr, w_arr, 4)
        img = Image.fromarray(arr, "RGBA")
    arr = np.array(img, dtype=np.uint8)
    out = dest_surface if dest_surface is not None else Surface(surface.get_size())
    out._pixels[:] = arr
    return out


def pixelate(surface: Surface, pixel_size: int,
             dest_surface: Surface | None = None) -> Surface:
    """Pixelate a surface by downscaling and upscaling."""
    Image = _pil_image()
    w, h = surface.get_size()
    small_w = max(1, w // pixel_size)
    small_h = max(1, h // pixel_size)
    img = Image.fromarray(surface._pixels, "RGBA")
    small = img.resize((small_w, small_h), Image.NEAREST)
    big = small.resize((w, h), Image.NEAREST)
    arr = np.array(big, dtype=np.uint8)
    out = dest_surface if dest_surface is not None else Surface((w, h))
    out._pixels[:] = arr
    return out
