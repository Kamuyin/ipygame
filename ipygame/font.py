"""pygame-compatible font module."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

from ipygame.color import Color
from ipygame.surface import Surface

__all__ = [
    "init",
    "quit",
    "get_init",
    "get_default_font",
    "get_fonts",
    "match_font",
    "SysFont",
    "Font",
]

_initialized = False
_DEFAULT_FONT_NAME = "freesansbold.ttf"


def init() -> None:
    global _initialized
    _initialized = True


def quit() -> None:
    global _initialized
    _initialized = False


def get_init() -> bool:
    return _initialized


def get_sdl_ttf_version(linked: bool = True):
    return (0, 0, 0)


def get_default_font() -> str:
    return _DEFAULT_FONT_NAME


def _find_system_font_dirs() -> list[Path]:
    """Return platform-specific system font directories."""
    dirs = []
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs.append(Path(windir) / "Fonts")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            dirs.append(Path(localappdata) / "Microsoft" / "Windows" / "Fonts")
    elif sys.platform == "darwin":
        dirs.extend([
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path.home() / "Library" / "Fonts",
        ])
    else:
        dirs.extend([
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".local" / "share" / "fonts",
            Path.home() / ".fonts",
        ])
    return dirs


def get_fonts() -> list[str]:
    """List available system font names (lowercase, no extension)."""
    fonts: set[str] = set()
    for d in _find_system_font_dirs():
        if d.is_dir():
            for f in d.rglob("*"):
                if f.suffix.lower() in (".ttf", ".otf", ".ttc"):
                    fonts.add(f.stem.lower().replace(" ", ""))
    return sorted(fonts)


def match_font(name: str, bold: bool = False, italic: bool = False) -> str | None:
    """Find a specific system font file path."""
    target = name.lower().replace(" ", "")
    for d in _find_system_font_dirs():
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if f.suffix.lower() not in (".ttf", ".otf", ".ttc"):
                continue
            stem = f.stem.lower().replace(" ", "")
            if target in stem:
                if bold and "bold" not in stem:
                    continue
                if italic and ("italic" not in stem and "oblique" not in stem):
                    continue
                return str(f)
    if bold or italic:
        return match_font(name, bold=False, italic=False)
    return None


def SysFont(name: str | Sequence[str] | None, size: int,
            bold: bool = False, italic: bool = False,
            constructor=None) -> "Font":
    """Create a Font from system fonts."""
    if constructor is None:
        constructor = Font

    if name is None:
        return constructor(None, size)

    names = [name] if isinstance(name, str) else list(name)
    for n in names:
        for candidate in n.split(","):
            path = match_font(candidate.strip(), bold=bold, italic=italic)
            if path:
                f = constructor(path, size)
                f._bold = bold
                f._italic = italic
                return f
    return constructor(None, size)


class Font:
    """TrueType font rendering using Pillow."""

    def __init__(self, filename: str | Path | None = None, size: int = 20):
        from PIL import ImageFont

        self._size = max(1, int(size))
        self._bold = False
        self._italic = False
        self._underline = False
        self._strikethrough = False
        self._align = 0  # LEFT

        if filename is None:
            try:
                self._font = ImageFont.truetype("arial.ttf", self._size)
            except (OSError, IOError):
                self._font = ImageFont.load_default()
        else:
            self._font = ImageFont.truetype(str(filename), self._size)

    @property
    def name(self) -> str:
        family = getattr(self._font, "family", None)
        return family if family else "unknown"

    @property
    def style_name(self) -> str:
        style = getattr(self._font, "style", None)
        return style if style else ""

    @property
    def bold(self) -> bool:
        return self._bold

    @bold.setter
    def bold(self, value: bool):
        self._bold = value

    @property
    def italic(self) -> bool:
        return self._italic

    @italic.setter
    def italic(self, value: bool):
        self._italic = value

    @property
    def underline(self) -> bool:
        return self._underline

    @underline.setter
    def underline(self, value: bool):
        self._underline = value

    @property
    def strikethrough(self) -> bool:
        return self._strikethrough

    @strikethrough.setter
    def strikethrough(self, value: bool):
        self._strikethrough = value

    @property
    def point_size(self) -> int:
        return self._size

    @point_size.setter
    def point_size(self, value: int):
        self._size = max(1, int(value))
        from PIL import ImageFont
        try:
            path = self._font.path
            self._font = ImageFont.truetype(path, self._size)
        except (AttributeError, OSError):
            pass

    def set_bold(self, value: bool) -> None:
        self._bold = value

    def get_bold(self) -> bool:
        return self._bold

    def set_italic(self, value: bool) -> None:
        self._italic = value

    def get_italic(self) -> bool:
        return self._italic

    def set_underline(self, value: bool) -> None:
        self._underline = value

    def get_underline(self) -> bool:
        return self._underline

    def set_strikethrough(self, value: bool) -> None:
        self._strikethrough = value

    def get_strikethrough(self) -> bool:
        return self._strikethrough

    def size(self, text: str) -> tuple[int, int]:
        """Get the rendered dimensions of *text*."""
        bbox = self._font.getbbox(text)
        if bbox is None:
            return (0, self.get_height())
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])

    def get_height(self) -> int:
        """Font height in pixels."""
        bbox = self._font.getbbox("Ay")
        if bbox is None:
            return self._size
        return bbox[3] - bbox[1]

    def get_linesize(self) -> int:
        """Line spacing (height + leading)."""
        return int(self.get_height() * 1.2)

    def set_linesize(self, linesize: int) -> None:
        pass

    def get_ascent(self) -> int:
        bbox = self._font.getbbox("A")
        if bbox is None:
            return self._size
        return bbox[3]

    def get_descent(self) -> int:
        bbox = self._font.getbbox("gjpqy")
        if bbox is None:
            return 0
        return max(0, bbox[3] - self.get_height())

    def get_point_size(self) -> int:
        return self._size

    def set_point_size(self, val: int) -> None:
        self.point_size = val

    def set_script(self, script_code: str) -> None:
        pass

    def set_direction(self, direction: int) -> None:
        pass

    def metrics(self, text: str) -> list[tuple[int, int, int, int, int]]:
        """Return per-character metrics: (min_x, max_x, min_y, max_y, advance)."""
        result = []
        for ch in text:
            bbox = self._font.getbbox(ch)
            if bbox is None:
                result.append((0, 0, 0, 0, 0))
            else:
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                result.append((bbox[0], bbox[2], bbox[1], bbox[3], w))
        return result

    def render(self, text: str, antialias: bool = True,
               color=None, bgcolor=None,
               wraplength: int = 0) -> Surface:
        """Render text to a new Surface."""
        from PIL import Image, ImageDraw

        if color is None:
            fg = (255, 255, 255, 255)
        else:
            c = Color(color) if not isinstance(color, Color) else color
            fg = (c.r, c.g, c.b, c.a)

        if not text:
            text = " "
            empty = True
        else:
            empty = False

        if wraplength > 0:
            lines = self._wrap_text(text, wraplength)
            text_to_measure = max(lines, key=lambda l: self.size(l)[0])
            tw, th = self.size(text_to_measure)
            total_h = self.get_linesize() * len(lines)
        else:
            lines = [text]
            tw, th = self.size(text)
            total_h = th

        iw = max(tw + 2, 1)
        ih = max(total_h + 2, 1)

        if bgcolor is not None:
            bg = Color(bgcolor) if not isinstance(bgcolor, Color) else bgcolor
            img = Image.new("RGBA", (iw, ih), (bg.r, bg.g, bg.b, bg.a))
        else:
            img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))

        draw = ImageDraw.Draw(img)

        y_offset = 0
        for line in lines:
            draw.text((0, y_offset), line, font=self._font, fill=fg)
            y_offset += self.get_linesize()

        if self._underline:
            y_line = y_offset - 2
            draw.line([(0, y_line), (iw, y_line)], fill=fg, width=1)

        if self._strikethrough:
            y_line = total_h // 2
            draw.line([(0, y_line), (iw, y_line)], fill=fg, width=1)

        arr = np.array(img, dtype=np.uint8)
        if empty:
            arr = arr[:, :1, :]

        surf = Surface((arr.shape[1], arr.shape[0]))
        surf._pixels[:] = arr
        return surf

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        words = text.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip() if current else word
            tw, _ = self.size(test)
            if tw <= max_width or not current:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines if lines else [""]
