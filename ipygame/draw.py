"""pygame-compatible drawing functions."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from ipygame.rect import Rect
from ipygame.surface import Surface, _color_to_rgba

__all__ = [
    "rect", "circle", "ellipse", "arc",
    "line", "lines", "aaline", "aalines",
    "polygon",
]


def _clip_rect(surface: Surface, area: Rect) -> Rect:
    """Clip *area* to both the surface bounds and its clip region."""
    r = area.clip(Rect(0, 0, surface.width, surface.height))
    clip = surface.get_clip()
    return r.clip(clip)


def _set_pixel(pixels: np.ndarray, x: int, y: int, rgba, h: int, w: int):
    """Safely set a single pixel (bounds-checked)."""
    if 0 <= x < w and 0 <= y < h:
        pixels[y, x] = rgba


def rect(
    surface: Surface,
    color,
    rect_arg,
    width: int = 0,
    border_radius: int = -1,
    border_top_left_radius: int = -1,
    border_top_right_radius: int = -1,
    border_bottom_left_radius: int = -1,
    border_bottom_right_radius: int = -1,
) -> Rect:
    """Draw a rectangle on *surface*."""
    rgba = _color_to_rgba(color)
    r = Rect(rect_arg)
    area = _clip_rect(surface, r)
    if area.w <= 0 or area.h <= 0:
        return area

    px = surface._pixels
    if width == 0:
        px[area.y:area.y + area.h, area.x:area.x + area.w] = rgba
    else:
        w = min(width, r.w // 2, r.h // 2)
        t = _clip_rect(surface, Rect(r.x, r.y, r.w, w))
        if t.w > 0 and t.h > 0:
            px[t.y:t.y + t.h, t.x:t.x + t.w] = rgba
        t = _clip_rect(surface, Rect(r.x, r.y + r.h - w, r.w, w))
        if t.w > 0 and t.h > 0:
            px[t.y:t.y + t.h, t.x:t.x + t.w] = rgba
        t = _clip_rect(surface, Rect(r.x, r.y + w, w, r.h - 2 * w))
        if t.w > 0 and t.h > 0:
            px[t.y:t.y + t.h, t.x:t.x + t.w] = rgba
        t = _clip_rect(surface, Rect(r.x + r.w - w, r.y + w, w, r.h - 2 * w))
        if t.w > 0 and t.h > 0:
            px[t.y:t.y + t.h, t.x:t.x + t.w] = rgba

    return area


def circle(
    surface: Surface,
    color,
    center,
    radius: int,
    width: int = 0,
    draw_top_right: bool | None = None,
    draw_top_left: bool | None = None,
    draw_bottom_left: bool | None = None,
    draw_bottom_right: bool | None = None,
) -> Rect:
    """Draw a circle on *surface*."""
    rgba = _color_to_rgba(color)
    cx, cy = int(center[0]), int(center[1])
    r = int(radius)
    if r < 0:
        raise ValueError("radius must be non-negative")

    px = surface._pixels
    h, w = px.shape[:2]

    bounding = Rect(cx - r, cy - r, 2 * r + 1, 2 * r + 1)

    if width == 0:
        clip = _clip_rect(surface, bounding)
        if clip.w <= 0 or clip.h <= 0:
            return clip
        yy, xx = np.ogrid[clip.y:clip.y + clip.h, clip.x:clip.x + clip.w]
        dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
        mask = dist_sq <= r * r
        px[clip.y:clip.y + clip.h, clip.x:clip.x + clip.w][mask] = rgba
    else:
        _draw_circle_outline(px, cx, cy, r, width, rgba, h, w)

    return _clip_rect(surface, bounding)


def _draw_circle_outline(px, cx, cy, r, width, rgba, h, w):
    """Midpoint circle algorithm with thickness."""
    for t in range(width):
        cr = r - t
        if cr < 0:
            break
        x, y = 0, cr
        d = 1 - cr
        while x <= y:
            for sx, sy in [(x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)]:
                _set_pixel(px, cx + sx, cy + sy, rgba, h, w)
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1


def ellipse(
    surface: Surface,
    color,
    rect_arg,
    width: int = 0,
) -> Rect:
    """Draw an ellipse inside *rect_arg*."""
    rgba = _color_to_rgba(color)
    r = Rect(rect_arg)
    clip = _clip_rect(surface, r)
    if clip.w <= 0 or clip.h <= 0:
        return clip

    px = surface._pixels
    cx = r.x + r.w / 2.0
    cy = r.y + r.h / 2.0
    rx = r.w / 2.0
    ry = r.h / 2.0

    if rx == 0 or ry == 0:
        return clip

    if width == 0:
        yy, xx = np.ogrid[clip.y:clip.y + clip.h, clip.x:clip.x + clip.w]
        dist = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        mask = dist <= 1.0
        px[clip.y:clip.y + clip.h, clip.x:clip.x + clip.w][mask] = rgba
    else:
        for t in range(width):
            _draw_ellipse_outline(px, cx, cy, max(0, rx - t), max(0, ry - t),
                                   rgba, px.shape[0], px.shape[1])
    return clip


def _draw_ellipse_outline(px, cx, cy, rx, ry, rgba, h, w):
    if rx <= 0 or ry <= 0:
        return
    steps = max(int(2 * math.pi * max(rx, ry)), 60)
    for i in range(steps):
        angle = 2 * math.pi * i / steps
        x = int(round(cx + rx * math.cos(angle)))
        y = int(round(cy + ry * math.sin(angle)))
        _set_pixel(px, x, y, rgba, h, w)


def arc(
    surface: Surface,
    color,
    rect_arg,
    start_angle: float,
    stop_angle: float,
    width: int = 1,
) -> Rect:
    """Draw an arc (portion of an ellipse outline)."""
    rgba = _color_to_rgba(color)
    r = Rect(rect_arg)
    clip = _clip_rect(surface, r)
    if clip.w <= 0 or clip.h <= 0:
        return clip

    px = surface._pixels
    h, w = px.shape[:2]
    cx = r.x + r.w / 2.0
    cy = r.y + r.h / 2.0
    rx = r.w / 2.0
    ry = r.h / 2.0

    if rx <= 0 or ry <= 0:
        return clip

    while stop_angle < start_angle:
        stop_angle += 2 * math.pi

    for t in range(max(1, width)):
        crx = max(0, rx - t)
        cry = max(0, ry - t)
        if crx <= 0 or cry <= 0:
            break
        steps = max(int((stop_angle - start_angle) * max(crx, cry)), 30)
        for i in range(steps + 1):
            angle = start_angle + (stop_angle - start_angle) * i / steps
            x = int(round(cx + crx * math.cos(angle)))
            y = int(round(cy - cry * math.sin(angle)))
            _set_pixel(px, x, y, rgba, h, w)

    return clip


def line(
    surface: Surface,
    color,
    start_pos,
    end_pos,
    width: int = 1,
) -> Rect:
    """Draw a straight line."""
    rgba = _color_to_rgba(color)
    x0, y0 = int(start_pos[0]), int(start_pos[1])
    x1, y1 = int(end_pos[0]), int(end_pos[1])
    px = surface._pixels
    h, w = px.shape[:2]

    if width <= 1:
        _bresenham(px, x0, y0, x1, y1, rgba, h, w)
    else:
        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy)
        if length == 0:
            _set_pixel(px, x0, y0, rgba, h, w)
        else:
            nx = -dy / length
            ny = dx / length
            for i in range(-(width // 2), width - width // 2):
                ox = round(nx * i)
                oy = round(ny * i)
                _bresenham(px, x0 + ox, y0 + oy, x1 + ox, y1 + oy, rgba, h, w)

    bx = min(x0, x1) - width
    by = min(y0, y1) - width
    bw = abs(x1 - x0) + 2 * width
    bh = abs(y1 - y0) + 2 * width
    return _clip_rect(surface, Rect(bx, by, bw, bh))


def _bresenham(px, x0, y0, x1, y1, rgba, h, w):
    """Bresenham's line algorithm."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _set_pixel(px, x0, y0, rgba, h, w)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def lines(
    surface: Surface,
    color,
    closed: bool,
    points: Sequence,
    width: int = 1,
) -> Rect:
    """Draw multiple connected lines."""
    if len(points) < 2:
        raise ValueError("points must contain at least 2 points")
    rgba = _color_to_rgba(color)
    rects = []
    for i in range(len(points) - 1):
        rects.append(line(surface, rgba, points[i], points[i + 1], width))
    if closed and len(points) > 2:
        rects.append(line(surface, rgba, points[-1], points[0], width))
    result = rects[0]
    for r in rects[1:]:
        result = result.union(r)
    return result


