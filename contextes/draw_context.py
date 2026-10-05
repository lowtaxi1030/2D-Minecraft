from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from camera import Camera


class DrawContext:

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
    ):
        self.screen = screen
        self.camera = camera
