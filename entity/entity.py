from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class Entity:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.vel_x = 0
        self.vel_y = 0
        self.remove = False

    def update(self): ...
    def draw(self): ...
