from __future__ import annotations

from ipygame.color import Color
from ipygame.rect import Rect, FRect
from ipygame.surface import Surface

from ipygame.constants import *  # noqa: F401,F403

from ipygame import (
    color,
    colordict,
    constants,
    display,
    draw,
    event,
    font,
    gfxdraw,
    image,
    key,
    locals,
    mask,
    math,
    mouse,
    pixelcopy,
    rect,
    surface,
    surfarray,
    time,
    transform,
)

from ipygame import (
    camera,
    cursors,
    freetype,
    ftfont,
    midi,
    sndarray,
    sprite,
)

__version__ = "0.1.0"

from ipygame._backend import get_backend as _get_backend
import time as _stdlib_time


def init() -> tuple[int, int]:
    """Initialize ipygame.  Returns ``(num_successful, num_failed)``."""
    backend = _get_backend()
    backend.mark_init()
    return (6, 0)


def quit() -> None:
    """Uninitialize ipygame."""
    backend = _get_backend()
    backend.mark_quit()


def get_init() -> bool:
    return _get_backend().initialized


class error(RuntimeError):
    pass


from ipygame._hook import (
    install as install_hook,
    uninstall as uninstall_hook,
)  # noqa: E402
