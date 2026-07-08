import pygame

import config
import tool
import ui_obs as ui


class Player:
    def __init__(self, x, y):
        # 1. 初始化玩家的形狀與位置 (先用 Rect 方塊代替)
        self.rect = pygame.Rect(x, y, config.BLOCK_SIZE * 0.875, config.BLOCK_SIZE * 2 * 0.875)

        # 2. 物理相關變數
        self.vel_x = 0
        self.vel_y = 0
        self.jump_strength = -(config.BLOCK_SIZE / (20/3))
        self.is_grounded = False
        self.all_modes = ["spectator", "creative", "survival"]  # , "survival"
        self.mode_index = 1
        self.mode = self.all_modes[self.mode_index]
        self.current_speed = config.PLAYER_SPEED

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

        self.selected_hotbar_index = 0

        # ---- 🧪 測試用：先手動塞一點東西進去，等等開發畫面才看得到 ----
        self.hotbar[0] = {"type": "grass", "count": 64}
        self.hotbar[1] = {"type": "dirt", "count": 64}
        self.hotbar[2] = {"type": "stone", "count": 32}
        self.hotbar[3] = {"type": "iron_ore", "count": 5}
        self.hotbar[4] = {"type": "coal_ore", "count": 10}
        self.hotbar[5] = {"type": "deepslate", "count": 10}

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

    def handle_input(self, evnets):
        """處理鍵盤輸入（左右移動、跳躍）"""
        keys = pygame.key.get_pressed()
        if self.mode == "spectator" or self.is_flying:
            self.vel_x = 0
            self.vel_y = 0

            # X 軸：左右控制
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x -= config.PLAYER_FLYING_SPEED  # 往左是負
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x += config.PLAYER_FLYING_SPEED  # 往右是正

            # Y 軸：上下自由飛行
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel_y -= config.PLAYER_FLYING_SPEED  # 網上飛是負（對抗重力）
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.vel_y += config.PLAYER_FLYING_SPEED  # 往下飛是正
        elif self.mode != "spectator":
            self.vel_x = 0

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -config.PLAYER_FLYING_SPEED if self.is_flying else -self.current_speed
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = config.PLAYER_FLYING_SPEED if self.is_flying else self.current_speed
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.is_grounded:
                if not self.is_flying:
                    self.vel_y = self.jump_strength
                    self.is_grounded = False

        for event in evnets:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.mode_index = (self.mode_index + 1) % len(self.all_modes)
                    self.mode = self.all_modes[self.mode_index]
                    if self.mode in ["creative", "survival"]:
                        self.vel_x = 0
                        self.vel_y = 0
                    if self.mode == "survival":
                        self.is_flying = False
                if event.key == pygame.K_e:
                    self.is_open_inv = not self.is_open_inv

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

            if event.type == pygame.MOUSEWHEEL:
                self.selected_hotbar_index -= event.y
                if self.selected_hotbar_index >= 9:
                    self.selected_hotbar_index = 0

                if self.selected_hotbar_index <= -1:
                    self.selected_hotbar_index = 8

    def update(self, world_data):
        """處理重力、移動位置、以及與地圖方塊的碰撞偵測"""
        self.current_speed = config.PLAYER_RUN_SPEED if self.is_running else config.PLAYER_SPEED

        left_x = tool.clamp(0, config.MAP_WIDTH - 1, int(self.rect.left // config.BLOCK_SIZE))
        right_x = tool.clamp(0, config.MAP_WIDTH - 1, int((self.rect.right - 1) // config.BLOCK_SIZE))
        top_y = tool.clamp(0, config.MAP_HEIGHT - 1, int(self.rect.top // config.BLOCK_SIZE))
        bottom_y = tool.clamp(0, config.MAP_HEIGHT - 1, int((self.rect.bottom - 1) // config.BLOCK_SIZE))

        self.is_stuck = (
            config.world_data[top_y][left_x] != "air"
            or config.world_data[bottom_y][left_x] != "air"
            or config.world_data[top_y][right_x] != "air"
            or config.world_data[bottom_y][right_x] != "air"
        ) and self.mode != "spectator"

        center_grid_x = self.rect.centerx // config.BLOCK_SIZE
        center_grid_y = self.rect.centery // config.BLOCK_SIZE

        start_x = max(0, center_grid_x - 2)
        end_x = min(config.MAP_WIDTH, center_grid_x + 3)

        start_y = max(0, center_grid_y - 2)
        end_y = min(config.MAP_HEIGHT, center_grid_y + 3)

        self.rect.x += self.vel_x

        # 檢查玩家周圍的方塊
        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):
                block_name = world_data[y_pos][x_pos]
                if block_name == "air" or self.mode == "spectator":
                    continue

                block_rect = pygame.Rect(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE, config.BLOCK_SIZE, config.BLOCK_SIZE)

                # 如果 X 移動後撞到了方塊
                if self.rect.colliderect(block_rect) and self.mode != "spectator":
                    # 往右走時撞到（速度大於 0）
                    if self.vel_x > 0:
                        # 把玩家的右側擋在方塊的左側
                        self.rect.right = block_rect.left
                        if self.auto_jump and self.is_grounded and not self.is_flying:
                            height_difference = self.rect.bottom - block_rect.top

                            # 💡 提示 1：算出玩家正頭頂上方 1 格的網格位置
                            # 用玩家中心點的 X 座標除以方塊大小，得知目前在哪一欄
                            head_grid_x = int(self.rect.centerx // config.BLOCK_SIZE)
                            # 用玩家頭頂的 Y 座標減去 1 格的距離，除以方塊大小，得知頭頂上一格在哪一列
                            head_grid_y = int((self.rect.top - config.BLOCK_SIZE) // config.BLOCK_SIZE)

                            # 💡 提示 2：安全防護，確保網格座標在世界地圖內
                            head_grid_y = tool.clamp(0, config.MAP_HEIGHT - 1, head_grid_y)
                            head_grid_x = tool.clamp(0, config.MAP_WIDTH - 1, head_grid_x)

                            # 💡 提示 3：檢查頭頂那一格是不是空的（假設空的叫做 "air"）
                            is_ceiling_clear = world_data[head_grid_y][head_grid_x] == "air"

                            # 💡 關鍵：高度差要在 1.5 格內，【並且】頭頂必須是空的才能跳！
                            if (0 < height_difference <= config.BLOCK_SIZE * 1.5) and is_ceiling_clear:
                                self.vel_y = self.jump_strength
                                self.is_grounded = False
                    # 往左走時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        # 把玩家的左側擋在方塊的右側
                        self.rect.left = block_rect.right
                        if self.auto_jump and self.is_grounded and not self.is_flying:
                            height_difference = self.rect.bottom - block_rect.top

                            # 💡 提示 1：算出玩家正頭頂上方 1 格的網格位置
                            # 用玩家中心點的 X 座標除以方塊大小，得知目前在哪一欄
                            head_grid_x = int(self.rect.centerx // config.BLOCK_SIZE)
                            # 用玩家頭頂的 Y 座標減去 1 格的距離，除以方塊大小，得知頭頂上一格在哪一列
                            head_grid_y = int((self.rect.top - config.BLOCK_SIZE) // config.BLOCK_SIZE)

                            # 💡 提示 2：安全防護，確保網格座標在世界地圖內
                            head_grid_y = tool.clamp(0, config.MAP_HEIGHT - 1, head_grid_y)
                            head_grid_x = tool.clamp(0, config.MAP_WIDTH - 1, head_grid_x)

                            # 💡 提示 3：檢查頭頂那一格是不是空的（假設空的叫做 "air"）
                            is_ceiling_clear = world_data[head_grid_y][head_grid_x] == "air"

                            # 💡 關鍵：高度差要在 1.5 格內，【並且】頭頂必須是空的才能跳！
                            if (0 < height_difference <= config.BLOCK_SIZE * 1.5) and is_ceiling_clear:
                                self.vel_y = self.jump_strength
                                self.is_grounded = False
        # 應用重力
        if self.mode != "spectator" and not self.is_flying:
            self.vel_y += config.GRAVITY

        self.rect.y += self.vel_y

        # 預設玩家在空中
        self.is_grounded = False

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
                    block_name = world_data[y_pos][x_pos]
                    if block_name == "air" or self.mode == "spectator":
                        continue

                    block_rect = pygame.Rect(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE, config.BLOCK_SIZE, config.BLOCK_SIZE)

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
        max_player_x = (config.MAP_WIDTH * config.BLOCK_SIZE) - 35
        self.rect.x = tool.clamp(0, max_player_x, self.rect.x)
        self.rect.y = tool.clamp(None, None, self.rect.y)

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
            pygame.draw.rect(screen, (0, 128, 255), (render_x, render_y, self.rect.width, self.rect.height))
        ui.show_text(
            screen,
            f"X: {self.rect.x // config.BLOCK_SIZE}, Y: {self.rect.y // config.BLOCK_SIZE}",
            tool.Colors.WHITE,
            config.current_width - 150,
            config.current_height - 30,
            size=15,
            alpha=160,
        )
