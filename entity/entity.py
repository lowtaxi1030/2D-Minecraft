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

        self.pending_events = []

    def handle_event(self, event, context): ...
    def handle_input(self): ...
    def update(self, context, dt): ...
    def draw(self): ...

    def resolve_stuck(self, *args, **kwagrs): ...

    def destroy(self):
        self.remove = True
