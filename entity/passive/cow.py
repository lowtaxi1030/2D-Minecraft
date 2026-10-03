from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from chunk_manager import ChunkManager

import random

import config
import tool

from ..living_entity import LivingEntity


class Cow(LivingEntity):

    def __init__(self, x, y, chunk_manager: ChunkManager):
        super().__init__(pygame.Rect(x, y, config.BLOCK_SIZE * 0.9, config.BLOCK_SIZE * 1.4), chunk_manager)

        self.move_direction = 0
        self.ai_timer = random.randint(60, 180)

    def update(self):
        self._update_ai()
        self.vel_x = self.move_direction * 2

        self.rect.x += self.vel_x

    def _update_ai(self):
        self.ai_timer -= 1

        if self.ai_timer <= 0:
            self.ai_timer = random.randint(60, 180)
            self.move_direction = random.choice([-1, 0, 1])

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, tool.Colors.BROWN, self.rect)
