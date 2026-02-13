"""pygame-compatible display module."""

from __future__ import annotations

import os
import warnings
from typing import Sequence

import numpy as np

from ipygame._backend import get_backend
from ipygame.rect import Rect
from ipygame.surface import Surface

__all__ = [
    "init", "quit", "get_init",
    "set_mode", "get_surface", "flip", "update",
    "set_caption", "get_caption",
    "set_icon", "iconify", "toggle_fullscreen",
    "Info", "get_driver",
    "get_window_size",
]


def init() -> None:
    """Initialise the display module."""
    get_backend().mark_init()


def quit() -> None:
    """Uninitialise the display module."""
    b = get_backend()
    if b.canvas is not None:
        try:
            b.canvas.clear()
        except Exception:
            pass
    b.mark_quit()


def get_init() -> bool:
    return get_backend().initialized


def set_mode(
    size: tuple[int, int] = (0, 0),
    flags: int = 0,
    depth: int = 0,
    display: int = 0,
    vsync: int = 0,
) -> Surface:
    """Create a display Surface backed by an ipycanvas Canvas.

    The canvas widget is automatically shown in the notebook output.
    """
    from ipycanvas import Canvas, hold_canvas
    from IPython.display import display as ipy_display

    b = get_backend()
    if not b.initialized:
        init()

    w, h = int(size[0]), int(size[1])
    if w <= 0:
        w = 640
    if h <= 0:
        h = 480

    canvas = Canvas(width=w, height=h)
    canvas.layout.border = "1px solid #888"

    b.canvas = canvas
    surf = Surface((w, h), flags)
    surf._is_display = True
    surf._pixels[:, :] = (0, 0, 0, 255)
    b.display_surface = surf
    b.last_presented_pixels = None

    from ipygame.event import _wire_canvas_events
    _wire_canvas_events(canvas)

    ipy_display(canvas)

    return surf


def get_surface() -> Surface | None:
    """Return the current display Surface, or ``None``."""
    return get_backend().display_surface


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


_DELTA_FLIP_ENABLED = _env_bool("IPYGAME_DELTA_FLIP", True)
_DELTA_FLIP_MAX_BBOX_RATIO = max(0.05, min(1.0, _env_float("IPYGAME_DELTA_FLIP_MAX_BBOX_RATIO", 0.70)))


def flip() -> None:
    """Update the full display Surface to the canvas."""
    b = get_backend()
    if b.canvas is None or b.display_surface is None:
        return
    _flush_surface_to_canvas(b.canvas, b.display_surface, use_delta=_DELTA_FLIP_ENABLED)


def update(rectangle=None) -> None:
    """Update portions of the display (or the full display if *rectangle* is None)."""
    b = get_backend()
    if b.canvas is None or b.display_surface is None:
        return

    if rectangle is None:
        flip()
        return

    rects = _coerce_rectangles(rectangle, b.display_surface)
    if not rects:
        return

    _flush_rects_to_canvas(b.canvas, b.display_surface, rects)
    _update_presented_cache_for_rects(b.display_surface, rects)


def _flush_surface_to_canvas(canvas, surface: Surface, *, use_delta: bool) -> None:
    """Transfer Surface pixels to the ipycanvas Canvas, optionally using a delta update."""
    from ipycanvas import hold_canvas

    b = get_backend()
    current = surface._pixels

    if not use_delta:
        with hold_canvas(canvas):
            canvas.put_image_data(current, 0, 0)
        b.last_presented_pixels = current.copy()
        return

    previous = b.last_presented_pixels
    if previous is None or previous.shape != current.shape:
        with hold_canvas(canvas):
            canvas.put_image_data(current, 0, 0)
        b.last_presented_pixels = current.copy()
        return

    changed = np.any(current != previous, axis=2)
    if not np.any(changed):
        return

    ys, xs = np.where(changed)
    min_y = int(ys.min())
    max_y = int(ys.max())
    min_x = int(xs.min())
    max_x = int(xs.max())

    patch_w = max_x - min_x + 1
    patch_h = max_y - min_y + 1
    patch_area = patch_w * patch_h
    full_area = current.shape[0] * current.shape[1]
    patch_ratio = patch_area / max(1, full_area)

    if patch_ratio > _DELTA_FLIP_MAX_BBOX_RATIO:
        with hold_canvas(canvas):
            canvas.put_image_data(current, 0, 0)
        previous[:, :] = current
        return

    patch = current[min_y:max_y + 1, min_x:max_x + 1]
    with hold_canvas(canvas):
        canvas.put_image_data(patch, min_x, min_y)
    previous[min_y:max_y + 1, min_x:max_x + 1] = patch


