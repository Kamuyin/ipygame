"""pygame-compatible key module."""

from __future__ import annotations

import time as _time

from ipygame import constants as _c

__all__ = [
    "get_focused",
    "get_pressed",
    "get_just_pressed",
    "get_just_released",
    "get_mods",
    "set_mods",
    "set_repeat",
    "get_repeat",
    "name",
    "key_code",
    "start_text_input",
    "stop_text_input",
    "set_text_input_rect",
    "ScancodeWrapper",
]

_pressed: dict[int, bool] = {}
_just_pressed: dict[int, bool] = {}
_just_released: dict[int, bool] = {}
_mods: int = _c.KMOD_NONE
_repeat_delay: int = 0
_repeat_interval: int = 0
_text_input: bool = True
_key_up_supported: bool = True
_down_times: dict[int, float] = {}
_KEYUP_EMULATION_WINDOW_SEC: float = 0.2

_KEY_TO_NAME: dict[int, str] = {}
_NAME_TO_KEY: dict[str, int] = {}

for _attr in dir(_c):
    if _attr.startswith("K_"):
        _val = getattr(_c, _attr)
        _n = _attr[2:].lower()
        _KEY_TO_NAME[_val] = _n
        _NAME_TO_KEY[_n] = _val

_KEY_TO_NAME[_c.K_SPACE] = "space"
_KEY_TO_NAME[_c.K_RETURN] = "return"
_KEY_TO_NAME[_c.K_ESCAPE] = "escape"
_KEY_TO_NAME[_c.K_TAB] = "tab"
_KEY_TO_NAME[_c.K_BACKSPACE] = "backspace"
_KEY_TO_NAME[_c.K_DELETE] = "delete"
_KEY_TO_NAME[_c.K_UP] = "up"
_KEY_TO_NAME[_c.K_DOWN] = "down"
_KEY_TO_NAME[_c.K_LEFT] = "left"
_KEY_TO_NAME[_c.K_RIGHT] = "right"
for _k, _n in list(_KEY_TO_NAME.items()):
    _NAME_TO_KEY[_n] = _k


class ScancodeWrapper(tuple):
    """Tuple subclass returned by ``get_pressed()`` — indexed by key constant."""

    def __new__(cls, mapping: dict[int, bool], size: int = 512):
        data = [False] * size
        for k, v in mapping.items():
            if 0 <= k < size:
                data[k] = v
        obj = super().__new__(cls, data)
        obj._mapping = {int(k): bool(v) for k, v in mapping.items() if int(k) >= 0}
        return obj

    def __getitem__(self, index):
        if isinstance(index, slice):
            return super().__getitem__(index)
        if index < 0:
            return super().__getitem__(index)
        if index >= len(self):
            return self._mapping.get(int(index), False)
        return super().__getitem__(index)


def get_focused() -> bool:
    """True when the display is receiving keyboard input."""
    from ipygame._backend import get_backend
    return get_backend().initialized


def get_pressed() -> ScancodeWrapper:
    """Get the state of all keyboard buttons."""
    if not _key_up_supported:
        now = _time.perf_counter()
        expired = [k for k, t in _down_times.items()
                   if (now - t) > _KEYUP_EMULATION_WINDOW_SEC]
        for k in expired:
            _pressed[k] = False
            _down_times.pop(k, None)
    return ScancodeWrapper(_pressed)


def get_just_pressed() -> ScancodeWrapper:
    """Get keys that were just pressed this frame."""
    wrapper = ScancodeWrapper(_just_pressed)
    _just_pressed.clear()
    return wrapper


def get_just_released() -> ScancodeWrapper:
    """Get keys that were just released this frame."""
    wrapper = ScancodeWrapper(_just_released)
    _just_released.clear()
    return wrapper


def get_mods() -> int:
    """Get the state of modifier keys."""
    return _mods


def set_mods(mods: int) -> None:
    """Set the state of modifier keys."""
    global _mods
    _mods = mods


def set_repeat(delay: int = 0, interval: int = 0) -> None:
    """Control how held keys are repeated."""
    global _repeat_delay, _repeat_interval
    _repeat_delay = delay
    _repeat_interval = interval


def get_repeat() -> tuple[int, int]:
    """Get the repeat delay and interval."""
    return (_repeat_delay, _repeat_interval)


def name(key: int, use_compat: bool = True) -> str:
    """Return the descriptive name of a key constant."""
    return _KEY_TO_NAME.get(key, "")


def key_code(name_str: str) -> int:
    """Get the key constant from a descriptive name."""
    n = name_str.lower().strip()
    if n in _NAME_TO_KEY:
        return _NAME_TO_KEY[n]
    raise ValueError(f"unknown key name: {name_str!r}")


def start_text_input() -> None:
    """Start receiving TEXTINPUT events."""
    global _text_input
    _text_input = True


def stop_text_input() -> None:
    """Stop receiving TEXTINPUT events."""
    global _text_input
    _text_input = False


def set_text_input_rect(rect) -> None:
    """Set the IME candidate list rectangle (no-op in ipygame)."""
    pass


def _key_down(key: int, mods: int) -> None:
    global _mods
    _pressed[key] = True
    _just_pressed[key] = True
    _mods = mods
    _down_times[key] = _time.perf_counter()


def _key_up(key: int, mods: int) -> None:
    global _mods
    _pressed[key] = False
    _just_released[key] = True
    _mods = mods
    _down_times.pop(key, None)


def _set_key_up_supported(supported: bool) -> None:
    global _key_up_supported
    _key_up_supported = supported
