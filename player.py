from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camera import Camera
    from chunk_manager import ChunkManager
    from fluid_manager import FluidManager

# import math

import pygame

import config
import tool


class Player:
    def __init__(self, x, y, chunk_manager: ChunkManager):
        self.chunk_manager = chunk_manager

        self.spawn_x = x * config.BLOCK_SIZE
        self.spawn_y = y * config.BLOCK_SIZE

        # 1. 初始化玩家的形狀與位置 (先用 Rect 方塊代替)
        self.hitbox_width, self.hitbox_height = config.BLOCK_SIZE * 0.6, config.BLOCK_SIZE * 1.8  # 0.6, 1.8
        self.display_width, self.display_height = config.BLOCK_SIZE * 0.875, config.BLOCK_SIZE * 1.75
        self.hitbox = pygame.Rect(x * config.BLOCK_SIZE, y * config.BLOCK_SIZE, self.hitbox_width, self.hitbox_height)
        self.display_rect = pygame.Rect(self.hitbox.x, self.hitbox.y, self.display_width, self.display_height)  # 用於顯示的矩形

        # 2. 物理相關變數
        self.vel_x = 0
        self.vel_y = 0
        self.jump_strength = -10  # 1.2522 blocks per second
        self.is_grounded = False
        self.all_modes = ["survival", "creative", "spectator"]  # , "adventure" 之後再用
        self.mode_index = 0
        self.mode = self.all_modes[self.mode_index]
        self.current_speed = 4.317  # blocks per second
        self.jump_buffer = 0

        self.gravity = 40
        self.walk_speed = 4.317  # blocks per second
        self.cheat_speed = 30  # blocks per second
        self.run_speed = 5.612  # blocks per second  10 or 5.612
        self.flying_speed = 10.0  # blocks per second
        self.flying_run_speed = 20.0  # blocks per second

        self.buoyancy = 37
        self.swim_rise_accel = -20
        self.swim_sink_accel = 20
        self.water_drag = 0.5
        self.swim_speed = 4.3  # blocks per second
        self.swim_accel_x = self.swim_speed / 0.5
        self.is_submerged = False
        self.max_swim_speed = 10.0  # blocks per second

        self.wants_to_rise = False
        self.wants_to_sink = False
        self.wants_to_swim = False

        self.is_stuck = False
        self.is_running = False
        self.auto_jump = True
        self.is_flying = False
        self.is_die = False

        self.desired_swimming = False
        self.is_swimming = False

        self.inv_type = None
        # self.crafting_types = [None, "inventory", "crafting_table"]
        self.hit_box_open = False

        self.just_switched_mode = False

        # 記錄格式： { pygame.K_d: 上次按下的時間(毫秒), pygame.K_a: 上次按下的時間(毫秒) }
        self.last_press_time = {}
        self.DOUBLE_DELAY = 250

        # 背包程式
        # 格式：{"type": "方塊名稱", "count": 數量}
        # 如果格子是空的，就直接用 None 表示
        self.hotbar = [None] * 9  # 熱鍵列，長度為9
        self.inventory = [None] * 27  # 主背包長度為9X3=27

        self.selected_hotbar_index = 0
        # self.held_item = self.hotbar[self.selected_hotbar_index]

        self.facing = 1  # 向右
        self.move_direction = 0
        self.hp = 20
        self.max_hp = 20

        # 掉落傷害
        self.fall_distance = 0  # 玩家從空中掉落的距離，單位是像素
        self.fall_damage = True  # 是否會受到掉落傷害
        self.safe_fall_distance = 3  # 安全掉落距離

        self.pending_drops = []

    @property
    def held_item(self):
        return self.hotbar[self.selected_hotbar_index]

    @held_item.setter
    def held_item(self, value):
        self.hotbar[self.selected_hotbar_index] = value

    def check_double_press(self, key):
        current_time = pygame.time.get_ticks()
        is_double = False

        # 如果這個按鍵之前被按過，就計算時差
        if key in self.last_press_time:
            time_diff = current_time - self.last_press_time[key]
            # 💡 提示：如果時差在 250 毫秒內，且大於 10 毫秒（防止同一幀重複觸發）
            if 10 < time_diff <= self.DOUBLE_DELAY:
                is_double = True

        # 💡 提示：記得更新這一次按下的時間，留給下一次判斷用
        self.last_press_time[key] = current_time
        return is_double

    def handle_event(self, event, keys, fluid_manager: FluidManager):

        if event.type == pygame.KEYDOWN:
            if not self.inv_type:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.selected_hotbar_index = event.key - pygame.K_1

                # for _key in [pygame.K_d, pygame.K_RIGHT, pygame.K_a, pygame.K_LEFT]:
                #     is_double = self.check_double_press(_key)
                #     self._handle_run_and_swim(is_double)

                watched_keys = [pygame.K_d, pygame.K_RIGHT, pygame.K_a, pygame.K_LEFT]
                if event.key in watched_keys:
                    is_double = self.check_double_press(event.key)
                    self._handle_run_and_swim(is_double, fluid_manager)

                if self.mode == "creative":
                    if event.key == pygame.K_SPACE:
                        if self.check_double_press(pygame.K_SPACE):
                            self.is_flying = not self.is_flying
                    if event.key == pygame.K_w:
                        if self.check_double_press(pygame.K_w):
                            self.is_flying = not self.is_flying
                    if event.key == pygame.K_UP:
                        if self.check_double_press(pygame.K_UP):
                            self.is_flying = not self.is_flying

                if self.can_drop_item():
                    if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
                        if event.key == pygame.K_q:
                            return self.drop_selected_item(drop_all=True)
                    elif event.key == pygame.K_q:
                        return self.drop_selected_item()

            if event.key == pygame.K_e:
                if self.inv_type is None:
                    self.inv_type = "inventory"
                else:
                    self.inv_type = None

        if event.type == pygame.KEYUP:
            if event.key in [pygame.K_d, pygame.K_RIGHT, pygame.K_a, pygame.K_LEFT]:
                self.is_running = False

        if event.type == pygame.MOUSEWHEEL:
            self.selected_hotbar_index -= event.y
            if self.selected_hotbar_index >= 9:
                self.selected_hotbar_index = 0

            if self.selected_hotbar_index <= -1:
                self.selected_hotbar_index = 8

    def _handle_run_and_swim(self, is_double: bool, fluid_manager: FluidManager):
        water_surface_y = self._get_water_surface_y(fluid_manager)
        if self.is_submerged and water_surface_y is not None and self.hitbox.top > water_surface_y:
            self.wants_to_swim = is_double
            self.is_running = False
        else:
            self.is_running = is_double
            self.wants_to_swim = False

    def handle_input(self):
        """處理鍵盤輸入（左右移動、跳躍）"""

        keys = pygame.key.get_pressed()
        if not self.inv_type:
            if self.mode == "spectator" or self.is_flying:
                self.vel_x = 0
                self.vel_y = 0

                # X 軸：左右控制
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.vel_x -= self.flying_run_speed if self.is_running else self.flying_speed  # self.cheat_speed  # 往左是負
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.vel_x += self.flying_run_speed if self.is_running else self.flying_speed  # self.cheat_speed  # 往右是正

                # Y 軸：上下自由飛行
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.vel_y -= self.flying_run_speed if self.is_running else self.flying_speed  # 往上飛是負（對抗重力）
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.vel_y += self.flying_run_speed if self.is_running else self.flying_speed  # 往下飛是正
            elif self.mode != "spectator":
                if not self.is_submerged:
                    self.vel_x = 0

                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    if self.is_flying:
                        self.vel_x = -self.flying_speed
                    elif self.is_submerged:
                        self.move_direction = -1  # 只記錄意圖，不碰vel_x
                    else:
                        self.vel_x = -self.current_speed
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    if self.is_flying:
                        self.vel_x = self.flying_speed
                    elif self.is_submerged:
                        self.move_direction = 1  # 只記錄意圖，不碰vel_x
                    else:
                        self.vel_x = self.current_speed
                elif self.is_submerged:
                    self.move_direction = 0  # 泡水時沒按鍵，意圖歸零(讓update()去逐漸減速，不是瞬間停)
                if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
                    if self.is_grounded and not self.is_submerged:
                        if not self.is_flying:
                            self.vel_y = self.jump_strength
                            self.is_grounded = False
                    if self.is_submerged:
                        self.wants_to_rise = True
                else:
                    self.wants_to_rise = False

                if self.is_submerged and (keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    self.wants_to_sink = True
                else:
                    self.wants_to_sink = False

        else:
            self.vel_x = 0

    def _try_auto_jump(self, block_rect):

        if self.is_submerged or self.is_flying:
            return

        if self.auto_jump and self.is_grounded and not self.is_flying:
            height_difference = self.hitbox.bottom - block_rect.top

            head_grid_x = int(self.hitbox.centerx // config.BLOCK_SIZE)  #       ----之後這段可以做成----
            head_grid_y = int((self.hitbox.top - config.BLOCK_SIZE) // config.BLOCK_SIZE)

            head_grid_y = tool.clamp(0, config.MAP_HEIGHT - 1, head_grid_y)  # _get_head_grid()
            head_grid_x = head_grid_x  #                                       ------------------------

            is_ceiling_clear = self.chunk_manager.get_block(head_grid_x, head_grid_y) == "air"

            # 💡 關鍵：高度差要在 1.5 格內，【並且】頭頂必須是空的才能跳！
            if (0 < height_difference <= config.BLOCK_SIZE * 1.5) and is_ceiling_clear:
                self.vel_y = self.jump_strength
                self.is_grounded = False
            else:
                self.is_running = False

    def _is_submerged(self, x_pos: int, fluid_manager: FluidManager):
        """
        x_pos: 玩家的 x 座標 (像素)
        """
        # 計算玩家中心點的格子座標
        center_grid_x = x_pos // config.BLOCK_SIZE
        bottom_grid_y = tool.clamp(0, config.MAP_HEIGHT - 1, (self.hitbox.bottom - 1) // config.BLOCK_SIZE)

        # 取得玩家中心點所在的方塊名稱
        block_name = self.chunk_manager.get_block(center_grid_x * config.BLOCK_SIZE, bottom_grid_y * config.BLOCK_SIZE)

        # 判斷該方塊是否為水或熔岩
        return fluid_manager.is_fluid(block_name)

    def _get_water_surface_y(self, fluid_manager: FluidManager):
        # 玩家目前的格子座標
        grid_x = self.hitbox.centerx // config.BLOCK_SIZE
        grid_y = self.hitbox.centery // config.BLOCK_SIZE

        # 從玩家位置往上找，直到不是水為止
        while grid_y > 0:
            block_name = self.chunk_manager.get_block(grid_x * config.BLOCK_SIZE, grid_y * config.BLOCK_SIZE)
            if not fluid_manager.is_fluid(block_name):
                # 上一格就是水面
                return (grid_y + 1) * config.BLOCK_SIZE
            grid_y -= 1

        return None  # 沒找到水面

    # 更新邏輯
    def update(self, mouse_pos: tuple[int, int], dt: int, game_camera: Camera, fluid_manager: FluidManager):

        self.is_submerged = any(
            self._is_submerged(x, fluid_manager) for x in [self.hitbox.left, self.hitbox.centerx, self.hitbox.right - 1]
        )

        # keys = pygame.key.get_pressed()
        # still_moving = keys[pygame.K_a] or keys[pygame.K_d] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]

        self.desired_swimming = self._get_desired_swimming_state(fluid_manager)

        old_bottom = self.hitbox.bottom
        test_rect = self.hitbox.copy()
        test_rect.size = (new_size := self._get_pose_size())
        test_rect.bottom = old_bottom
        if self._can_change_pose(test_rect):
            self.hitbox = self._change_pose(new_size, old_bottom)
        # else:
        #     self.desired_swimming = True

        """處理重力、移動位置、以及與地圖方塊的碰撞偵測"""
        self.current_speed = self.run_speed if self.is_running else self.walk_speed  # self.cheat_speed

        left_x = int(self.hitbox.left // config.BLOCK_SIZE)
        right_x = int((self.hitbox.right - 1) // config.BLOCK_SIZE)
        top_y = tool.clamp(0, config.MAP_HEIGHT - 1, int(self.hitbox.top // config.BLOCK_SIZE))
        bottom_y = tool.clamp(0, config.MAP_HEIGHT - 1, int((self.hitbox.bottom - 1) // config.BLOCK_SIZE))

        self.is_stuck = (
            not tool.is_passable(self.chunk_manager.get_block(left_x * config.BLOCK_SIZE, top_y * config.BLOCK_SIZE))
            or not tool.is_passable(self.chunk_manager.get_block(left_x * config.BLOCK_SIZE, bottom_y * config.BLOCK_SIZE))
            or not tool.is_passable(self.chunk_manager.get_block(right_x * config.BLOCK_SIZE, top_y * config.BLOCK_SIZE))
            or not tool.is_passable(self.chunk_manager.get_block(right_x * config.BLOCK_SIZE, bottom_y * config.BLOCK_SIZE))
        ) and self.mode != "spectator"

        head_stuck = not tool.is_passable(self.chunk_manager.get_block(self.hitbox.centerx, top_y))
        feet_stuck = not tool.is_passable(self.chunk_manager.get_block(self.hitbox.centerx, bottom_y))

        self.is_fully_stuck = head_stuck and feet_stuck

        if self.is_submerged and not self.is_flying:
            self._apply_swim_horizontal_physics(dt)

        self.hitbox.x += self.vel_x * config.BLOCK_SIZE * dt

        if not self.is_fully_stuck:
            self._collide_x(is_swich_mode=self.just_switched_mode)
        # 應用重力
        if self.mode != "spectator" and not self.is_flying:
            if self.is_submerged:
                self._apply_swim_vertical_physics(dt)
            else:
                self.vel_y += self.gravity * dt

        # 預設玩家在空中
        self.is_grounded = False

        self._collide_y(dt, fluid_manager, game_camera)

        screen_player_x = (self.hitbox.centerx - game_camera.scroll_x) * game_camera.zoom
        if mouse_pos[0] < screen_player_x:
            self.facing = -1
        elif mouse_pos[0] > screen_player_x:
            self.facing = 1

        self._update_display_rect()

    def _get_pose_size(self):
        if self.desired_swimming:
            return (self.hitbox_width, self.hitbox_width)
        else:
            return (self.hitbox_width, self.hitbox_height)

    def _get_display_size(self):
        if self.is_swimming:
            return (self.display_height, self.display_width)
        else:
            return (self.display_width, self.display_height)

    def _can_change_pose(self, target_pose_rect: pygame.Rect):
        # 找出 target_pose_rect 覆蓋到的方塊範圍
        start_x, end_x, start_y, end_y = self._get_collision_range(target_pose_rect)

        # 逐一檢查這些方塊
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = self.chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if tool.is_passable(block_name) or self.mode == "spectator":
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                # 如果 target_pose_rect 與方塊有碰撞，就不能改變姿勢
                if target_pose_rect.colliderect(block_rect):
                    return False

        # 全部都沒有碰撞
        return True

    def _change_pose(self, size: tuple[int, int], bottom: int):
        new_rect = pygame.Rect(self.hitbox.x, self.hitbox.y, *size)
        new_rect.bottom = bottom
        self.is_swimming = self.desired_swimming

        return new_rect

    def _apply_swim_horizontal_physics(self, dt):
        if self.move_direction != 0:
            self.vel_x += self.move_direction * self.swim_accel_x * dt
        self.vel_x *= 1 - self.water_drag * dt
        max_speed = self.swim_speed * (1.5 if self.is_swimming else 1.0)
        self.vel_x = tool.clamp(-max_speed, max_speed, self.vel_x)

    def _apply_swim_vertical_physics(self, dt):
        self.vel_y += (self.gravity - self.buoyancy) * dt
        if self.wants_to_rise:
            self.vel_y += self.swim_rise_accel * dt
        if self.wants_to_sink:
            self.vel_y += self.swim_sink_accel * dt
        self.vel_y *= 1 - self.water_drag * dt
        self.vel_y = tool.clamp(-self.max_swim_speed, self.max_swim_speed, self.vel_y)

    def _can_swim(self, fluid_manager: FluidManager):
        water_surface_y = self._get_water_surface_y(fluid_manager)
        return self.wants_to_swim and self.is_submerged and water_surface_y is not None and self.hitbox.top > water_surface_y

    def _get_desired_swimming_state(self, fluid_manager: FluidManager):

        if self.is_flying:
            return False

        if self._can_swim(fluid_manager):
            return True

        if self.is_swimming and self.is_submerged:
            # 保持游泳模式，不要強制站起來
            return True

        return False

    def _get_collision_range(self, target_rect: pygame.Rect = None):
        if target_rect is None:
            target_rect = self.hitbox

        center_grid_x = target_rect.centerx // config.BLOCK_SIZE
        center_grid_y = target_rect.centery // config.BLOCK_SIZE

        start_x = center_grid_x - 2
        end_x = center_grid_x + 3

        start_y = max(0, center_grid_y - 2)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 3)

        return start_x, end_x, start_y, end_y

    def _collide_x(self, is_swich_mode=False):
        # 檢查玩家周圍的方塊
        start_x, end_x, start_y, end_y = self._get_collision_range()
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = self.chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if tool.is_passable(block_name) or self.mode == "spectator":
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                # 如果卡牆了，就不要移動，交給_collide_y處理
                if is_swich_mode and self.is_stuck:
                    self.vel_x = 0

                # 如果 X 移動後撞到了方塊
                if self.hitbox.colliderect(block_rect) and self.mode != "spectator":
                    # 往右走時撞到（速度大於 0）
                    if self.vel_x > 0:
                        # 把玩家的右側擋在方塊的左側
                        self.hitbox.right = block_rect.left
                        self._try_auto_jump(block_rect)
                    # 往左走時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        # 把玩家的左側擋在方塊的右側
                        self.hitbox.left = block_rect.right
                        self._try_auto_jump(block_rect)

    def _collide_y(self, dt, fluid_manager: FluidManager, game_camera: Camera):
        move_y = self.vel_y * config.BLOCK_SIZE * dt
        rem_y = abs(move_y)  # 還剩下多少 Y 距離要走
        sign_y = 1 if move_y > 0 else -1

        self.fall_damage = self.mode == "survival"  # 只有生存模式才會受到掉落傷害

        while rem_y > 0:
            current_step = min(4, rem_y)  # 每次最多試探 4 像素
            self.hitbox.y += current_step * sign_y
            rem_y -= current_step
            if sign_y > 0:
                self.fall_distance += current_step
                if any(
                    fluid_manager.is_fluid(self.chunk_manager.get_block(x_pos, self.hitbox.bottom - 5))
                    for x_pos in [self.hitbox.left, self.hitbox.centerx, self.hitbox.right - 1]
                ):
                    self.fall_distance = 0
            else:
                self.fall_distance = 0  # 往上跳時，重置掉落距離

            hit_y = False
            start_x, end_x, start_y, end_y = self._get_collision_range()
            # print(f"[GROUND HIT]\nvel_y before collision: {self.vel_y}\nmove_y before collision: {move_y}")
            for y_pos in range(start_y, end_y):
                for x_pos in range(start_x, end_x):
                    block_name = self.chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                    if tool.is_passable(block_name) or self.mode == "spectator":
                        continue

                    block_rect = pygame.Rect(
                        x_pos * config.BLOCK_SIZE,
                        y_pos * config.BLOCK_SIZE,
                        config.BLOCK_SIZE,
                        config.BLOCK_SIZE,
                    )

                    if self.hitbox.colliderect(block_rect):
                        if sign_y > 0:
                            self.hitbox.bottom = block_rect.top
                            self.is_grounded = True
                            fallen_blocks = self.fall_distance / config.BLOCK_SIZE
                            if fallen_blocks >= self.safe_fall_distance and self.fall_damage:
                                self.take_damage(damage := int(fallen_blocks) - (self.safe_fall_distance - 1), game_camera)
                                print(f"掉落了 {fallen_blocks:.2f} 格，受到{damage}傷害！")
                            self.fall_distance = 0  # 落地後重置掉落距離

                        else:
                            self.hitbox.top = block_rect.bottom

                        self.vel_y = 0  # 速度煞車歸零
                        # print(f"vel_y after collision: {self.vel_y}")
                        hit_y = True
                        break
                if hit_y:
                    break

            if hit_y:
                break

    def _update_display_rect(self):
        """更新顯示用的矩形位置與大小"""
        self.display_rect.width, self.display_rect.height = self._get_display_size()
        self.display_rect.centerx = self.hitbox.centerx
        self.display_rect.bottom = self.hitbox.bottom

    def draw(self, screen: pygame.Surface, scroll_x, scroll_y):
        """將玩家畫在畫面上 (記得扣除鏡頭捲動位移)"""
        # 計算在螢幕上的實際繪製位置
        render_x = self.display_rect.x - scroll_x
        render_y = self.display_rect.y - scroll_y

        hit_box_rect = pygame.Rect(self.hitbox.x - scroll_x, self.hitbox.y - scroll_y, self.hitbox.width, self.hitbox.height)

        if self.mode == "spectator":
            # 1. 建立一個全新的臨時 Surface，大小跟你的 rect 一樣
            temp_surface = pygame.Surface((self.display_rect.width, self.display_rect.height), pygame.SRCALPHA)

            # 2. 填入顏色與透明度，第四個參數就是 Alpha 值 (0 ~ 255)
            # (0, 128, 255) 是原本的藍色，128 代表 50% 半透明
            temp_surface.fill((*tool.Colors.YELLOW, 128))

            # 3. 把這個半透明的 Surface 畫到螢幕上（記得扣掉鏡頭的捲動偏移 scroll）
            screen.blit(temp_surface, (render_x, render_y))
        else:
            # 生存模式：照舊畫你原本完全不透明的普通方塊
            # 這裡的坐標一樣要記得扣掉你的 scroll 喔！
            pygame.draw.rect(
                screen,
                tool.Colors.YELLOW,
                (render_x, render_y, self.display_rect.width, self.display_rect.height),
            )
            if self.hit_box_open:
                pygame.draw.rect(
                    screen,
                    tool.Colors.RED,
                    hit_box_rect,
                    1,
                )

    """受傷、死亡"""

    def take_damage(self, amount: int, game_camera: Camera):
        game_camera.shake(config.BLOCK_SIZE / 8, 150)
        self.hp = tool.clamp(0, self.max_hp, self.hp - amount)
        if self.hp <= 0:
            self._die()

    def _die(self):
        for item in self.hotbar + self.inventory:
            if item is not None:
                self.pending_drops.append(item)

        self.hotbar = [None] * 9
        self.inventory = [None] * 27

        self.is_die = True
        self.vel_x = 0
        self.vel_y = 0
        self.fall_distance = 0

        config.game_state = "DEATH"

    def _respawn(self):

        self.is_die = False

        self.hp = self.max_hp
        self.hitbox.x = self.spawn_x
        self.hitbox.y = self.spawn_y

        self.vel_x = 0
        self.vel_y = 0

    """外部用函式"""

    def remove_selected_item(self, count: int):
        if self.should_consume_block():
            self.held_item["count"] -= count
            if self.held_item["count"] <= 0:
                self.held_item = None

    def pick_item(self, item_type: str | None):
        if item_type == "air":
            return

        # print("目前手上", self.selected_hotbar_index, self.held_item)

        # 步驟一：先巡一遍 Hotbar，如果有相同的物品，就把指標切換過去
        for i, item in enumerate(self.hotbar):
            if item is not None and item["type"] == item_type:
                self.selected_hotbar_index = i
                return

        # 步驟二：如果 Hotbar 沒有這個物品，到主背包裡找
        for i, item in enumerate(self.inventory):
            if item is not None and item["type"] == item_type:

                # 嘗試把手上的東西放進背包空位
                if self._move_hand_item_to_inventory():
                    # 情況 A：成功把手上物品移入背包（或本來就是空手）
                    # print("拿出", self.inventory[i])
                    self.held_item = self.inventory[i]
                    self.inventory[i] = None
                else:
                    # 情況 B：背包滿了！直接將手上物品與背包內的 A 做「等價交換」！
                    # print(f"背包已滿，直接交換手上的 {self.held_item['type']} 與背包中的 {item_type}")
                    temp = self.held_item
                    self.held_item = self.inventory[i]
                    self.inventory[i] = temp

                return

        # 步驟三：尋找空格
        for i, item in enumerate(self.hotbar):
            if item is None:
                self.selected_hotbar_index = i
                self.held_item = {"type": item_type, "count": 1}
                return

        # 步驟四：這時才逼不得已覆蓋目前選中的這一格。
        self.held_item = {"type": item_type, "count": 1}

    def _move_hand_item_to_inventory(self):
        hand = self.held_item

        if hand is None:
            return True

        # print("搬運", hand)

        for i, item in enumerate(self.inventory):
            if item is None:
                self.inventory[i] = hand
                self.held_item = None
                # print("放到 inventory", i)
                return True

        return False

    """掉落物相關"""

    def give_item(self, item_type: str, count: int, should_modify=True):
        if not should_modify:
            return count

        count = self._try_merge_slots(self.hotbar, item_type, count)
        count = self._try_merge_slots(self.inventory, item_type, count)

        count = self._try_find_empty_slot(self.hotbar, item_type, count)
        count = self._try_find_empty_slot(self.inventory, item_type, count)

        return count

    def drop_selected_item(self, drop_all=False):
        current_item = self.held_item
        if current_item is not None:
            dropped_item = {
                "type": current_item["type"],
                "count": current_item["count"] if drop_all else 1,
            }

            if drop_all:
                self.held_item = None
            else:
                current_item["count"] -= 1
                if current_item["count"] == 0:
                    self.held_item = None

            return dropped_item
        else:
            return None

    def _try_merge_slots(self, slots, item_type: str, count: int):
        for _, item in enumerate(slots):
            if item is not None and item["type"] == item_type and item["count"] < config.MAX_STACK:
                can_place_num = config.MAX_STACK - item["count"]
                put_num = min(count, can_place_num)
                item["count"] += put_num
                count -= put_num

                if count == 0:
                    return count

        return count

    def _try_find_empty_slot(self, slots, item_type, count):
        if count <= 0:
            return 0

        for index, item in enumerate(slots):
            if item is None:
                put_num = min(count, config.MAX_STACK)

                slots[index] = {"type": item_type, "count": put_num}

                count -= put_num

                if count == 0:
                    return 0

        return count

    """各種判定"""

    def will_drop_item_entity(self):
        return self.mode == "survival"

    def can_break_block(self):
        return self.mode != "spectator"

    def can_place_block(self):
        return self.mode != "spectator"

    def can_pickup_item(self, item_type: str) -> bool:
        """判斷玩家是否能撿起指定類型的物品"""
        if self.mode == "spectator":
            return False

        # 1. 檢查快捷列 (hotbar)
        for item in self.hotbar:
            if item is None:
                return True  # 有空位，直接可以撿
            if item["type"] == item_type and item["count"] < 64:
                return True  # 有同類型且未滿 64，可以疊加

        # 2. 檢查背包 (inventory)
        for item in self.inventory:
            if item is None:
                return True  # 有空位，直接可以撿
            if item["type"] == item_type and item["count"] < 64:
                return True  # 有同類型且未滿 64，可以疊加

        return False

    def can_drop_item(self):
        return self.mode != "spectator"

    def should_consume_block(self):
        return self.mode == "survival"

    def can_pick_block(self):
        return self.mode == "creative"
