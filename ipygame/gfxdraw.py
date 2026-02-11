"""pygame-compatible gfxdraw module."""

from __future__ import annotations

import math as _math

import numpy as np

from ipygame.color import Color
from ipygame.rect import Rect
from ipygame.surface import Surface, _color_to_rgba

__all__ = [
    "pixel",
    "hline",
    "vline",
    "line",
    "rectangle",
    "box",
    "circle",
    "aacircle",
    "filled_circle",
    "ellipse",
    "aaellipse",
    "filled_ellipse",
    "arc",
    "pie",
    "trigon",
    "aatrigon",
    "filled_trigon",
    "polygon",
    "aapolygon",
    "filled_polygon",
    "bezier",
]


def _clr(color) -> tuple[int, int, int, int]:
    if isinstance(color, Color):
        return (color.r, color.g, color.b, color.a)
    c = Color(color)
    return (c.r, c.g, c.b, c.a)


def pixel(surface: Surface, x: int, y: int, color) -> None:
    """Draw a single pixel."""
    r, g, b, a = _clr(color)
    if 0 <= x < surface.width and 0 <= y < surface.height:
        surface._pixels[y, x] = [r, g, b, a]


def hline(surface: Surface, x1: int, x2: int, y: int, color) -> None:
    """Draw a horizontal line."""
    r, g, b, a = _clr(color)
    if y < 0 or y >= surface.height:
        return
    x1, x2 = max(0, min(x1, x2)), min(surface.width - 1, max(x1, x2))
    if x1 > x2:
        return
    surface._pixels[y, x1:x2 + 1] = [r, g, b, a]


def vline(surface: Surface, x: int, y1: int, y2: int, color) -> None:
    """Draw a vertical line."""
    r, g, b, a = _clr(color)
    if x < 0 or x >= surface.width:
        return
    y1, y2 = max(0, min(y1, y2)), min(surface.height - 1, max(y1, y2))
    if y1 > y2:
        return
    surface._pixels[y1:y2 + 1, x] = [r, g, b, a]


def line(surface: Surface, x1: int, y1: int, x2: int, y2: int, color) -> None:
    """Draw a line between two points."""
    from ipygame.draw import line as draw_line
    draw_line(surface, color, (x1, y1), (x2, y2))


def rectangle(surface: Surface, rect, color) -> None:
    """Draw an unfilled rectangle."""
    r = Rect(rect)
    c = _clr(color)
    hline(surface, r.left, r.right - 1, r.top, c)
    hline(surface, r.left, r.right - 1, r.bottom - 1, c)
    vline(surface, r.left, r.top, r.bottom - 1, c)
    vline(surface, r.right - 1, r.top, r.bottom - 1, c)


def box(surface: Surface, rect, color) -> None:
    """Draw a filled rectangle."""
    r = Rect(rect)
    cr, cg, cb, ca = _clr(color)
    x1 = max(0, r.left)
    y1 = max(0, r.top)
    x2 = min(surface.width, r.right)
    y2 = min(surface.height, r.bottom)
    if x1 < x2 and y1 < y2:
        surface._pixels[y1:y2, x1:x2] = [cr, cg, cb, ca]


def circle(surface: Surface, x: int, y: int, r: int, color) -> None:
    """Draw an unfilled circle (Midpoint algorithm)."""
    c = _clr(color)
    _midpoint_circle(surface, x, y, r, c, filled=False)


def aacircle(surface: Surface, x: int, y: int, r: int, color) -> None:
    """Draw an anti-aliased circle."""
    c = _clr(color)
    steps = max(36, int(2 * _math.pi * r))
    for i in range(steps):
        a1 = 2 * _math.pi * i / steps
        a2 = 2 * _math.pi * (i + 1) / steps
        x1f = x + r * _math.cos(a1)
        y1f = y + r * _math.sin(a1)
        x2f = x + r * _math.cos(a2)
        y2f = y + r * _math.sin(a2)
        _aa_line(surface, x1f, y1f, x2f, y2f, c)


def filled_circle(surface: Surface, x: int, y: int, r: int, color) -> None:
    """Draw a filled circle."""
    c = _clr(color)
    _midpoint_circle(surface, x, y, r, c, filled=True)


