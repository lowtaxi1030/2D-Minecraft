from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextes import DrawContext, UpdateContext

import random

import pygame

import config
import tool

from ..living_entity import LivingEntity


class Cow(LivingEntity):

    def __init__(self, x, y):
        super().__init__(pygame.Rect(x, y, config.BLOCK_SIZE * 0.9, config.BLOCK_SIZE * 1.4))

        self.move_direction = 0
        self.move_speed = 2  # blocks per second
        self.ai_timer = random.randint(2, 3)  # 幾秒

    def update(self, context: UpdateContext, dt: float):
        self._update_ai(dt)
        self.vel_x = self.move_direction * self.move_speed
        self.vel_y += self.gravity * dt

        self._update_physics(context, dt)

    def _update_ai(self, dt: float):
        self.ai_timer -= dt

        if self.ai_timer <= 0:
            self.ai_timer = random.randint(2, 3)
            self.move_direction = random.choice([-1, 0, 1])

    def draw(self, context: DrawContext):
        display_rect = self.rect.copy()
        display_rect.x -= context.camera.scroll_x
        display_rect.y -= context.camera.scroll_y
        pygame.draw.rect(context.screen, tool.Colors.BROWN, display_rect)
