from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from player import Player

import pygame

import tool
from ui.element import ui_widgets as ui


class Hotbar:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        self.SLOT_SPACING = 64
        self.inv_hotbar_first_x = self.assets.ui_rects["inventory"].left + 56
        self.inv_hotbar_first_y = self.assets.ui_rects["inventory"].bottom - 55
        self.INV_SPACING = 63
        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = self.assets.ui_rects["inventory"].top + 323  # 調整這個
        self.INV_SPACING_X = 63
        self.INV_SPACING_Y = 63

        self.show_hotbar = True

        self.item_text = ui.Text(
            name="item_text",
            text="",
            pos=(self.assets.select_frame_rect.centerx, self.assets.select_frame_rect.centery - 80),
            colors=tool.Colors.WHITE,
            size=25,
        )

    def handle_events(self, event, player: Player, mouse_pos):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.show_hotbar = not self.show_hotbar

    def update(self, player: Player):
        self.assets.update_img_pos(self.assets.hotbar_bg_rect, screen_center=True, is_bottom=True)

        self.assets.select_frame_rect.left = self.assets.hotbar_bg_rect.left - 1 + (player.selected_hotbar_index * self.SLOT_SPACING)
        self.assets.select_frame_rect.top = self.assets.hotbar_bg_rect.top - 3

    def draw(self, screen: pygame.Surface, player: Player):
        if self.show_hotbar:
            # 畫圖片
            screen.blit(self.assets.hotbar_bg, self.assets.hotbar_bg_rect)
            screen.blit(self.assets.select_frame, self.assets.select_frame_rect)

            # 畫方塊和數量
            self.block_start_x = self.assets.select_frame_rect.centerx
            self.block_start_y = self.assets.select_frame_rect.centery
            first_slot_center_x = self.assets.hotbar_bg_rect.left + 36
            for i in range(9):
                item = player.hotbar[i]
                if item is not None:
                    item_center_x = first_slot_center_x + (i * self.SLOT_SPACING)
                    item_center_y = self.assets.select_frame_rect.centery
                    ui.draw_item(screen, self.assets, item, item_center_x, item_center_y)
            item = player.held_item

            if item is not None:

                self.item_text.text = item["type"].replace("_", " ")

                self.item_text.draw(screen)
