from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ipycanvas import Canvas
    from ipygame.surface import Surface

__all__: list[str] = []


class _Backend:
    """Singleton holding global display / init state."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.canvas: Canvas | None = None
        self.display_surface: Surface | None = None
        self.caption: str = "ipygame window"
        self.icon = None
        self.initialized: bool = False
        self.init_ticks: float = 0.0
        self.quit_flag: bool = False

    def mark_init(self):
        self.initialized = True
        self.init_ticks = time.perf_counter()
        self.quit_flag = False

    def mark_quit(self):
        self.initialized = False
        self.quit_flag = True
        self.canvas = None
        self.display_surface = None


_backend = _Backend()


def get_backend() -> _Backend:
    return _backend
