"""pygame-compatible event module."""

from __future__ import annotations

import collections
import itertools
from typing import Sequence

from ipygame import constants as _c

__all__ = [
    "Event",
    "pump", "get", "poll", "wait", "peek",
    "clear", "post",
    "event_name", "set_blocked", "set_allowed", "get_blocked",
    "set_grab", "get_grab",
    "custom_type",
]


class Event:
    """Represents a single event, compatible with ``pygame.event.Event``."""

    __slots__ = ("type", "__dict__")

    def __init__(self, event_type: int, attributes: dict | None = None, **kwargs):
        self.type = event_type
        if attributes:
            self.__dict__.update(attributes)
        self.__dict__.update(kwargs)

    @property
    def dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "type"}

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items()
                          if k != "type")
        name = event_name(self.type)
        if attrs:
            return f"<Event({self.type}-{name} {{{attrs}}})>"
        return f"<Event({self.type}-{name} {{}})>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Event):
            return self.type == other.type and self.__dict__ == other.__dict__
        return NotImplemented

    def __bool__(self) -> bool:
        return self.type != _c.NOEVENT


_event_queue: collections.deque[Event] = collections.deque()
_blocked: set[int] = set()
_allowed: set[int] | None = None
_grab: bool = False
_custom_type_counter = itertools.count(_c.USEREVENT + 1)


def pump() -> None:
    """Internal processing — no-op in ipygame (events arrive via callbacks)."""
    pass


def get(eventtype=None, pump: bool = True, exclude=None) -> list[Event]:
    """Get and remove events from the queue.

    *eventtype* can be a single type ``int``, a sequence of types, or
    ``None`` (all events).
    """
    if eventtype is None:
        types = None
    elif isinstance(eventtype, int):
        types = {eventtype}
    else:
        types = set(eventtype)

    if exclude is None:
        excl = set()
    elif isinstance(exclude, int):
        excl = {exclude}
    else:
        excl = set(exclude)

    result: list[Event] = []
    remaining: list[Event] = []
    for ev in _event_queue:
        match = (types is None or ev.type in types) and ev.type not in excl
        if match:
            result.append(ev)
        else:
            remaining.append(ev)
    _event_queue.clear()
    _event_queue.extend(remaining)
    return result


def poll() -> Event:
    """Get a single event from the queue (or ``NOEVENT``)."""
    if _event_queue:
        return _event_queue.popleft()
    return Event(_c.NOEVENT)


def wait(timeout: int = 0) -> Event:
    """Wait for an event.  In Jupyter this just polls (blocking not advisable)."""
    return poll()


def peek(eventtype=None) -> bool:
    """Return ``True`` if there are events of the given type in the queue."""
    if eventtype is None:
        return len(_event_queue) > 0
    if isinstance(eventtype, int):
        return any(ev.type == eventtype for ev in _event_queue)
    types = set(eventtype)
    return any(ev.type in types for ev in _event_queue)


def clear(eventtype=None) -> None:
    """Remove events from the queue."""
    if eventtype is None:
        _event_queue.clear()
    else:
        get(eventtype)


def post(event: Event) -> bool:
    """Place an event on the queue."""
    if event.type in _blocked:
        return False
    _event_queue.append(event)
    return True


def event_name(event_type: int) -> str:
    """Return a human-readable name for *event_type*."""
    _NAMES = {
        _c.NOEVENT: "NoEvent",
        _c.QUIT: "Quit",
        _c.KEYDOWN: "KeyDown",
        _c.KEYUP: "KeyUp",
        _c.MOUSEMOTION: "MouseMotion",
        _c.MOUSEBUTTONDOWN: "MouseButtonDown",
        _c.MOUSEBUTTONUP: "MouseButtonUp",
        _c.MOUSEWHEEL: "MouseWheel",
        _c.TEXTINPUT: "TextInput",
        _c.TEXTEDITING: "TextEditing",
        _c.VIDEORESIZE: "VideoResize",
        _c.VIDEOEXPOSE: "VideoExpose",
        _c.USEREVENT: "UserEvent",
        _c.FINGERDOWN: "FingerDown",
        _c.FINGERUP: "FingerUp",
        _c.FINGERMOTION: "FingerMotion",
        _c.DROPFILE: "DropFile",
    }
    return _NAMES.get(event_type, f"Unknown({event_type})")


def set_blocked(event_type) -> None:
    global _allowed
    _allowed = None
    if event_type is None:
        _blocked.clear()
    elif isinstance(event_type, int):
        _blocked.add(event_type)
    else:
        _blocked.update(event_type)


def set_allowed(event_type) -> None:
    if event_type is None:
        _blocked.clear()
    elif isinstance(event_type, int):
        _blocked.discard(event_type)
    else:
        for t in event_type:
            _blocked.discard(t)


def get_blocked(event_type: int) -> bool:
    return event_type in _blocked


def set_grab(grab: bool) -> None:
    global _grab
    _grab = grab


def get_grab() -> bool:
    return _grab


def custom_type() -> int:
    """Allocate and return a unique event type id."""
    return next(_custom_type_counter)


