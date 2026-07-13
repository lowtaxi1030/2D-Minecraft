import pygame

import chunk_manager
import config
import tool


class Player:
    def __init__(self, x, y):
        # 1. 初始化玩家的形狀與位置 (先用 Rect 方塊代替)
        self.rect = pygame.Rect(x, y, config.BLOCK_SIZE * 0.875, config.BLOCK_SIZE * 2 * 0.875)

        # 2. 物理相關變數
        self.vel_x = 0
        self.vel_y = 0
        self.jump_strength = -(config.BLOCK_SIZE / 4.5)
        self.is_grounded = False
        self.all_modes = ["spectator", "creative", "survival"]  # , "survival"
        self.mode_index = 1
        self.mode = self.all_modes[self.mode_index]
        self.current_speed = config.BLOCK_SIZE // 10
        self.jump_buffer = 0

        self.gravity = round(max(0.1, config.BLOCK_SIZE / 55), 2)
        self.player_speed = config.BLOCK_SIZE // 10
        self.player_run_speed = config.BLOCK_SIZE // 5
        self.player_flying_speed = config.BLOCK_SIZE // 4

        self.is_stuck = False
        self.is_running = False
        self.auto_jump = True
        self.is_flying = False
        self.is_open_inv = False

        # 記錄格式： { pygame.K_d: 上次按下的時間(毫秒), pygame.K_a: 上次按下的時間(毫秒) }
        self.last_press_time = {}
        self.DOUBLE_DELAY = 250

        # 背包程式
        # 格式：{"type": "方塊名稱", "count": 數量}
        # 如果格子是空的，就直接用 None 表示
        self.hotbar = [None] * 9  # 熱鍵列，長度為9
        self.inventory = [None] * 27  # 主背包長度為9X3=27
        self.MAX_STACK = 64

        self.selected_hotbar_index = 0

        self.facing = 1  # 向右

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

    def handle_event(self, event, keys):

        if event.type == pygame.KEYDOWN:
            if not self.is_open_inv:
                if event.key == pygame.K_m:
                    self.mode_index = (self.mode_index + 1) % len(self.all_modes)
                    self.mode = self.all_modes[self.mode_index]
                    if self.mode in ["creative", "survival"]:
                        self.vel_x = 0
                        self.vel_y = 0
                    if self.mode == "survival":
                        self.is_flying = False

                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.selected_hotbar_index = event.key - pygame.K_1

                if self.mode != "spectator":
                    if event.key == pygame.K_d:
                        self.is_running = self.check_double_press(pygame.K_d)
                    if event.key == pygame.K_RIGHT:
                        self.is_running = self.check_double_press(pygame.K_RIGHT)
                    if event.key == pygame.K_a:
                        self.is_running = self.check_double_press(pygame.K_a)
                    if event.key == pygame.K_LEFT:
                        self.is_running = self.check_double_press(pygame.K_LEFT)
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
                self.is_open_inv = not self.is_open_inv

        if event.type == pygame.MOUSEWHEEL:
            self.selected_hotbar_index -= event.y
            if self.selected_hotbar_index >= 9:
                self.selected_hotbar_index = 0

            if self.selected_hotbar_index <= -1:
                self.selected_hotbar_index = 8

    def handle_input(self, mouse_pos):
        """處理鍵盤輸入（左右移動、跳躍）"""

        keys = pygame.key.get_pressed()
        if not self.is_open_inv:
            if self.mode == "spectator" or self.is_flying:
                self.vel_x = 0
                self.vel_y = 0

                # X 軸：左右控制
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.vel_x -= self.player_flying_speed  # 往左是負
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.vel_x += self.player_flying_speed  # 往右是正

                # Y 軸：上下自由飛行
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.vel_y -= self.player_flying_speed  # 往上飛是負（對抗重力）
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.vel_y += self.player_flying_speed  # 往下飛是正
            elif self.mode != "spectator":
                self.vel_x = 0

                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.vel_x = -self.player_flying_speed if self.is_flying else -self.current_speed
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.vel_x = self.player_flying_speed if self.is_flying else self.current_speed
                if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.is_grounded:
                    if not self.is_flying:
                        self.vel_y = self.jump_strength
                        self.is_grounded = False
        else:
            self.vel_x = 0

        if mouse_pos[0] < self.rect.centerx:
            self.facing = -1
        elif mouse_pos[0] > self.rect.centerx:
            self.facing = 1

    def _try_auto_jump(self, block_rect):

        if self.auto_jump and self.is_grounded and not self.is_flying:
            height_difference = self.rect.bottom - block_rect.top

            head_grid_x = int(self.rect.centerx // config.BLOCK_SIZE)  #  ----之後這段可以做成----
            head_grid_y = int((self.rect.top - config.BLOCK_SIZE) // config.BLOCK_SIZE)

            head_grid_y = tool.clamp(0, config.MAP_HEIGHT - 1, head_grid_y)  # _get_head_grid()
            head_grid_x = tool.clamp(0, config.MAP_WIDTH - 1, head_grid_x)  #  ------------------------

            is_ceiling_clear = chunk_manager.get_block(head_grid_x, head_grid_y) == "air"

            # 💡 關鍵：高度差要在 1.5 格內，【並且】頭頂必須是空的才能跳！
            if (0 < height_difference <= config.BLOCK_SIZE * 1.5) and is_ceiling_clear:
                self.vel_y = self.jump_strength
                self.is_grounded = False
            else:
                self.is_running = False

    def update(self):
        """處理按鍵問題"""
        if self.is_flying:
            self.is_running = False

        # self.is_running &= not self.is_flying  # (另一種寫法，可以嘗試)

        """處理重力、移動位置、以及與地圖方塊的碰撞偵測"""
        self.current_speed = self.player_run_speed if self.is_running else self.player_speed

        left_x = int(self.rect.left // config.BLOCK_SIZE)
        right_x = int((self.rect.right - 1) // config.BLOCK_SIZE)
        top_y = tool.clamp(0, config.MAP_HEIGHT - 1, int(self.rect.top // config.BLOCK_SIZE))
        bottom_y = tool.clamp(0, config.MAP_HEIGHT - 1, int((self.rect.bottom - 1) // config.BLOCK_SIZE))

        self.is_stuck = (
            chunk_manager.get_block(left_x * config.BLOCK_SIZE, top_y * config.BLOCK_SIZE) != "air"
            or chunk_manager.get_block(left_x * config.BLOCK_SIZE, bottom_y * config.BLOCK_SIZE) != "air"
            or chunk_manager.get_block(right_x * config.BLOCK_SIZE, top_y * config.BLOCK_SIZE) != "air"
            or chunk_manager.get_block(right_x * config.BLOCK_SIZE, bottom_y * config.BLOCK_SIZE) != "air"
        ) and self.mode != "spectator"

        center_grid_x = self.rect.centerx // config.BLOCK_SIZE
        center_grid_y = self.rect.centery // config.BLOCK_SIZE

        start_x = center_grid_x - 2
        end_x = center_grid_x + 3

        start_y = max(0, center_grid_y - 2)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 3)

        self.rect.x += self.vel_x

        self._collide_x(start_x, end_x, start_y, end_y)
        # 應用重力
        if self.mode != "spectator" and not self.is_flying:
            self.vel_y += self.gravity

        # 預設玩家在空中
        self.is_grounded = False

        self._collide_y(start_x, end_x, start_y, end_y)

    def _collide_x(self, start_x, end_x, start_y, end_y):
        # 檢查玩家周圍的方塊
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                if block_name == "air" or self.mode == "spectator":
                    continue

                block_rect = pygame.Rect(
                    x_pos * config.BLOCK_SIZE,
                    y_pos * config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                    config.BLOCK_SIZE,
                )

                # 如果 X 移動後撞到了方塊
                if self.rect.colliderect(block_rect) and self.mode != "spectator":
                    # 往右走時撞到（速度大於 0）
                    if self.vel_x > 0:
                        # 把玩家的右側擋在方塊的左側
                        self.rect.right = block_rect.left
                        self._try_auto_jump(block_rect)
                    # 往左走時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        # 把玩家的左側擋在方塊的右側
                        self.rect.left = block_rect.right
                        self._try_auto_jump(block_rect)

    def _collide_y(self, start_x, end_x, start_y, end_y):
        rem_y = abs(self.vel_y)  # 還剩下多少 Y 距離要走
        sign_y = 1 if self.vel_y > 0 else -1

        # 🎯 參考你最得意的碎步架構
        while rem_y > 0:
            current_step = min(4, rem_y)  # 每次最多試探 4 像素
            self.rect.y += current_step * sign_y
            rem_y -= current_step

            hit_y = False
            for y_pos in range(start_y, end_y):
                for x_pos in range(start_x, end_x):
                    block_name = chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)
                    if block_name == "air" or self.mode == "spectator":
                        continue

                    block_rect = pygame.Rect(
                        x_pos * config.BLOCK_SIZE,
                        y_pos * config.BLOCK_SIZE,
                        config.BLOCK_SIZE,
                        config.BLOCK_SIZE,
                    )

                    if self.rect.colliderect(block_rect):
                        # 🎯 修正：不要用中心點比較，直接用移動方向判斷！
                        if sign_y > 0:  # 往下掉撞到 -> 站在地板上
                            self.rect.bottom = block_rect.top
                            self.is_grounded = True
                        else:  # 往上跳撞到 -> 頭撞到天花板
                            self.rect.top = block_rect.bottom

                        self.vel_y = 0  # 速度煞車歸零
                        hit_y = True
                        break
                if hit_y:
                    break

            if hit_y:
                # 🎯 撞到了就直接完全報廢這幀剩下的碎步，絕對不會過度疊加移動
                break

    def draw(self, screen: pygame.Surface, scroll_x, scroll_y):
        """將玩家畫在畫面上 (記得扣除鏡頭捲動位移)"""
        # 計算在螢幕上的實際繪製位置
        render_x = self.rect.x - scroll_x
        render_y = self.rect.y - scroll_y

        if self.mode == "spectator":
            # 1. 建立一個全新的臨時 Surface，大小跟你的 rect 一樣
            temp_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

            # 2. 填入顏色與透明度，第四個參數就是 Alpha 值 (0 ~ 255)
            # (0, 128, 255) 是原本的藍色，128 代表 50% 半透明
            temp_surface.fill((0, 128, 255, 128))

            # 3. 把這個半透明的 Surface 畫到螢幕上（記得扣掉鏡頭的捲動偏移 scroll）
            screen.blit(temp_surface, (render_x, render_y))
        else:
            # 生存模式：照舊畫你原本完全不透明的普通方塊
            # 這裡的坐標一樣要記得扣掉你的 scroll 喔！
            pygame.draw.rect(
                screen,
                (0, 128, 255),
                (render_x, render_y, self.rect.width, self.rect.height),
            )

    """外部用函式"""

    def remove_selected_item(self, count: int):
        if self.should_consume_block():
            self.hotbar[self.selected_hotbar_index]["count"] -= count
            if self.hotbar[self.selected_hotbar_index]["count"] <= 0:
                self.hotbar[self.selected_hotbar_index] = None

    def pick_item(self, item_type: str):
        # 步驟一：先巡一遍 Hotbar，如果有相同的物品，就把指標切換過去
        for i, item in enumerate(self.hotbar):
            if item is not None and item["type"] == item_type:
                self.selected_hotbar_index = i
                if self.mode == "creative":
                    self.hotbar[self.selected_hotbar_index]["count"] = self.MAX_STACK
                return

        # 步驟二：如果 Hotbar 沒有，改去檢查 Hotbar 有沒有哪一格是空的 (None)。如果有空格，就把物品塞進那個空格，並把指標選過去。
        for i, item in enumerate(self.hotbar):
            if item is None:
                self.hotbar[i] = {"type": item_type, "count": self.MAX_STACK}
                self.selected_hotbar_index = i
                return

        # 步驟三：如果 Hotbar 全滿且都沒有這個物品，把原本格子裡的東西跟主背包做交換
        for i, item in enumerate(self.inventory):
            if item is not None and item["type"] == item_type:
                h_item = self.hotbar[self.selected_hotbar_index]
                self.hotbar[self.selected_hotbar_index] = self.inventory[i]
                self.inventory[i] = h_item
                return

        # 步驟四：這時才逼不得已覆蓋目前選中的這一格。
        self.hotbar[self.selected_hotbar_index] = {"type": item_type, "count": self.MAX_STACK}

    """掉落物相關"""

    def give_item(self, item_type: str, count: int):
        count = self._try_merge_slots(self.hotbar, item_type, count)
        count = self._try_merge_slots(self.inventory, item_type, count)

        count = self._try_find_empty_slot(self.hotbar, item_type, count)
        count = self._try_find_empty_slot(self.inventory, item_type, count)

        return count == 0

    def drop_selected_item(self, drop_all=False):
        current_item = self.hotbar[self.selected_hotbar_index]
        if current_item is not None:
            dropped_item = {
                "type": current_item["type"],
                "count": current_item["count"] if drop_all else 1,
            }

            if drop_all:
                self.hotbar[self.selected_hotbar_index] = None
            else:
                current_item["count"] -= 1
                if current_item["count"] == 0:
                    self.hotbar[self.selected_hotbar_index] = None

            return dropped_item
        else:
            return None

    def _try_merge_slots(self, slots, item_type, count):
        for _, item in enumerate(slots):
            if item is not None and item["type"] == item_type and item["count"] < self.MAX_STACK:
                can_place_num = self.MAX_STACK - item["count"]
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
                put_num = min(count, self.MAX_STACK)

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

    def can_pickup_item(self):
        return self.mode != "spectator"

    def can_drop_item(self):
        return self.mode != "spectator"

    def should_consume_block(self):
        return self.mode == "survival"

    def can_pick_block(self):
        return self.mode == "creative"