def aaline(
    surface: Surface,
    color,
    start_pos,
    end_pos,
) -> Rect:
    """Draw an anti-aliased line (Wu's algorithm)."""
    rgba = _color_to_rgba(color)
    x0, y0 = float(start_pos[0]), float(start_pos[1])
    x1, y1 = float(end_pos[0]), float(end_pos[1])
    px = surface._pixels
    h, w = px.shape[:2]

    _wu_line(px, x0, y0, x1, y1, rgba, h, w)

    bx = int(min(x0, x1))
    by = int(min(y0, y1))
    bw = int(abs(x1 - x0)) + 2
    bh = int(abs(y1 - y0)) + 2
    return _clip_rect(surface, Rect(bx, by, bw, bh))


def _wu_line(px, x0, y0, x1, y1, rgba, h, w):
    """Xiaolin Wu's line algorithm for anti-aliasing."""
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
    xpxl1 = int(xend)
    ypxl1 = int(math.floor(yend))
    if steep:
        _blend_pixel(px, ypxl1, xpxl1, rgba, 1.0, h, w)
    else:
        _blend_pixel(px, xpxl1, ypxl1, rgba, 1.0, h, w)
    intery = yend + gradient

    xend = round(x1)
    yend = y1 + gradient * (xend - x1)
    xpxl2 = int(xend)
    ypxl2 = int(math.floor(yend))
    if steep:
        _blend_pixel(px, ypxl2, xpxl2, rgba, 1.0, h, w)
    else:
        _blend_pixel(px, xpxl2, ypxl2, rgba, 1.0, h, w)

    for x in range(xpxl1 + 1, xpxl2):
        ipart = int(math.floor(intery))
        fpart = intery - ipart
        if steep:
            _blend_pixel(px, ipart, x, rgba, 1 - fpart, h, w)
            _blend_pixel(px, ipart + 1, x, rgba, fpart, h, w)
        else:
            _blend_pixel(px, x, ipart, rgba, 1 - fpart, h, w)
            _blend_pixel(px, x, ipart + 1, rgba, fpart, h, w)
        intery += gradient