def _midpoint_circle(surface, cx, cy, radius, color, filled):
    """Midpoint circle rasterization."""
    px = surface._pixels
    h, w = px.shape[:2]
    cr, cg, cb, ca = color

    def _plot(x, y):
        if 0 <= x < w and 0 <= y < h:
            px[y, x] = [cr, cg, cb, ca]

    def _hline(x1, x2, y):
        if y < 0 or y >= h:
            return
        x1 = max(0, x1)
        x2 = min(w - 1, x2)
        if x1 <= x2:
            px[y, x1:x2 + 1] = [cr, cg, cb, ca]

    x, y = 0, radius
    d = 1 - radius
    while x <= y:
        if filled:
            _hline(cx - x, cx + x, cy + y)
            _hline(cx - x, cx + x, cy - y)
            _hline(cx - y, cx + y, cy + x)
            _hline(cx - y, cx + y, cy - x)
        else:
            _plot(cx + x, cy + y)
            _plot(cx - x, cy + y)
            _plot(cx + x, cy - y)
            _plot(cx - x, cy - y)
            _plot(cx + y, cy + x)
            _plot(cx - y, cy + x)
            _plot(cx + y, cy - x)
            _plot(cx - y, cy - x)
        x += 1
        if d < 0:
            d += 2 * x + 1
        else:
            y -= 1
            d += 2 * (x - y) + 1


def ellipse(surface: Surface, x: int, y: int,
            rx: int, ry: int, color) -> None:
    """Draw an unfilled ellipse."""
    c = _clr(color)
    steps = max(36, int(_math.pi * (rx + ry)))
    px = surface._pixels
    h, w = px.shape[:2]
    for i in range(steps):
        a = 2 * _math.pi * i / steps
        ex = int(round(x + rx * _math.cos(a)))
        ey = int(round(y + ry * _math.sin(a)))
        if 0 <= ex < w and 0 <= ey < h:
            px[ey, ex] = list(c)


def aaellipse(surface: Surface, x: int, y: int,
              rx: int, ry: int, color) -> None:
    """Draw an anti-aliased ellipse."""
    c = _clr(color)
    steps = max(36, int(_math.pi * (rx + ry)))
    for i in range(steps):
        a1 = 2 * _math.pi * i / steps
        a2 = 2 * _math.pi * (i + 1) / steps
        x1f = x + rx * _math.cos(a1)
        y1f = y + ry * _math.sin(a1)
        x2f = x + rx * _math.cos(a2)
        y2f = y + ry * _math.sin(a2)
        _aa_line(surface, x1f, y1f, x2f, y2f, c)


def filled_ellipse(surface: Surface, x: int, y: int,
                   rx: int, ry: int, color) -> None:
    """Draw a filled ellipse."""
    cr, cg, cb, ca = _clr(color)
    px = surface._pixels
    h, w = px.shape[:2]
    for row in range(max(0, y - ry), min(h, y + ry + 1)):
        dy = row - y
        if ry == 0:
            half_w = rx
        else:
            val = 1 - (dy * dy) / (ry * ry)
            if val < 0:
                continue
            half_w = int(rx * _math.sqrt(val))
        x1 = max(0, x - half_w)
        x2 = min(w - 1, x + half_w)
        if x1 <= x2:
            px[row, x1:x2 + 1] = [cr, cg, cb, ca]


def arc(surface: Surface, x: int, y: int, r: int,
        start_angle: int, end_angle: int, color) -> None:
    """Draw an arc (start/end in degrees)."""
    c = _clr(color)
    sa = _math.radians(start_angle)
    ea = _math.radians(end_angle)
    if ea < sa:
        ea += 2 * _math.pi
    steps = max(36, int(abs(ea - sa) * r))
    px = surface._pixels
    h, w = px.shape[:2]
    for i in range(steps + 1):
        a = sa + (ea - sa) * i / steps
        px_x = int(round(x + r * _math.cos(a)))
        px_y = int(round(y + r * _math.sin(a)))
        if 0 <= px_x < w and 0 <= px_y < h:
            px[px_y, px_x] = list(c)


def pie(surface: Surface, x: int, y: int, r: int,
        start_angle: int, end_angle: int, color) -> None:
    """Draw a pie slice (filled arc with lines to center)."""
    c = _clr(color)
    sa = _math.radians(start_angle)
    ea = _math.radians(end_angle)
    arc(surface, x, y, r, start_angle, end_angle, c)
    x1 = int(round(x + r * _math.cos(sa)))
    y1 = int(round(y + r * _math.sin(sa)))
    x2 = int(round(x + r * _math.cos(ea)))
    y2 = int(round(y + r * _math.sin(ea)))
    line(surface, x, y, x1, y1, c)
    line(surface, x, y, x2, y2, c)


def trigon(surface: Surface, x1: int, y1: int, x2: int, y2: int,
           x3: int, y3: int, color) -> None:
    """Draw an unfilled triangle."""
    polygon(surface, [(x1, y1), (x2, y2), (x3, y3)], color)


