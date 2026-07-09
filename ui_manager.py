import pygame

import asset_manager as assets
import config
import tool
import ui_obs as ui
from player import Player

pygame.init()


class UI:
    def __init__(self):

        self.hotbar = Hotbar()
        self.inventory = Inventory()
        self.debug = DebugScreen()

    def update(self, player):
        self.hotbar.update(player)
        self.inventory.update()
        self.debug.update()

    def draw(self, screen, player: Player):

        if player.is_open_inv:
            self.inventory.draw(screen, player)
        else:
            self.hotbar.draw(screen, player)

        self.debug.draw(screen, player)


def draw_item(screen, item, center_x, center_y):
    block_img = assets.img_blocks[item["type"]]
    block_img = pygame.transform.scale(block_img, (48, 48))
    block_rect = block_img.get_rect()
    block_rect.center = (center_x, center_y)
    screen.blit(block_img, block_rect)
    ui.show_text(
        screen,
        str(item["count"]),
        tool.Colors.WHITE,
        center_x,
        center_y + 5,
        25,
    )


class Hotbar:
    def __init__(self):
        self.SLOT_SPACING = 64
        self.inv_hotbar_first_x = assets.inv_rect.left + 56
        self.inv_hotbar_first_y = assets.inv_rect.bottom - 55
        self.INV_SPACING = 63
        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = assets.inv_rect.top + 323  # 調整這個
        self.INV_SPACING_X = 63
        self.INV_SPACING_Y = 63

    def update(self, player: Player):
        assets.update_img_pos(assets.hotbar_bg_rect, screen_center=True, is_bottom=True)

        assets.select_frame_rect.left = assets.hotbar_bg_rect.left - 1 + (player.selected_hotbar_index * self.SLOT_SPACING)
        assets.select_frame_rect.top = assets.hotbar_bg_rect.top - 3

    def draw(self, screen: pygame.Surface, player: Player):
        # 畫圖片
        screen.blit(assets.hotbar_bg, assets.hotbar_bg_rect)
        screen.blit(assets.select_frame, assets.select_frame_rect)

        # 畫方塊和數量
        self.block_start_x = assets.select_frame_rect.centerx
        self.block_start_y = assets.select_frame_rect.centery
        first_slot_center_x = assets.hotbar_bg_rect.left + 36
        for i in range(9):
            item = player.hotbar[i]
            if item is not None:
                item_center_x = first_slot_center_x + (i * self.SLOT_SPACING)
                item_center_y = assets.select_frame_rect.centery
                draw_item(screen, item, item_center_x, item_center_y)


class Inventory:
    def __init__(self):
        self.SLOT_SPACING = 64
        self.inv_hotbar_first_x = assets.inv_rect.left + 56
        self.inv_hotbar_first_y = assets.inv_rect.bottom - 55
        self.INV_SPACING = 63
        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = assets.inv_rect.top + 323  # 調整這個
        self.INV_SPACING_X = 63
        self.INV_SPACING_Y = 63

    def update(self):
        assets.update_img_pos(assets.inv_rect, y_center=True, screen_center=True)

        self.inv_hotbar_first_x = assets.inv_rect.left + 56
        self.inv_hotbar_first_y = assets.inv_rect.bottom - 55

        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = assets.inv_rect.top + 323

    def draw(self, screen, player: Player):
        self._draw_background(screen)
        self._draw_inventory_items(player, screen)
        self._draw_hotbar_items(player, screen)

    def _draw_background(self, screen):
        screen.blit(assets.inventory_img, assets.inv_rect)

    def _draw_inventory_items(self, player, screen):
        """繪製 3x9 主背包"""
        for row in range(3):
            for col in range(9):
                index = row * 9 + col
                # 假設你的 player 裡面已經建立好一個 27 大小的 inventory 陣列
                item = player.inventory[index]
                if item is not None:
                    # 運用剛才調好的邏輯，動態算出 27 格每一格的中心點
                    item_center_x = self.inv_main_first_x + (col * self.INV_SPACING_X)
                    item_center_y = self.inv_main_first_y + (row * self.INV_SPACING_Y)
                    draw_item(screen, item, item_center_x, item_center_y)

    def _draw_hotbar_items(self, player, screen):
        for i in range(9):
            item = player.hotbar[i]
            if item is not None:
                # 利用新的微調變數算出位置
                item_center_x = self.inv_hotbar_first_x + (i * self.INV_SPACING)
                item_center_y = self.inv_hotbar_first_y
                draw_item(screen, item, item_center_x, item_center_y)


class DebugScreen:

    def update(self):
        pass

    def _draw_pos(self, screen, player: Player):
        """玩家按下 F3 時的畫面"""
        ui.show_text(
            screen,
            f"x: {player.rect.x // config.BLOCK_SIZE}  y: {player.rect.y // config.BLOCK_SIZE}",
            tool.Colors.WHITE,
            10,
            10,
            size=18,
        )

    def draw(self, screen, player):
        if not config.show_debug_screen:
            return
        self._draw_pos(screen, player)
