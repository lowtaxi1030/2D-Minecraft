from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from player import Player
    from world_manager import World

import pygame

import config
import tool
from ui.element import ui_widgets as ui


def draw_item(screen: pygame.Surface, assets: AssetManager, item, center_x, center_y):
    block_img = assets.block(item["type"])
    block_img = pygame.transform.scale(block_img, (48, 48))
    block_rect = block_img.get_rect()
    block_rect.center = (center_x, center_y)
    screen.blit(block_img, block_rect)
    show_center_x = center_x - 5
    if item["count"] < 10:
        show_center_x = center_x + 11
    ui.show_text(
        screen,
        str(item["count"]),
        tool.Colors.WHITE,
        show_center_x,
        center_y + 5,
        25,
        show=item["count"] > 1,
    )


class PlayerInventory:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        self.SLOT_SPACING = 64

        self.inv_hotbar_first_x = self.assets.ui_rects["inventory"].left + 20
        self.inv_hotbar_first_y = self.assets.ui_rects["inventory"].bottom - 91

        # self.INV_SPACING = 63

        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = self.assets.ui_rects["inventory"].top + 287  # 調整這個

        self.INV_SPACING_X = 63
        self.INV_SPACING_Y = 63

    def _get_clicked_slot(self, mouse_pos, start_x, start_y):
        col = (mouse_pos[0] - start_x) // self.INV_SPACING_X
        row = (mouse_pos[1] - start_y) // self.INV_SPACING_Y
        return col, row

    def _get_slot(self, player: Player, area, index):
        if area == "hotbar":
            return player.hotbar[index]
        if area == "inventory":
            return player.inventory[index]

    def _update_slot(self, player: Player, area, index, item):
        if area == "hotbar":
            player.hotbar[index] = item
        if area == "inventory":
            player.inventory[index] = item

    def _get_clicked_slot_info(self, mouse_pos):
        # --- 1. 檢查主背包區域 ---
        # 改把 self.inv_main_first_x、y 丟進去算
        col, row = self._get_clicked_slot(mouse_pos, self.inv_main_first_x, self.inv_main_first_y)
        if mouse_pos[0] >= self.inv_main_first_x and mouse_pos[1] >= self.inv_main_first_y:
            if 0 <= col < 9 and 0 <= row < 3:
                return "inventory", row * 9 + col

        # --- 2. 檢查快捷列區域 ---
        # 改把 self.inv_hotbar_first_x、y 丟進去算
        col, row = self._get_clicked_slot(mouse_pos, self.inv_hotbar_first_x, self.inv_hotbar_first_y)
        if mouse_pos[0] >= self.inv_hotbar_first_x and mouse_pos[1] >= self.inv_hotbar_first_y:
            # 快捷列只有一排，所以 row 必須是 0
            if 0 <= col < 9 and row == 0:
                return "hotbar", col

        return None, None

    def update(self):
        self.inv_hotbar_first_x = self.assets.ui_rects["inventory"].left + 20
        self.inv_hotbar_first_y = self.assets.ui_rects["inventory"].bottom - 91

        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = self.assets.ui_rects["inventory"].top + 287

    def draw(self, screen: pygame.Surface, player: Player):
        self._draw_inventory_items(screen, player)
        self._draw_hotbar_items(screen, player)

    def _draw_inventory_items(self, screen: pygame.Surface, player: Player):
        """繪製 3x9 主背包"""
        for row in range(3):
            for col in range(9):
                index = row * 9 + col
                # 假設你的 player 裡面已經建立好一個 27 大小的 inventory 陣列
                item = player.inventory[index]
                if item is not None:
                    # 運用剛才調好的邏輯，動態算出 27 格每一格的中心點
                    item_center_x = self.inv_main_first_x + col * self.INV_SPACING_X + config.SLOT_SIZE // 2
                    item_center_y = self.inv_main_first_y + row * self.INV_SPACING_Y + config.SLOT_SIZE // 2
                    draw_item(screen, self.assets, item, item_center_x, item_center_y)

    def _draw_hotbar_items(self, screen: pygame.Surface, player):
        for i in range(9):
            item = player.hotbar[i]
            if item is not None:
                # 利用新的微調變數算出位置
                item_center_x = self.inv_hotbar_first_x + i * self.INV_SPACING_X + config.SLOT_SIZE // 2
                item_center_y = self.inv_hotbar_first_y + config.SLOT_SIZE // 2
                draw_item(screen, self.assets, item, item_center_x, item_center_y)

    def clear_grid_and_drop(self, player: Player, world_manager: World):
        if self.held_item is not None and self.held_item.get("count", 0) > 0:
            player.give_item(self.held_item["type"], self.held_item["count"])
            self.held_item = None
