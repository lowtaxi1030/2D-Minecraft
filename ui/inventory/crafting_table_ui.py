from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from craft_manager import CraftingManager
    from player import Player
    from world_manager import World

import pygame

import config
import craft_manager
import tool
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


class CraftingTableUI(BaseInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets, "crafting_table")

        self.crafting_grid = craft_manager.CraftingGrid(3, 3)

        self.CRAFT_OFFSET_X = 97
        self.CRAFT_OFFSET_Y = 53

        self.craft_start_x = self.assets.ui_rects["crafting_table"].left + self.CRAFT_OFFSET_X
        self.craft_start_y = self.assets.ui_rects["crafting_table"].top + self.CRAFT_OFFSET_Y

        self.craft_output_x = self.assets.ui_rects["crafting_table"].left + 0
        self.craft_output_y = self.assets.ui_rects["crafting_table"].top + 0

        self.CRAFT_SPACING_X = 63
        self.CRAFT_SPACING_Y = 63

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        super().handle_events(event, player, mouse_pos, world_manager, crafting_manager)

        self._update_craft_preview(crafting_manager)

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, _ = self._get_clicked_slot_info(mouse_pos)

        if area == "output_craft":
            # 1. 取得當前合成盤材料字典
            ingredients = self._get_crafting_ingredients_dict()
            if ingredients == {}:
                return

            # self._can_receive_crafted_item()

            # 快速鍵！
            if self.keys[pygame.K_LSHIFT] or self.keys[pygame.K_RSHIFT]:
                # 處理快速鍵SHIFT: 一次合成、直到材料不夠為止，並把材料丟進背包裏面
                while True:
                    # 1. 執行合成（直接傳盤面，讓它自動計算當前剩餘材料）
                    result = crafting_manager.craft(ingredients, self.crafting_grid, is_preview=False)

                    # 2. 沒材料了，安全跳出
                    if not result:
                        break

                    # 3. 把成品給玩家（塞進背包）
                    self._receive_crafted_item(result, player, world_manager, force_inventory=True)
                return

            result = crafting_manager.craft(ingredients, self.crafting_grid, is_preview=False)  # 執行合成，扣除材料

            if result is not None and result:
                self._receive_crafted_item(result, player, world_manager)  # 將成品給玩家
            return

        super()._handle_left_click(player, mouse_pos, world_manager, crafting_manager)

    def _can_interact_with_slot(self, area, index):
        return area != "output_craft"

    def _update_craft_preview(self, crafting_manager: CraftingManager):
        # 統計合成盤裡的材料數量
        ingredients = self._get_crafting_ingredients_dict()

        # 這時候 ingredients 就會變成 {"oak_log": 1} 這種字典格式了！
        preview_result = crafting_manager.craft(ingredients, self.crafting_grid, is_preview=True)

        if preview_result:
            self.preview_item = preview_result
        else:
            self.preview_item = None

    def _get_crafting_ingredients_dict(self):
        # 統計合成盤裡的材料數量
        ingredients = {}
        for i in range(self.crafting_grid.width * self.crafting_grid.height):
            slot = self.crafting_grid.get(i)
            if slot is not None:
                item_type = slot["type"]
                count = slot["count"]
                ingredients[item_type] = ingredients.get(item_type, 0) + count
        return ingredients

    def _receive_crafted_item(self, result_item, player: Player, world_manager: World, force_inventory=False):
        remaining = 0
        if force_inventory:
            remaining = player.give_item(result_item["type"], result_item["count"])  # 將成品放入玩家背包或掉落到地面

        else:
            if self.held_item is None:
                self.held_item = result_item
            elif self.held_item["type"] == result_item["type"]:
                self.held_item, result_item = self.item_slot_manager._try_merge_stack(self.held_item, result_item)
                if result_item is not None and result_item["count"] > 0:
                    remaining = player.give_item(result_item["type"], result_item["count"])  # 將多的成品放入玩家背包或掉落到地面
            else:
                # 如果手上有東西，且不是同一種物品，則直接給玩家背包
                if result_item is not None and result_item["count"] > 0:
                    remaining = player.give_item(result_item["type"], result_item["count"])  # 將成品放入玩家背包或掉落到地面

        if remaining > 0:
            world_manager.spawn_item_entity(remaining, player.hitbox.centerx, player.hitbox.top, "inv_drop", player)  # 生成掉落物

    def _get_clicked_slot_info(self, mouse_pos):
        col, row = self._get_clicked_slot(mouse_pos, self.craft_start_x, self.craft_start_y)
        if mouse_pos[0] >= self.craft_start_x and mouse_pos[1] >= self.craft_start_y:
            if 0 <= col < self.crafting_grid.width and 0 <= row < self.crafting_grid.height:
                return "craft", row * self.crafting_grid.width + col

        output_rect = pygame.Rect(0, 0, config.SLOT_SIZE, config.SLOT_SIZE)
        output_rect.center = (self.craft_output_x, self.craft_output_y)
        if output_rect.collidepoint(mouse_pos):
            return "output_craft", 0

        return super()._get_clicked_slot_info(mouse_pos)

    def _get_slot(self, player: Player, area, index):
        if area == "craft":
            return self.crafting_grid.get(index)
        if area == "output_craft":
            return self.preview_item
        return super()._get_slot(player, area, index)

    def _update_slot(self, player, area, index, item):
        if area == "output_craft":
            self.preview_item = None
        if area == "craft":
            self.crafting_grid.set(index, item)
        return super()._update_slot(player, area, index, item)

    def update(self, player: Player):

        super().update(player)

        self.craft_start_x = self.assets.ui_rects["crafting_table"].left + self.CRAFT_OFFSET_X
        self.craft_start_y = self.assets.ui_rects["crafting_table"].top + self.CRAFT_OFFSET_Y

        self.craft_output_x = self.assets.ui_rects["crafting_table"].right - 155
        self.craft_output_y = self.assets.ui_rects["crafting_table"].top + 150

    def draw(self, screen: pygame.Surface, player):
        super().draw(screen, player)
        self._draw_crafting_grid(screen)
        self._draw_result_item(screen)
        self._draw_held_item(screen)

    def _draw_crafting_grid(self, screen: pygame.Surface):
        for row in range(self.crafting_grid.height):
            for col in range(self.crafting_grid.width):
                item = self.crafting_grid.grid[row][col]
                if item is not None:
                    item_center_x = self.craft_start_x + col * self.CRAFT_SPACING_X + config.SLOT_SIZE // 2
                    item_center_y = self.craft_start_y + row * self.CRAFT_SPACING_Y + config.SLOT_SIZE // 2
                    draw_item(screen, self.assets, item, item_center_x, item_center_y)

    def _draw_held_item(self, screen: pygame.Surface):
        # print("[from: _draw_held_item]", self.held_item)
        if self.held_item is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        draw_item(screen, self.assets, self.held_item, mouse_x, mouse_y)

    def _draw_result_item(self, screen: pygame.Surface):
        # 測試用：直接畫一個工作檯看位置對不對
        # draw_item(screen, self.assets, {"type": "crafting_table", "count": 1}, self.craft_output_x, self.craft_output_y)
        if self.preview_item is None:
            return

        draw_item(screen, self.assets, self.preview_item, self.craft_output_x, self.craft_output_y)

    def clear_grid_and_drop(self, player: Player, world_manager: World):
        """將 3x3 合成格與手上拿著的物品清空，並生成掉落物到世界上"""
        # 1. 掉落 3x3 合成格裡的東西
        for i in range(self.crafting_grid.width * self.crafting_grid.height):
            item = self.crafting_grid.get(i)
            if item is not None and item.get("count", 0) > 0:
                player.give_item(item["type"], item["count"])
                self.crafting_grid.set(i, None)

        # 2. 如果玩家滑鼠游標上還「抓著」物品（held_item），也一起掉落
        if self.held_item is not None and self.held_item.get("count", 0) > 0:
            player.give_item(self.held_item["type"], self.held_item["count"])
            self.held_item = None

        # 3. 清空預覽
        self.preview_item = None
