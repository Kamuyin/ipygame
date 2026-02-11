from __future__ import annotations

import importlib
import sys

_SUBMODULE_MAP = {
    "pygame.camera":     "ipygame.camera",
    "pygame.color":      "ipygame.color",
    "pygame.colordict":  "ipygame.colordict",
    "pygame.constants":  "ipygame.constants",
    "pygame.cursors":    "ipygame.cursors",
    "pygame.display":    "ipygame.display",
    "pygame.draw":       "ipygame.draw",
    "pygame.event":      "ipygame.event",
    "pygame.font":       "ipygame.font",
    "pygame.freetype":   "ipygame.freetype",
    "pygame.ftfont":     "ipygame.ftfont",
    "pygame.gfxdraw":    "ipygame.gfxdraw",
    "pygame.image":      "ipygame.image",
    "pygame.key":        "ipygame.key",
    "pygame.locals":     "ipygame.locals",
    "pygame.mask":       "ipygame.mask",
    "pygame.math":       "ipygame.math",
    "pygame.midi":       "ipygame.midi",
    "pygame.mouse":      "ipygame.mouse",
    "pygame.pixelcopy":  "ipygame.pixelcopy",
    "pygame.rect":       "ipygame.rect",
    "pygame.sndarray":   "ipygame.sndarray",
    "pygame.sprite":     "ipygame.sprite",
    "pygame.surface":    "ipygame.surface",
    "pygame.surfarray":  "ipygame.surfarray",
    "pygame.time":       "ipygame.time",
    "pygame.transform":  "ipygame.transform",
}


def install() -> None:
    import ipygame

    sys.modules.setdefault("pygame", ipygame)

    for pygame_name, ipygame_name in _SUBMODULE_MAP.items():
        if pygame_name not in sys.modules:
            try:
                mod = importlib.import_module(ipygame_name)
                sys.modules[pygame_name] = mod
            except ImportError:
                pass


def uninstall() -> None:
    for key in list(sys.modules):
        if key == "pygame" or key.startswith("pygame."):
            if "ipygame" in getattr(sys.modules[key], "__name__", ""):
                del sys.modules[key]
