import pygame

import config
import tool


class Player:
    def __init__(self, x, y):
        # 1. 初始化玩家的形狀與位置 (先用 Rect 方塊代替)
        self.rect = pygame.Rect(x, y, 40, 80)

        # 2. 物理相關變數
        self.vel_x = 0
        self.vel_y = 0
        self.gravity = 0.85
        self.speed = 5
        self.jump_power = -12
        self.is_grounded = False
        self.all_modes = ["spectator", "survival"]
        self.m_i = 1
        self.mode = self.all_modes[self.m_i]

    def handle_input(self, evnets):
        """處理鍵盤輸入（左右移動、跳躍）"""
        keys = pygame.key.get_pressed()
        if self.mode != "spectator":
            self.vel_x = 0

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -self.speed
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = self.speed
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.is_grounded:
                self.vel_y = self.jump_power
                self.is_grounded = False
        elif self.mode == "spectator":
            self.vel_x = 0
            self.vel_y = 0

            # X 軸：左右控制
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x -= 10  # 往左是負
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x += 10  # 往右是正

            # Y 軸：上下自由飛行
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel_y -= 10  # 網上飛是負（對抗重力）
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.vel_y += 10  # 往下飛是正
        for event in evnets:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    self.m_i = (self.m_i + 1) % len(self.all_modes)
                    self.mode = self.all_modes[self.m_i]

    def update(self, world_data):
        """處理重力、移動位置、以及與地圖方塊的碰撞偵測"""
        self.rect.x += self.vel_x

        # 檢查玩家周圍的方塊
        for y_idx, row in enumerate(world_data):
            for x_idx, block_name in enumerate(row):
                if block_name == "air" or self.mode == "spectator":
                    continue

                block_rect = pygame.Rect(x_idx * config.BLOCK_SIZE, y_idx * config.BLOCK_SIZE, config.BLOCK_SIZE, config.BLOCK_SIZE)

                # 如果 X 移動後撞到了方塊
                if self.rect.colliderect(block_rect) and self.mode != "spectator":
                    # 往右走時撞到（速度大於 0）
                    if self.vel_x > 0:
                        # 把玩家的右側擋在方塊的左側
                        self.rect.right = block_rect.left
                    # 往左走時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        # 把玩家的左側擋在方塊的右側
                        self.rect.left = block_rect.right
        # 應用重力
        if self.mode != "spectator":
            self.vel_y += self.gravity

        self.rect.y += self.vel_y

        # 預設玩家在空中
        self.is_grounded = False

        for y_idx, row in enumerate(world_data):
            for x_idx, block_name in enumerate(row):
                # 空氣不用檢查碰撞
                if block_name == "air" or self.mode == "spectator":
                    continue

                # 算出這個方塊在遊戲世界中的實際 Rect
                block_rect = pygame.Rect(x_idx * config.BLOCK_SIZE, y_idx * config.BLOCK_SIZE, config.BLOCK_SIZE, config.BLOCK_SIZE)

                # 3. 檢查玩家方塊人有沒有撞到這個實體方塊
                if self.rect.colliderect(block_rect):
                    # 如果往下掉時撞到了（速度大於 0）
                    if self.vel_y > 0:
                        # 把玩家的底部黏在方塊的頂部
                        self.rect.bottom = block_rect.top
                        self.vel_y = 0
                        self.is_grounded = True

                    # 如果往上跳時頭撞到了（速度小於 0）
                    elif self.vel_y < 0:
                        # 把玩家的頂部卡在方塊的底部
                        self.rect.top = block_rect.bottom
                        self.vel_y = 0
        max_player_x = (config.MAP_WIDTH * config.BLOCK_SIZE) - 40
        max_player_y = (config.MAP_HEIGHT * config.BLOCK_SIZE) - 80
        self.rect.x = tool.num_range(0, max_player_x, self.rect.x)
        self.rect.y = tool.num_range(0, max_player_y, self.rect.y)

    def draw(self, surface, scroll_x, scroll_y):
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
            surface.blit(temp_surface, (render_x, render_y))
        else:
            # 生存模式：照舊畫你原本完全不透明的普通方塊
            # 這裡的坐標一樣要記得扣掉你的 scroll 喔！
            pygame.draw.rect(surface, (0, 128, 255), (render_x, render_y, self.rect.width, self.rect.height))
        tool.show_text(
            surface,
            f"X: {self.rect.x // config.BLOCK_SIZE}, Y: {self.rect.y // config.BLOCK_SIZE}",
            tool.Colors.WHITE,
            config.WIDTH - 100,
            config.HEIGHT - 30,
            size=15,
            alpha=160,
        )