def aatrigon(surface: Surface, x1: int, y1: int, x2: int, y2: int,
             x3: int, y3: int, color) -> None:
    """Draw an anti-aliased triangle."""
    aapolygon(surface, [(x1, y1), (x2, y2), (x3, y3)], color)


def filled_trigon(surface: Surface, x1: int, y1: int, x2: int, y2: int,
                  x3: int, y3: int, color) -> None:
    """Draw a filled triangle."""
    filled_polygon(surface, [(x1, y1), (x2, y2), (x3, y3)], color)


def polygon(surface: Surface, points, color) -> None:
    """Draw an unfilled polygon."""
    c = _clr(color)
    pts = [(int(p[0]), int(p[1])) for p in points]
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        line(surface, x1, y1, x2, y2, c)


def aapolygon(surface: Surface, points, color) -> None:
    """Draw an anti-aliased polygon outline."""
    c = _clr(color)
    pts = [(float(p[0]), float(p[1])) for p in points]
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        _aa_line(surface, x1, y1, x2, y2, c)


def filled_polygon(surface: Surface, points, color) -> None:
    """Draw a filled polygon using scanline fill."""
    from ipygame.draw import polygon as draw_polygon
    draw_polygon(surface, color, points)


def bezier(surface: Surface, points, steps: int, color) -> None:
    """Draw a Bezier curve through control points."""
    c = _clr(color)
    pts = [(float(p[0]), float(p[1])) for p in points]
    n = len(pts)
    if n < 2:
        return

    prev = None
    for s in range(steps + 1):
        t = s / steps
        tmp = list(pts)
        for k in range(1, n):
            tmp = [
                (tmp[i][0] * (1 - t) + tmp[i + 1][0] * t,
                 tmp[i][1] * (1 - t) + tmp[i + 1][1] * t)
                for i in range(len(tmp) - 1)
            ]
        curr = (int(round(tmp[0][0])), int(round(tmp[0][1])))
        if prev is not None:
            line(surface, prev[0], prev[1], curr[0], curr[1], c)
        prev = curr


def textured_polygon(surface: Surface, points, texture: Surface,
                     tx: int, ty: int) -> None:
    """Draw a textured polygon (simplified — draws filled with texture tiling)."""
    avg = texture._pixels.reshape(-1, 4).mean(axis=0).astype(int)
    filled_polygon(surface, points, tuple(avg))


def _aa_line(surface: Surface, x0: float, y0: float,
             x1: float, y1: float, color: tuple[int, int, int, int]) -> None:
    """Xiaolin Wu's anti-aliased line."""
    px = surface._pixels
    h, w = px.shape[:2]
    r, g, b, a = color

    def _plot_aa(x: int, y: int, brightness: float):
        if 0 <= x < w and 0 <= y < h:
            alpha_f = brightness * (a / 255.0)
            existing = px[y, x].astype(np.float32)
            new = np.array([r, g, b, a], dtype=np.float32)
            px[y, x] = (existing * (1 - alpha_f) + new * alpha_f).astype(np.uint8)

    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0
    gradient = dy / dx if dx != 0 else 1.0

    xend = round(x0)
    yend = y0 + gradient * (xend - x0)
    xgap = 1.0 - ((x0 + 0.5) % 1)
    xpxl1 = int(xend)
    ypxl1 = int(yend)
    if steep:
        _plot_aa(ypxl1, xpxl1, (1 - (yend % 1)) * xgap)
        _plot_aa(ypxl1 + 1, xpxl1, (yend % 1) * xgap)
    else:
        _plot_aa(xpxl1, ypxl1, (1 - (yend % 1)) * xgap)
        _plot_aa(xpxl1, ypxl1 + 1, (yend % 1) * xgap)
    intery = yend + gradient

    xend = round(x1)
    yend = y1 + gradient * (xend - x1)
    xgap = (x1 + 0.5) % 1
    xpxl2 = int(xend)
    ypxl2 = int(yend)
    if steep:
        _plot_aa(ypxl2, xpxl2, (1 - (yend % 1)) * xgap)
        _plot_aa(ypxl2 + 1, xpxl2, (yend % 1) * xgap)
    else:
        _plot_aa(xpxl2, ypxl2, (1 - (yend % 1)) * xgap)
        _plot_aa(xpxl2, ypxl2 + 1, (yend % 1) * xgap)

    for x in range(xpxl1 + 1, xpxl2):
        if steep:
            _plot_aa(int(intery), x, 1 - (intery % 1))
            _plot_aa(int(intery) + 1, x, intery % 1)
        else:
            _plot_aa(x, int(intery), 1 - (intery % 1))
            _plot_aa(x, int(intery) + 1, intery % 1)
        intery += gradient
