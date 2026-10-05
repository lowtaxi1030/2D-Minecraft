from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chunk_manager import ChunkManager
    from contextes import DrawContext, UpdateContext
    from entity.player import Player
import random

import pygame

import config
import tool

from .entity import Entity


class ItemEntity(Entity):
    def __init__(self, item: dict[str, int], x, y, spawn_reason: str, player: Player, img: pygame.Surface):
        """
        直接傳入方塊的左上角座標，至中由本身自行處理\n
        spawn_reason 可以是：\n
        "drop"     --玩家按 Q 丟出\n
        "inv_drop" --從背包丟出\n
        "break"    --挖方塊掉落\n
        "craft"    --合成出來的東西因背包沒有空間而跑出來\n
        "death"    --玩家死亡掉落\n
        "mob"      --生物掉落\n
        "container"    --箱子、熔爐等噴出\n
        "command"  --指令生成\n
        """
        self.spawn_reason = spawn_reason

        self.item_type = item["type"]
        self.count = item["count"]

        self.age = 0

        self.size = config.BLOCK_SIZE * 0.6
        offset = (config.BLOCK_SIZE - self.size) / 2

        self.rect = pygame.Rect(x + offset, y + offset, self.size, self.size)
        super().__init__(self.rect)

        self.gravity = 1
        self.is_grounded = True

        self.image = pygame.transform.scale(img, (self.size, self.size))

        self.pickup_delay = 30  # 幾 tick 後才能撿
        self.is_attracting = False
        self.MAX_SPEED = 6

        self.ACCELERATION = 0.35

        self.air_friction = 0.98
        self.ground_friction = 0.6

        self._init_spawn_reason(player)

    def _init_spawn_reason(self, player):
        match self.spawn_reason:
            case "drop":
                self._init_drop(player)

            case "inv_drop":
                self._init_inv_drop(player)

            case "break":
                self._init_break()

            case "craft":
                self._init_craft(player)

            case "death":
                self._init_death()

            case "mob":
                self._init_mob()

            case "container":
                self._init_container()

            case "command":
                self._init_command()

    """各種初始化函式"""

    def _init_drop(self, player: Player):
        self.pickup_delay = 60

        self.vel_x = player.facing * 15
        self.vel_y = -4

    def _init_inv_drop(self, player: Player):
        self.pickup_delay = 120

        self.vel_x = player.facing * 25
        self.vel_y = -5

    def _init_break(self):
        speed = random.randint(5, 10)
        self.vel_x = random.choice([speed, -speed])
        self.vel_y = -8
        self.pickup_delay = 10

    def _init_craft(self, player: Player):
        self.pickup_delay = 60

        self.vel_x = player.facing * 15
        self.vel_y = -4

    def _init_death(self):
        self.pickup_delay = 60

        speed = random.randint(5, 18)
        self.vel_x = random.choice([speed, -speed])
        self.vel_y = -4

    def _init_mob(self):
        pass

    def _init_container(self):
        speed = random.randint(2, 5)
        self.vel_x = random.choice([speed, -speed])
        self.vel_y = -3
        self.pickup_delay = 60

    def _init_command(self):
        pass

    def update(self, context: UpdateContext, dt: float):
        self.age += 1

        if self.pickup_delay > 0:
            self.pickup_delay -= 1

        self.is_attracting = self._should_attract(context.player)

        if self.is_attracting:
            self._apply_attraction(context.player)
        else:
            self._handle_movement()

        self.is_grounded = False

        self.rect.x += self.vel_x
        self._collide_x(context.chunk_manager)

        self.rect.y += self.vel_y
        self._collide_y(context.chunk_manager)

    def _should_attract(self, player: Player) -> bool:
        if self.pickup_delay > 0:
            return False

        player_vec = pygame.math.Vector2((player.rect.centerx, player.rect.bottom))

        self_vec = pygame.math.Vector2(self.rect.center)

        return player.can_pickup_item(self.item_type) and player_vec.distance_to(self_vec) < config.BLOCK_SIZE * 2

    def _get_collision_range(self):
        center_grid_x = self.rect.centerx // config.BLOCK_SIZE
        center_grid_y = self.rect.centery // config.BLOCK_SIZE

        start_x = center_grid_x - 3
        end_x = center_grid_x + 4

        start_y = max(0, center_grid_y - 3)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 4)
        return (start_x, end_x, start_y, end_y)

    def _handle_movement(self):
        self.vel_y += self.gravity

        if self.vel_x != 0:
            if self.is_grounded:
                self.vel_x *= self.ground_friction
            else:
                self.vel_x *= self.air_friction

    def resolve_stuck(self, new_block_rect: pygame.Rect, player: Player, chunk_manager: ChunkManager):
        if not new_block_rect.colliderect(self.rect):
            return

        center_grid_x = self.rect.centerx // config.BLOCK_SIZE
        center_grid_y = self.rect.centery // config.BLOCK_SIZE

        start_x = center_grid_x - 3
        end_x = center_grid_x + 4

        start_y = max(0, center_grid_y - 3)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 4)

        original_x = self.rect.x
        original_y = self.rect.y

        step = 1

        for _ in range(config.BLOCK_SIZE):
            center_grid_x = self.rect.centerx // config.BLOCK_SIZE
            center_grid_y = self.rect.centery // config.BLOCK_SIZE

            if self.rect.centerx > player.rect.centerx:
                step = -1

            self.rect.x += step

            if not self._is_colliding(start_x, end_x, start_y, end_y, chunk_manager):
                return

        self.rect.x = original_x

        step *= -1

        for _ in range(config.BLOCK_SIZE):
            if not self._is_colliding(start_x, end_x, start_y, end_y, chunk_manager):
                return

        self.rect.x = original_x

        for _ in range(config.BLOCK_SIZE):
            self.rect.y -= 1
            if not self._is_colliding(start_x, end_x, start_y, end_y, chunk_manager):
                return

        self.rect.y = original_y

    def _apply_attraction(self, player: Player):
        player_pos = pygame.math.Vector2(player.rect.center)
        self_pos = pygame.math.Vector2(self.rect.center)
        direction = player_pos - self_pos

        # 版本1：離玩家越遠，速度越快
        distance = direction.length()

        speed = min(distance * 0.15, self.MAX_SPEED)

        if direction.length() > 0:
            direction.normalize_ip()

        self.vel_x = direction.x * speed
        self.vel_y = direction.y * speed

    def _collide_x(self, chunk_manager: ChunkManager):
        start_x, end_x, start_y, end_y = self._get_collision_range()
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if tool.is_passable(block_name):
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                # 如果 X 移動後撞到了方塊
                if self.rect.colliderect(block_rect):
                    # 往右移動時撞到（速度大於 0）
                    if self.vel_x > 0:
                        self.rect.right = block_rect.left
                    # 往左移動時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        self.rect.left = block_rect.right
                    self.vel_x = 0

    def _collide_y(self, chunk_manager: ChunkManager):
        start_x, end_x, start_y, end_y = self._get_collision_range()
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if tool.is_passable(block_name):
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                if self.rect.colliderect(block_rect):
                    if self.vel_y > 0:
                        self.rect.bottom = block_rect.top
                    if self.vel_y < 0:
                        self.rect.top = block_rect.bottom
                    self.vel_y = 0
                    self.is_grounded = True

    def draw(self, context: DrawContext):
        draw_rect = self.rect.copy()
        draw_rect.x -= context.camera.scroll_x
        draw_rect.y -= context.camera.scroll_y
        if not self.is_attracting:
            float_y = tool.float_offset(self.age, speed=10, offset=-15)
            draw_rect.y += float_y

        context.screen.blit(self.image, draw_rect.topleft)

    """外部用函式"""

    def pick_up(self):
        self.remove = True

    """判斷函式"""

    def _is_colliding(self, start_x, end_x, start_y, end_y, chunk_manager: ChunkManager):
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = block_name = chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if tool.is_passable(block_name):
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                if self.rect.colliderect(block_rect):
                    return True

        return False
