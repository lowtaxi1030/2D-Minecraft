import pygame

import asset_manager as assets
import config
import tool
from player import Player


class ItemEntity:
    def __init__(self, item_type: str, count: int, x, y, spawn_reason: str):
        """
        直接傳入方塊的左上角座標，至中由本身自行處理
        spawn_reason 可以是：
        "drop"    --玩家按 Q 丟出   <<<目前只有這個
        "break"   --挖方塊掉落      <<<還有這個
        "death"   --玩家死亡掉落
        "mob"     --生物掉落
        "chest"   --箱子噴出
        "command" --指令生成
        """
        self.type = spawn_reason

        self.item_type = item_type
        self.count = count

        self.age = 0

        self.size = config.BLOCK_SIZE * 0.6
        offset = (config.BLOCK_SIZE - self.size) / 2

        self.rect = pygame.Rect(x + offset, y + offset, self.size, self.size)

        self.vel_x = 0
        self.vel_y = 0

        self.gravity = 1
        self.is_grounded = True

        self.image = pygame.transform.scale(assets.img_blocks[item_type], (self.size, self.size))

        self.pickup_delay = 10  # 幾 tick 後才能撿
        self.is_attracting = False
        self.MAX_SPEED = 6

        self.ACCELERATION = 0.35

    def update(self, world_data, player):
        self.age += 1

        if self.is_attracting:
            self._apply_attraction(player)
        else:
            self.vel_y += self.gravity  # 之後這裡改成 _handle_movement()

        center_grid_x = self.rect.centerx // config.BLOCK_SIZE
        center_grid_y = self.rect.centery // config.BLOCK_SIZE

        start_x = max(0, center_grid_x - 3)
        end_x = min(config.MAP_WIDTH, center_grid_x + 4)

        start_y = max(0, center_grid_y - 3)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 4)

        self.is_grounded = False

        self.rect.x += self.vel_x
        self._collide_x(start_x, end_x, start_y, end_y, world_data)

        self.rect.y += self.vel_y
        self._collide_y(start_x, end_x, start_y, end_y, world_data)

    def _handle_movement(self):
        pass
        """
        可以寫：
        if spawn_reason == "drop":
            # 往玩家面前丟
            self.vel_x = ...
            self.vel_y = ...

        elif spawn_reason == "break":
            # 挖方塊時四散
            self.vel_x = random...
            self.vel_y = ...

        elif spawn_reason == "death":
            # 死亡大量噴裝
        """

    def resolve_stuck(self, world_data, new_block_rect, player: Player):
        if not new_block_rect.colliderect(self.rect):
            return

        center_grid_x = self.rect.centerx // config.BLOCK_SIZE
        center_grid_y = self.rect.centery // config.BLOCK_SIZE

        start_x = max(0, center_grid_x - 3)
        end_x = min(config.MAP_WIDTH, center_grid_x + 4)

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

            if not self._is_colliding(world_data, start_x, end_x, start_y, end_y):
                return

        self.rect.x = original_x

        step *= -1

        for _ in range(config.BLOCK_SIZE):
            if not self._is_colliding(world_data, start_x, end_x, start_y, end_y):
                return

        self.rect.x = original_x

        for _ in range(config.BLOCK_SIZE):
            self.rect.y -= 1
            if not self._is_colliding(world_data, start_x, end_x, start_y, end_y):
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

    def _collide_x(self, start_x, end_x, start_y, end_y, world_data):
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = world_data[y_pos][x_pos]
                if block_name == "air":
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

    def _collide_y(self, start_x, end_x, start_y, end_y, world_data):
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = world_data[y_pos][x_pos]
                if block_name == "air":
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

    def draw(self, screen: pygame.Surface, scroll_x, scroll_y):
        draw_rect = self.rect.copy()
        draw_rect.x -= scroll_x
        draw_rect.y -= scroll_y
        if not self.is_attracting:
            float_y = tool.float_offset(self.age, speed=10, offset=-15)
            draw_rect.y += float_y

        screen.blit(self.image, draw_rect.topleft)

    """外部用函式"""

    def try_attract(self, player: Player):
        player_vec = pygame.math.Vector2((player.rect.centerx, player.rect.bottom))
        self_vec = pygame.math.Vector2(self.rect.center)

        self.is_attracting = player.can_pickup_item() and player_vec.distance_to(self_vec) < config.BLOCK_SIZE * 3

    """判斷函式"""

    def _is_colliding(self, world_data, start_x, end_x, start_y, end_y):
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = world_data[y_pos][x_pos]
                if block_name == "air":
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