_JS_KEY_MAP: dict[str, int] = {
    "Backspace": _c.K_BACKSPACE,
    "Tab": _c.K_TAB,
    "Enter": _c.K_RETURN,
    "Escape": _c.K_ESCAPE,
    " ": _c.K_SPACE,
    "ArrowLeft": _c.K_LEFT,
    "ArrowRight": _c.K_RIGHT,
    "ArrowUp": _c.K_UP,
    "ArrowDown": _c.K_DOWN,
    "Delete": _c.K_DELETE,
    "Insert": _c.K_INSERT,
    "Home": _c.K_HOME,
    "End": _c.K_END,
    "PageUp": _c.K_PAGEUP,
    "PageDown": _c.K_PAGEDOWN,
    "CapsLock": _c.K_CAPSLOCK,
    "ShiftLeft": _c.K_LSHIFT,
    "ShiftRight": _c.K_RSHIFT,
    "ControlLeft": _c.K_LCTRL,
    "ControlRight": _c.K_RCTRL,
    "AltLeft": _c.K_LALT,
    "AltRight": _c.K_RALT,
    "MetaLeft": _c.K_LGUI,
    "MetaRight": _c.K_RGUI,
    "F1": _c.K_F1, "F2": _c.K_F2, "F3": _c.K_F3, "F4": _c.K_F4,
    "F5": _c.K_F5, "F6": _c.K_F6, "F7": _c.K_F7, "F8": _c.K_F8,
    "F9": _c.K_F9, "F10": _c.K_F10, "F11": _c.K_F11, "F12": _c.K_F12,
}

for _ch in "abcdefghijklmnopqrstuvwxyz":
    _JS_KEY_MAP[_ch] = getattr(_c, f"K_{_ch}")
    _JS_KEY_MAP[_ch.upper()] = getattr(_c, f"K_{_ch}")
for _d in "0123456789":
    _JS_KEY_MAP[_d] = getattr(_c, f"K_{_d}")


def _get_mods_from_event(info: dict) -> int:
    mods = _c.KMOD_NONE
    if info.get("shiftKey"):
        mods |= _c.KMOD_SHIFT
    if info.get("ctrlKey"):
        mods |= _c.KMOD_CTRL
    if info.get("altKey"):
        mods |= _c.KMOD_ALT
    if info.get("metaKey"):
        mods |= _c.KMOD_GUI
    return mods


def _wire_canvas_events(canvas) -> None:
    """Register ipycanvas callbacks that translate to pygame events."""
    from ipygame import key as _key_mod
    from ipygame import mouse as _mouse_mod

    _key_mod._set_key_up_supported(hasattr(canvas, "on_key_up"))

    def _on_mouse_move(x, y):
        ix, iy = int(x), int(y)
        _mouse_mod._update_pos(ix, iy)
        buttons = tuple(_mouse_mod._buttons[:3])
        rel = (_mouse_mod._rel[0], _mouse_mod._rel[1])
        post(Event(_c.MOUSEMOTION,
                    pos=(ix, iy), rel=rel, buttons=buttons))

    def _on_mouse_down(x, y):
        ix, iy = int(x), int(y)
        _mouse_mod._update_pos(ix, iy)
        _mouse_mod._button_down(_c.BUTTON_LEFT)
        post(Event(_c.MOUSEBUTTONDOWN,
                    pos=(ix, iy), button=_c.BUTTON_LEFT))

    def _on_mouse_up(x, y):
        ix, iy = int(x), int(y)
        _mouse_mod._update_pos(ix, iy)
        _mouse_mod._button_up(_c.BUTTON_LEFT)
        post(Event(_c.MOUSEBUTTONUP,
                    pos=(ix, iy), button=_c.BUTTON_LEFT))

    def _on_key_down(key, shift_key, ctrl_key, meta_key):
        k = _JS_KEY_MAP.get(key, _c.K_UNKNOWN)
        mods = _c.KMOD_NONE
        if shift_key:
            mods |= _c.KMOD_SHIFT
        if ctrl_key:
            mods |= _c.KMOD_CTRL
        if meta_key:
            mods |= _c.KMOD_GUI
        _key_mod._key_down(k, mods)
        post(Event(_c.KEYDOWN, key=k, mod=mods,
                    unicode=key if len(key) == 1 else ""))

    def _on_key_up(key, shift_key, ctrl_key, meta_key):
        k = _JS_KEY_MAP.get(key, _c.K_UNKNOWN)
        mods = _c.KMOD_NONE
        if shift_key:
            mods |= _c.KMOD_SHIFT
        if ctrl_key:
            mods |= _c.KMOD_CTRL
        if meta_key:
            mods |= _c.KMOD_GUI
        _key_mod._key_up(k, mods)
        post(Event(_c.KEYUP, key=k, mod=mods))

    canvas.on_mouse_move(_on_mouse_move)
    canvas.on_mouse_down(_on_mouse_down)
    canvas.on_mouse_up(_on_mouse_up)
    canvas.on_key_down(_on_key_down)
    if hasattr(canvas, "on_key_up"):
        canvas.on_key_up(_on_key_up)
