"""pygame-compatible mouse module."""

from __future__ import annotations

from ipygame import constants as _c

__all__ = [
    "get_pressed",
    "get_just_pressed",
    "get_just_released",
    "get_pos",
    "get_rel",
    "set_pos",
    "set_visible",
    "get_visible",
    "get_focused",
    "set_cursor",
    "get_cursor",
    "get_relative_mode",
    "set_relative_mode",
    "Cursor",
]

_pos: list[int] = [0, 0]
_rel: list[int] = [0, 0]
_buttons: list[bool] = [False, False, False, False, False]
_just_pressed: list[bool] = [False, False, False, False, False]
_just_released: list[bool] = [False, False, False, False, False]
_visible: bool = True
_relative_mode: bool = False


class Cursor:
    """Minimal cursor representation (cursors can't be changed in Jupyter)."""

    def __init__(self, *args, **kwargs):
        self._constant = args[0] if args and isinstance(args[0], int) else 0

    def __repr__(self) -> str:
        return f"<Cursor({self._constant})>"


_current_cursor = Cursor()


def get_pressed(num_buttons: int = 3, desktop: bool = False) -> tuple[bool, ...]:
    """Get the state of mouse buttons."""
    if num_buttons == 5:
        return tuple(_buttons)
    return tuple(_buttons[:3])


def get_just_pressed() -> tuple[bool, bool, bool, bool, bool]:
    """Get buttons that were just pressed this frame."""
    result = tuple(_just_pressed)
    for i in range(5):
        _just_pressed[i] = False
    return result  # type: ignore[return-value]


def get_just_released() -> tuple[bool, bool, bool, bool, bool]:
    """Get buttons that were just released this frame."""
    result = tuple(_just_released)
    for i in range(5):
        _just_released[i] = False
    return result  # type: ignore[return-value]


def get_pos(desktop: bool = False) -> tuple[int, int]:
    """Get the current mouse position."""
    return (_pos[0], _pos[1])


def get_rel() -> tuple[int, int]:
    """Get relative mouse movement since last call."""
    r = (_rel[0], _rel[1])
    _rel[0] = _rel[1] = 0
    return r


def set_pos(pos=None, x: int | None = None, y: int | None = None) -> None:
    """Set the mouse position (no-op in Jupyter — cursor is OS-controlled)."""
    if pos is not None:
        _pos[0], _pos[1] = int(pos[0]), int(pos[1])
    elif x is not None and y is not None:
        _pos[0], _pos[1] = int(x), int(y)


def set_visible(value: bool) -> int:
    """Hide or show the mouse cursor."""
    global _visible
    prev = _visible
    _visible = bool(value)
    return int(prev)


def get_visible() -> bool:
    """Get cursor visibility state."""
    return _visible


def get_focused() -> bool:
    """True when the display is receiving mouse input."""
    from ipygame._backend import get_backend
    return get_backend().initialized


def set_cursor(*args, **kwargs) -> None:
    """Set the mouse cursor (no visual effect in Jupyter)."""
    global _current_cursor
    if args and isinstance(args[0], Cursor):
        _current_cursor = args[0]
    else:
        _current_cursor = Cursor(*args, **kwargs)


def get_cursor() -> Cursor:
    """Get the current mouse cursor."""
    return _current_cursor


def get_relative_mode() -> bool:
    """Query relative mouse mode."""
    return _relative_mode


def set_relative_mode(enable: bool) -> None:
    """Enable or disable relative mouse mode."""
    global _relative_mode
    _relative_mode = enable


def _update_pos(x: int, y: int) -> None:
    _rel[0] = x - _pos[0]
    _rel[1] = y - _pos[1]
    _pos[0] = x
    _pos[1] = y


def _button_down(button: int) -> None:
    idx = button - 1
    if 0 <= idx < 5:
        _buttons[idx] = True
        _just_pressed[idx] = True


def _button_up(button: int) -> None:
    idx = button - 1
    if 0 <= idx < 5:
        _buttons[idx] = False
        _just_released[idx] = True
