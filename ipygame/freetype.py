"""ipygame.freetype stub module."""

from __future__ import annotations

_FREETYPE_AVAILABLE = False


def _not_implemented(*args, **kwargs):
    raise NotImplementedError("ipygame.freetype is not yet implemented")


def init(cache_size=64, resolution=72):
    pass


def quit():
    pass


def get_init():
    return False


def was_init():
    return False


def get_version():
    return (0, 0, 0)


class Font:
    def __init__(self, *args, **kwargs):
        _not_implemented()
