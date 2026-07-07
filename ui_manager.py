import pygame

import asset_manager as assets
import config

# import tool

pygame.init()


class UI:
    def __init__(self):
        self.all_ui = []
        total_hotbar_width = 9 * (config.SLOT_SIZE + config.PADDING) - config.PADDING

        self.start_x = (config.current_width - total_hotbar_width) // 2
        self.start_y = config.current_height - config.SLOT_SIZE - 10

        self.SLOT_SPACING = 64
        self.block_start_x = assets.select_frame_rect.centerx
        self.block_start_y = assets.select_frame_rect.centery

    def update(self, player):

        assets.update_img_pos(assets.hotbar_bg_rect, screen_center=True, is_bottom=True)
        assets.update_img_pos(assets.inv_rect, y_center=True, screen_center=True)

        assets.select_frame_rect.left = assets.hotbar_bg_rect.left - 1 + (player.selected_hotbar_index * self.SLOT_SPACING)
        assets.select_frame_rect.top = assets.hotbar_bg_rect.top - 3

    def draw(self, screen: pygame.Surface, player):
        if not player.is_open_inv:
            screen.blit(assets.hotbar_bg, assets.hotbar_bg_rect)
            screen.blit(assets.select_frame, assets.select_frame_rect)

        if player.is_open_inv:
            screen.blit(assets.inventory_img, assets.inv_rect)

            inv_hotbar_first_x = assets.inv_rect.left + 56
            inv_hotbar_first_y = assets.inv_rect.bottom - 55

            INV_SPACING = 63

            # 🎯 主背包位置推算
            # 💡 提示：主背包第一格的 X 軸與快捷列相同！
            inv_main_first_x = inv_hotbar_first_x

            # 💡 提示：主背包第一格（最上面那一排）的 Y 軸起點，你需要猜或量一個數字
            inv_main_first_y = assets.inv_rect.top + 300  # 👈 試著調整這個 Y 起點
            INV_SPACING_X = 63
            INV_SPACING_Y = 63  # 👈 垂直的格子間距通常跟橫向一樣是 63 像素左右

            # 繪製 3x9 主背包
            for row in range(3):
                for col in range(9):
                    index = row * 9 + col
                    # 假設你的 player 裡面已經建立好一個 27 大小的 inventory 陣列
                    item = player.inventory[index]

                    if item is not None:
                        # 運用剛才調好的邏輯，動態算出 27 格每一格的中心點
                        item_center_x = inv_main_first_x + (col * INV_SPACING_X)
                        item_center_y = inv_main_first_y + (row * INV_SPACING_Y)

                        block_img = config.img_blocks[item["type"]]
                        block_img = pygame.transform.scale(block_img, (40, 40))

                        block_rect = block_img.get_rect()
                        block_rect.center = (item_center_x, item_center_y)

                        screen.blit(block_img, block_rect)

            for i in range(9):
                item = player.hotbar[i]
                if item is not None:
                    # 利用新的微調變數算出位置
                    item_center_x = inv_hotbar_first_x + (i * INV_SPACING)
                    item_center_y = inv_hotbar_first_y

                    block_img = config.img_blocks[item["type"]]
                    block_img = pygame.transform.scale(block_img, (40, 40))

                    block_rect = block_img.get_rect()
                    block_rect.center = (item_center_x, item_center_y)

                    screen.blit(block_img, block_rect)
        else:
            self.block_start_x = assets.select_frame_rect.centerx
            self.block_start_y = assets.select_frame_rect.centery

            first_slot_center_x = assets.hotbar_bg_rect.left + 36

            for i in range(9):
                item = player.hotbar[i]
                if item is not None:
                    item_center_x = first_slot_center_x + (i * self.SLOT_SPACING)
                    item_center_y = assets.select_frame_rect.centery

                    block_img = config.img_blocks[item["type"]]
                    block_img = pygame.transform.scale(block_img, (40, 40))

                    block_rect = block_img.get_rect()
                    block_rect.center = (item_center_x, item_center_y)

                    screen.blit(block_img, block_rect)
