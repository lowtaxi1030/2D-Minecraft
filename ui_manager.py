import pygame

import asset_manager
import config

pygame.init()


class UI:
    def __init__(self):
        self.all_ui = []
        total_hotbar_width = 9 * (config.SLOT_SIZE + config.PADDING) - config.PADDING

        self.start_x = (config.current_width - total_hotbar_width) // 2
        self.start_y = config.current_height - config.SLOT_SIZE - 10

    def updata(self):
        asset_manager.update_img_pos(asset_manager.hotbar_bg_rect, (0, config.current_height - 40))

    def draw(self, screen: pygame.Surface, player):
        # for i in range(9):
        #     # 💡 提示：根據 i 算出每個格子的 X 座標
        #     x = self.start_x + i * (config.SLOT_SIZE + config.PADDING)
        #     y = self.start_y

        #     # 建立一個 Pygame 的 Rect 物件代表這一格
        #     slot_rect = pygame.Rect(x, y, config.SLOT_SIZE, config.SLOT_SIZE)

        #     # 💡 關鍵判斷：如果 i 等於玩家當前選中的格子 (self.selected_hotbar_index)
        #     # 就用特別醒目的顏色（例如金色、粗邊框）畫出「選取框」；其餘用普通灰色
        #     if i == player.selected_hotbar_index:
        #         pygame.draw.rect(screen, (255, 215, 0), slot_rect, 3)  # 金色粗框
        #     else:
        #         pygame.draw.rect(screen, (100, 100, 100), slot_rect, 2)  # 灰色細框

        #     # 3. 💡 提示：檢查玩家 hotbar[i] 裡面有沒有東西？
        #     item = player.hotbar[i]
        #     if item is not None:
        #         # 這裡等等可以拿來畫方塊的縮圖！
        #         # 並且用 pygame.font 寫出 item["count"] 的數量數字
        #         pass
        # screen.blit(asset_manager.hotbar_bg, asset_manager.hotbar_bg_rect)
        pass
