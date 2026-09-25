from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from player import Player

import pygame

import config
import tool
from states import ChestState
from ui.element import ui_widgets as ui

from .base_inventory import BaseInventory


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


class ChestUI(BaseInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets, "chest")
        self.chest_state = None

        self.CHEST_SPACING = 63

        self.CHEST_OFFSET = (20, 56)

        self.chest_pos = (
            self.assets.ui_rects["chest"].left + self.CHEST_OFFSET[0],
            self.assets.ui_rects["chest"].top + self.CHEST_OFFSET[1],
        )

    def set_state(self, state: ChestState):
        """用來切換目前 UI 正在顯示/操作哪一個熔爐的資料"""
        self.chest_state = state

    def _get_clicked_slot_info(self, mouse_pos):
        col, row = self._get_clicked_slot(mouse_pos, self.chest_pos[0], self.chest_pos[1])
        if mouse_pos[0] >= self.chest_pos[0] and mouse_pos[1] >= self.chest_pos[1]:
            if 0 <= col < self.chest_state.width and 0 <= row < self.chest_state.height:
                return "chest", row * self.chest_state.width + col

        return super()._get_clicked_slot_info(mouse_pos)

    def _get_slot(self, player: Player, area, index):
        if area == "chest":
            return self.chest_state.grids[index]
        return super()._get_slot(player, area, index)

    def _update_slot(self, player: Player, area, index, item):
        if area == "chest":
            self.chest_state.grids[index] = item
            return
        super()._update_slot(player, area, index, item)

    def update(self, player):
        super().update(player)

        self.chest_pos = (
            self.assets.ui_rects["chest"].left + self.CHEST_OFFSET[0],
            self.assets.ui_rects["chest"].top + self.CHEST_OFFSET[1],
        )

    def draw(self, screen: pygame.Surface, player: Player):
        super().draw(screen, player)

        self._draw_chest_items(screen)
        self._draw_held_item(screen)

    def _draw_chest_items(self, screen: pygame.Surface):
        for i, grid in enumerate(self.chest_state.grids):
            if grid is None:
                continue
            col, row = i % 9, i // 9
            item_center_x = self.chest_pos[0] + col * self.CHEST_SPACING + config.SLOT_SIZE // 2
            item_center_y = self.chest_pos[1] + row * self.CHEST_SPACING + config.SLOT_SIZE // 2
            # if i == 0:
            #     draw_item(screen, self.assets, {"type": "iron_block", "count": 64}, item_center_x, item_center_y)
            draw_item(screen, self.assets, grid, item_center_x, item_center_y)

    def _draw_held_item(self, screen: pygame.Surface):
        # print("[from: _draw_held_item]", self.held_item)
        if self.held_item is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        draw_item(screen, self.assets, self.held_item, mouse_x, mouse_y)
