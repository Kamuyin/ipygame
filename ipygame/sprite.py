"""ipygame.sprite module."""

from __future__ import annotations

from typing import Iterable, Sequence

from ipygame.rect import Rect
from ipygame.surface import Surface


class Sprite:
    """Minimal pygame-compatible Sprite."""

    def __init__(self, *groups: "Group") -> None:
        self.image: Surface | None = None
        self.rect: Rect | None = None
        self.__groups: set[Group] = set()
        for g in groups:
            g.add(self)

    def add(self, *groups: "Group") -> None:
        for g in groups:
            if g not in self.__groups:
                self.__groups.add(g)
                g.add(self)

    def remove(self, *groups: "Group") -> None:
        for g in groups:
            if g in self.__groups:
                self.__groups.discard(g)
                g.remove(self)

    def kill(self) -> None:
        for g in list(self.__groups):
            g.remove(self)
        self.__groups.clear()

    def alive(self) -> bool:
        return len(self.__groups) > 0

    def groups(self) -> list["Group"]:
        return list(self.__groups)

    def update(self, *args, **kwargs) -> None:
        pass


class Group:
    """Minimal pygame-compatible Group (aka RenderPlain)."""

    def __init__(self, *sprites: Sprite) -> None:
        self._sprites: set[Sprite] = set()
        self.add(*sprites)

    def add(self, *sprites: Sprite) -> None:
        for s in sprites:
            if isinstance(s, Sprite):
                if s not in self._sprites:
                    self._sprites.add(s)
                    s.add(self)
            elif hasattr(s, "__iter__"):
                self.add(*s)

    def remove(self, *sprites: Sprite) -> None:
        for s in sprites:
            if isinstance(s, Sprite):
                if s in self._sprites:
                    self._sprites.discard(s)
                    s.remove(self)
            elif hasattr(s, "__iter__"):
                self.remove(*s)

    def has(self, *sprites: Sprite) -> bool:
        return all(s in self._sprites for s in sprites)

    def sprites(self) -> list[Sprite]:
        return list(self._sprites)

    def copy(self) -> "Group":
        return Group(*self._sprites)

    def empty(self) -> None:
        for s in list(self._sprites):
            self.remove(s)

    def update(self, *args, **kwargs) -> None:
        for s in self._sprites:
            s.update(*args, **kwargs)

    def draw(self, surface: Surface) -> list[Rect]:
        rects = []
        for s in self._sprites:
            if s.image is not None and s.rect is not None:
                surface.blit(s.image, s.rect)
                rects.append(s.rect)
        return rects

    def __len__(self) -> int:
        return len(self._sprites)

    def __bool__(self) -> bool:
        return len(self._sprites) > 0

    def __iter__(self):
        return iter(self._sprites)

    def __contains__(self, sprite: Sprite) -> bool:
        return sprite in self._sprites


RenderPlain = Group
RenderClear = Group
GroupSingle = Group


def groupcollide(
    group1: Group,
    group2: Group,
    dokill1: bool,
    dokill2: bool,
    collided=None,
) -> dict[Sprite, list[Sprite]]:
    """Find all sprites that collide between two groups."""
    if collided is None:
        def collided(a, b):
            return a.rect is not None and b.rect is not None and a.rect.colliderect(b.rect)

    result: dict[Sprite, list[Sprite]] = {}
    for s1 in list(group1):
        hits = [s2 for s2 in group2 if collided(s1, s2)]
        if hits:
            result[s1] = hits
            if dokill1:
                s1.kill()
            if dokill2:
                for s2 in hits:
                    s2.kill()
    return result


def spritecollide(
    sprite: Sprite,
    group: Group,
    dokill: bool,
    collided=None,
) -> list[Sprite]:
    """Find sprites in *group* that collide with *sprite*."""
    if collided is None:
        def collided(a, b):
            return a.rect is not None and b.rect is not None and a.rect.colliderect(b.rect)

    hits = [s for s in group if collided(sprite, s)]
    if dokill:
        for s in hits:
            s.kill()
    return hits


def spritecollideany(
    sprite: Sprite,
    group: Group,
    collided=None,
) -> Sprite | None:
    """Like ``spritecollide`` but returns the first hit or ``None``."""
    if collided is None:
        def collided(a, b):
            return a.rect is not None and b.rect is not None and a.rect.colliderect(b.rect)

    for s in group:
        if collided(sprite, s):
            return s
    return None