def _coerce_rectangles(rectangle, surface: Surface) -> list[Rect]:
    def _to_rect(value) -> Rect | None:
        if isinstance(value, Rect):
            r = Rect(value)
        else:
            try:
                r = Rect(value)
            except Exception:
                return None
        clipped = r.clip(Rect(0, 0, surface.width, surface.height))
        if clipped.w <= 0 or clipped.h <= 0:
            return None
        return clipped

    if isinstance(rectangle, Rect):
        r = _to_rect(rectangle)
        return [r] if r is not None else []

    if isinstance(rectangle, Sequence) and not isinstance(rectangle, (str, bytes)):
        if len(rectangle) == 4 and not isinstance(rectangle[0], (Rect, list, tuple)):
            r = _to_rect(rectangle)
            return [r] if r is not None else []

        rects: list[Rect] = []
        for value in rectangle:
            r = _to_rect(value)
            if r is not None:
                rects.append(r)
        return rects

    r = _to_rect(rectangle)
    return [r] if r is not None else []


def _flush_rects_to_canvas(canvas, surface: Surface, rects: list[Rect]) -> None:
    from ipycanvas import hold_canvas

    with hold_canvas(canvas):
        for r in rects:
            patch = surface._pixels[r.y:r.y + r.h, r.x:r.x + r.w]
            canvas.put_image_data(patch, r.x, r.y)


def _update_presented_cache_for_rects(surface: Surface, rects: list[Rect]) -> None:
    b = get_backend()
    current = surface._pixels
    previous = b.last_presented_pixels

    if previous is None or previous.shape != current.shape:
        b.last_presented_pixels = current.copy()
        return

    for r in rects:
        previous[r.y:r.y + r.h, r.x:r.x + r.w] = current[r.y:r.y + r.h, r.x:r.x + r.w]


def set_caption(title: str, icontitle: str = "") -> None:
    get_backend().caption = title


def get_caption() -> tuple[str, str]:
    c = get_backend().caption
    return (c, c)


def set_icon(surface: Surface) -> None:
    get_backend().icon = surface


def iconify() -> bool:
    warnings.warn("iconify() has no effect in ipygame", stacklevel=2)
    return False


def toggle_fullscreen() -> int:
    warnings.warn("toggle_fullscreen() has no effect in ipygame", stacklevel=2)
    return 0


class _VidInfo:
    """Minimal video-info object returned by ``Info()``."""

    def __init__(self, w: int, h: int):
        self.hw = 0
        self.wm = 1
        self.video_mem = 0
        self.bitsize = 32
        self.bytesize = 4
        self.masks = (0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF)
        self.shifts = (24, 16, 8, 0)
        self.losses = (0, 0, 0, 0)
        self.current_w = w
        self.current_h = h

    def __repr__(self) -> str:
        return (f"<VideoInfo(current_w={self.current_w}, "
                f"current_h={self.current_h})>")


def Info() -> _VidInfo:
    b = get_backend()
    if b.display_surface is not None:
        return _VidInfo(*b.display_surface.get_size())
    return _VidInfo(0, 0)


def get_driver() -> str:
    return "ipycanvas"


def get_window_size() -> tuple[int, int]:
    b = get_backend()
    if b.display_surface is not None:
        return b.display_surface.get_size()
    return (0, 0)
