import pygame

import config


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

    def handle_input(self):
        """處理鍵盤輸入（左右移動、跳躍）"""
        keys = pygame.key.get_pressed()
        self.vel_x = 0

        if keys[pygame.K_a]:
            self.vel_x = -self.speed
        if keys[pygame.K_d]:
            self.vel_x = self.speed
        if keys[pygame.K_SPACE] and self.is_grounded:
            self.vel_y = self.jump_power
            self.is_grounded = False

    def update(self, world_data):
        """處理重力、移動位置、以及與地圖方塊的碰撞偵測"""
        self.rect.x += self.vel_x

        # 檢查玩家周圍的方塊
        for y_idx, row in enumerate(world_data):
            for x_idx, block_name in enumerate(row):
                if block_name == "air":
                    continue

                block_rect = pygame.Rect(x_idx * config.BLOCK_SIZE, y_idx * config.BLOCK_SIZE, config.BLOCK_SIZE, config.BLOCK_SIZE)

                # 如果 X 移動後撞到了方塊
                if self.rect.colliderect(block_rect):
                    # 往右走時撞到（速度大於 0）
                    if self.vel_x > 0:
                        # 把玩家的右側擋在方塊的左側
                        self.rect.right = block_rect.left
                    # 往左走時撞到（速度小於 0）
                    elif self.vel_x < 0:
                        # 把玩家的左側擋在方塊的右側
                        self.rect.left = block_rect.right
        # 應用重力
        self.vel_y += self.gravity

        self.rect.y += self.vel_y

        # 預設玩家在空中
        self.is_grounded = False

        for y_idx, row in enumerate(world_data):
            for x_idx, block_name in enumerate(row):
                # 空氣不用檢查碰撞
                if block_name == "air":
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

    def draw(self, surface, scroll_x, scroll_y):
        """將玩家畫在畫面上 (記得扣除鏡頭捲動位移)"""
        # 計算在螢幕上的實際繪製位置
        render_x = self.rect.x - scroll_x
        render_y = self.rect.y - scroll_y

        # 先用簡單的顏色畫出方塊人
        pygame.draw.rect(surface, (0, 102, 204), (render_x, render_y, self.rect.width, self.rect.height))
