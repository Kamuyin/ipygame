"""pygame-compatible time module."""

from __future__ import annotations

import asyncio
import time as _time
import threading
from typing import TYPE_CHECKING

from ipygame._backend import get_backend
from ipygame import constants as _c

if TYPE_CHECKING:
    pass

__all__ = [
    "get_ticks",
    "wait",
    "delay",
    "set_timer",
    "Clock",
]


def get_ticks() -> int:
    """Milliseconds since ``pygame.init()`` was called."""
    backend = get_backend()
    if backend.init_ticks is None:
        return 0
    return int((_time.perf_counter() - backend.init_ticks) * 1000)


def wait(milliseconds: int) -> int:
    """Pause for *milliseconds* ms.  Returns actual wait time."""
    t0 = _time.perf_counter()
    _time.sleep(max(0, milliseconds / 1000.0))
    return int((_time.perf_counter() - t0) * 1000)


def delay(milliseconds: int) -> int:
    """Accurate delay (same as ``wait`` in ipygame)."""
    return wait(milliseconds)


_timers: dict[int, threading.Timer] = {}


def set_timer(event_type: int, millis: int = 0, loops: int = 0) -> None:
    """Repeatedly post *event_type* every *millis* ms.

    Pass ``millis=0`` to cancel an existing timer.
    *loops* is the number of events to post (0 = infinite).
    """
    existing = _timers.pop(event_type, None)
    if existing is not None:
        existing.cancel()

    if millis <= 0:
        return

    from ipygame.event import Event, post

    remaining = {"n": loops if loops > 0 else -1}

    def _fire():
        if remaining["n"] == 0:
            return
        post(Event(event_type))
        if remaining["n"] > 0:
            remaining["n"] -= 1
        if remaining["n"] != 0:
            t = threading.Timer(millis / 1000.0, _fire)
            t.daemon = True
            _timers[event_type] = t
            t.start()

    t = threading.Timer(millis / 1000.0, _fire)
    t.daemon = True
    _timers[event_type] = t
    t.start()


class Clock:
    """Frame-rate tracking and limiting, compatible with ``pygame.time.Clock``."""

    def __init__(self) -> None:
        self._last_tick: float | None = None
        self._dt: float = 0.0
        self._raw_dt: float = 0.0
        self._fps: float = 0.0
        self._fps_count: int = 0
        self._fps_tick: float = 0.0

    def tick(self, framerate: int = 0) -> int:
        """Update the clock.

        If *framerate* > 0 the method will sleep to keep the loop at
        that speed. Returns milliseconds since the last call.
        """
        now = _time.perf_counter()
        if self._last_tick is None:
            self._last_tick = now
            self._fps_tick = now
            return 0

        raw = (now - self._last_tick) * 1000.0
        self._raw_dt = raw

        if framerate > 0:
            target = 1000.0 / framerate
            sleep_ms = target - raw
            if sleep_ms > 1:
                _time.sleep(sleep_ms / 1000.0)
            now = _time.perf_counter()

        self._dt = (now - self._last_tick) * 1000.0
        self._last_tick = now

        # FPS estimation (simple moving average over 1 s)
        self._fps_count += 1
        elapsed = now - self._fps_tick
        if elapsed >= 1.0:
            self._fps = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_tick = now

        return int(self._dt)

    def tick_busy_loop(self, framerate: int = 0) -> int:
        """Like ``tick()`` but uses a busy loop for more accuracy."""
        now = _time.perf_counter()
        if self._last_tick is None:
            self._last_tick = now
            self._fps_tick = now
            return 0

        raw = (now - self._last_tick) * 1000.0
        self._raw_dt = raw

        if framerate > 0:
            target = 1000.0 / framerate
            deadline = self._last_tick + target / 1000.0
            while _time.perf_counter() < deadline:
                pass
            now = _time.perf_counter()

        self._dt = (now - self._last_tick) * 1000.0
        self._last_tick = now

        self._fps_count += 1
        elapsed = now - self._fps_tick
        if elapsed >= 1.0:
            self._fps = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_tick = now

        return int(self._dt)

    def get_time(self) -> int:
        """Milliseconds between the two most recent ``tick()`` calls."""
        return int(self._dt)

    def get_rawtime(self) -> int:
        """Like ``get_time()`` but without sleep compensation."""
        return int(self._raw_dt)

    def get_fps(self) -> float:
        """Compute the clock framerate (calls per second)."""
        return self._fps

    async def tick_async(self, framerate: int = 0) -> int:
        """Async version of ``tick()`` for Jupyter notebooks.

        Uses ``asyncio.sleep()`` instead of ``time.sleep()`` so the
        Jupyter kernel event loop can process widget messages (keyboard,
        mouse, etc.) between frames.
        """
        now = _time.perf_counter()
        if self._last_tick is None:
            self._last_tick = now
            self._fps_tick = now
            await asyncio.sleep(0)
            return 0

        raw = (now - self._last_tick) * 1000.0
        self._raw_dt = raw

        if framerate > 0:
            target = 1000.0 / framerate
            sleep_ms = target - raw
            if sleep_ms > 1:
                await asyncio.sleep(sleep_ms / 1000.0)
            else:
                await asyncio.sleep(0)
        else:
            await asyncio.sleep(0)

        now = _time.perf_counter()
        self._dt = (now - self._last_tick) * 1000.0
        self._last_tick = now

        self._fps_count += 1
        elapsed = now - self._fps_tick
        if elapsed >= 1.0:
            self._fps = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_tick = now

        return int(self._dt)
