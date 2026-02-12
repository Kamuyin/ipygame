"""pygame-compatible display module."""

from __future__ import annotations

import io
import warnings
from typing import Sequence

import numpy as np
from PIL import Image as PILImage

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
    "set_compression",
]

_use_compression: bool = True
_compression_format: str = "PNG"
_image_widget = None


def init() -> None:
    """Initialise the display module."""
    get_backend().mark_init()


def quit() -> None:
    """Uninitialise the display module."""
    global _image_widget
    b = get_backend()
    if b.canvas is not None:
        try:
            b.canvas.clear()
        except Exception:
            pass
    _image_widget = None
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
    global _image_widget
    from ipycanvas import Canvas, hold_canvas
    from ipycanvas.canvas import Image
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

    _placeholder = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    _image_widget = Image(value=_placeholder, format="png")

    from ipygame.event import _wire_canvas_events
    _wire_canvas_events(canvas)

    ipy_display(canvas)

    return surf


def get_surface() -> Surface | None:
    """Return the current display Surface, or ``None``."""
    return get_backend().display_surface


def flip() -> None:
    """Update the full display Surface to the canvas."""
    b = get_backend()
    if b.canvas is None or b.display_surface is None:
        return
    _flush_surface_to_canvas(b.canvas, b.display_surface)


def update(rectangle=None) -> None:
    """Update portions of the display (or the full display if *rectangle* is None)."""
    flip()


def _flush_surface_to_canvas(canvas, surface: Surface) -> None:
    """Transfer the Surface pixel buffer to the ipycanvas Canvas.
    
    If compression is enabled (default), encodes the frame as PNG before
    sending, which dramatically reduces bandwidth usage.
    """
    global _image_widget
    from ipycanvas import hold_canvas

    if _use_compression and _image_widget is not None:
        # Encode frame as PNG
        buf = io.BytesIO()
        pil_img = PILImage.fromarray(surface._pixels, "RGBA")
        pil_img.save(buf, _compression_format, optimize=False)
        _image_widget.value = buf.getvalue()
        
        with hold_canvas(canvas):
            canvas.clear()
            canvas.draw_image(_image_widget, 0, 0)
    else:
        # Raw pixel transfer
        with hold_canvas(canvas):
            canvas.put_image_data(surface._pixels, 0, 0)


def set_compression(enabled: bool = True, format: str = "PNG") -> None:
    """Configure frame compression for network transfer."""
    global _use_compression, _compression_format
    _use_compression = enabled
    if format.upper() in ("PNG", "WEBP"):
        _compression_format = format.upper()


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