def _blend_pixel(px, x, y, rgba, alpha, h, w):
    """Blend *rgba* into pixel at (x, y) with *alpha* (0-1)."""
    if 0 <= x < w and 0 <= y < h:
        existing = px[y, x].astype(np.float32)
        new = np.array(rgba, dtype=np.float32)
        px[y, x] = (existing * (1 - alpha) + new * alpha).astype(np.uint8)


def aalines(
    surface: Surface,
    color,
    closed: bool,
    points: Sequence,
) -> Rect:
    """Draw multiple connected anti-aliased lines."""
    if len(points) < 2:
        raise ValueError("points must contain at least 2 points")
    rects = []
    for i in range(len(points) - 1):
        rects.append(aaline(surface, color, points[i], points[i + 1]))
    if closed and len(points) > 2:
        rects.append(aaline(surface, color, points[-1], points[0]))
    result = rects[0]
    for r in rects[1:]:
        result = result.union(r)
    return result


def polygon(
    surface: Surface,
    color,
    points: Sequence,
    width: int = 0,
) -> Rect:
    """Draw a polygon."""
    if len(points) < 3:
        raise ValueError("polygon requires at least 3 points")
    rgba = _color_to_rgba(color)
    pts = [(int(p[0]), int(p[1])) for p in points]

    if width == 0:
        _fill_polygon(surface._pixels, pts, rgba)
    else:
        lines(surface, rgba, True, pts, width)

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return _clip_rect(surface, Rect(min(xs), min(ys),
                                     max(xs) - min(xs) + 1,
                                     max(ys) - min(ys) + 1))


def _fill_polygon(px, pts, rgba):
    """Scanline polygon fill."""
    h, w = px.shape[:2]
    ys = [p[1] for p in pts]
    ymin = max(0, min(ys))
    ymax = min(h - 1, max(ys))

    n = len(pts)
    for y in range(ymin, ymax + 1):
        intersections = []
        for i in range(n):
            j = (i + 1) % n
            y0, y1 = pts[i][1], pts[j][1]
            x0, x1 = pts[i][0], pts[j][0]
            if y0 == y1:
                continue
            if y0 > y1:
                x0, x1 = x1, x0
                y0, y1 = y1, y0
            if y0 <= y < y1:
                x_int = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                intersections.append(x_int)
        intersections.sort()
        for k in range(0, len(intersections) - 1, 2):
            x_start = max(0, int(math.ceil(intersections[k])))
            x_end = min(w - 1, int(math.floor(intersections[k + 1])))
            if x_start <= x_end:
                px[y, x_start:x_end + 1] = rgba
