from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from contextes.update_context import UpdateContext

import pygame

import config
import tool

from .entity import Entity


class PhysicalEntity(Entity):
    def __init__(self, rect: pygame.Rect):
        super().__init__(rect)

        self.is_grounded = False
        self.gravity = 40

        self.fall_distance = 0

    def _get_collision_range(self, target_rect: pygame.Rect | None = None):
        if target_rect is None:
            target_rect = self.rect

        center_grid_x = target_rect.centerx // config.BLOCK_SIZE
        center_grid_y = target_rect.centery // config.BLOCK_SIZE

        start_x = center_grid_x - 2
        end_x = center_grid_x + 3

        start_y = max(0, center_grid_y - 2)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 3)

        return start_x, end_x, start_y, end_y

    def _on_horizontal_collision(self, block_rect: pygame.Rect, context: UpdateContext): ...

    def _collide_x(self, context: UpdateContext):
        start_x, end_x, start_y, end_y = self._get_collision_range()
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = context.chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if self._should_ignore_collision(block_name):
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                if self.rect.colliderect(block_rect):
                    # 往右走時撞到（速度大於 0）
                    if self.vel_x > 0:
                        # 把玩家的右側擋在方塊的左側
                        self.vel_x = 0
                        self.rect.right = block_rect.left
                        self._on_horizontal_collision(block_rect, context)

                    # 往左走時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        # 把玩家的左側擋在方塊的右側
                        self.vel_x = 0
                        self.rect.left = block_rect.right
                        self._on_horizontal_collision(block_rect, context)

    def _collide_y(self, context: UpdateContext, dt: float):
        move_y = self.vel_y * config.BLOCK_SIZE * dt
        rem_y = abs(move_y)  # 還剩下多少 Y 距離要走
        sign_y = 1 if move_y > 0 else -1

        while rem_y > 0:
            current_step = min(4, rem_y)  # 每次最多試探 4 像素
            self.rect.y += current_step * sign_y
            rem_y -= current_step
            if sign_y > 0:
                self.fall_distance += current_step
                if any(
                    context.fluid_manager.is_fluid(context.chunk_manager.get_block(x_pos, self.rect.bottom - 5))
                    for x_pos in [self.rect.left, self.rect.centerx, self.rect.right - 1]
                ):
                    self.fall_distance = 0
            else:
                self.fall_distance = 0  # 往上跳時，重置掉落距離

            hit_y = False
            start_x, end_x, start_y, end_y = self._get_collision_range()
            for y_pos in range(start_y, end_y):
                for x_pos in range(start_x, end_x):
                    block_name = context.chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                    if self._should_ignore_collision(block_name):
                        continue

                    block_rect = pygame.Rect(
                        x_pos * config.BLOCK_SIZE,
                        y_pos * config.BLOCK_SIZE,
                        config.BLOCK_SIZE,
                        config.BLOCK_SIZE,
                    )

                    if self.rect.colliderect(block_rect):
                        if sign_y > 0:
                            self.rect.bottom = block_rect.top
                            self.is_grounded = True
                            self._handle_fall_damage()
                        else:
                            self.rect.top = block_rect.bottom

                        self.vel_y = 0  # 速度煞車歸零
                        hit_y = True
                        break
                if hit_y:
                    break

            if hit_y:
                break

    def _should_ignore_collision(self, block_name) -> bool:
        return tool.is_passable(block_name)

    def _can_take_fall_damage(self) -> bool:
        return False

    def _handle_fall_damage(self):
        pass
