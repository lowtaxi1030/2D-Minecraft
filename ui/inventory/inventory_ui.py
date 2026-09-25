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


class InventoryUI(BaseInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets, "inventory")

        self.craft_start_x = self.assets.ui_rects["inventory"].right - 281
        self.craft_start_y = self.assets.ui_rects["inventory"].top + 56

        self.craft_output_x = self.assets.ui_rects["inventory"].right - 50
        self.craft_output_y = self.assets.ui_rects["inventory"].top + 126

        self.player_craft_slots = craft_manager.CraftingGrid(2, 2)  # 合成欄位長度為2X2=4

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        super().handle_events(event, player, mouse_pos, world_manager, crafting_manager)

        self._update_craft_preview(crafting_manager)

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, _ = self._get_clicked_slot_info(mouse_pos)

        # 嘗試呼叫合成
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
                    result = crafting_manager.craft(ingredients, self.player_craft_slots, is_preview=False)

                    # 2. 沒材料了，安全跳出
                    if not result:
                        break

                    # 3. 把成品給玩家（塞進背包）
                    self._receive_crafted_item(result, player, world_manager, force_inventory=True)
                return

            result = crafting_manager.craft(ingredients, self.player_craft_slots, is_preview=False)  # 執行合成，扣除材料

            if result is not None and result:
                self._receive_crafted_item(result, player, world_manager)  # 將成品給玩家
            return

        super()._handle_left_click(player, mouse_pos, world_manager, crafting_manager)

    def _can_interact_with_slot(self, area, index):
        return area != "output_craft"

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

    def update(self, player):

        super().update(player)

        self.craft_start_x = self.assets.ui_rects["inventory"].right - 281
        self.craft_start_y = self.assets.ui_rects["inventory"].top + 56

        self.craft_output_x = self.assets.ui_rects["inventory"].right - 50
        self.craft_output_y = self.assets.ui_rects["inventory"].top + 126

    def _update_craft_preview(self, crafting_manager: CraftingManager):
        # 統計合成盤裡的材料數量
        ingredients = self._get_crafting_ingredients_dict()

        # 這時候 ingredients 就會變成 {"oak_log": 1} 這種字典格式了！
        preview_result = crafting_manager.craft(ingredients, self.player_craft_slots, is_preview=True)

        if preview_result:
            self.preview_item = preview_result
        else:
            self.preview_item = None

    def _get_clicked_slot_info(self, mouse_pos):
        # --- 1. 檢查合成欄區域 ---
        # 把 self.craft_start_x、y 丟進去算
        col, row = self._get_clicked_slot(mouse_pos, self.craft_start_x, self.craft_start_y)
        if mouse_pos[0] >= self.craft_start_x and mouse_pos[1] >= self.craft_start_y:
            if 0 <= col < self.player_craft_slots.width and 0 <= row < self.player_craft_slots.height:
                return "craft", row * self.player_craft_slots.width + col

        # --- 2. 檢查合成結果欄區域 ---
        # 把 self.craft_output_x、y 丟進去算
        output_rect = pygame.Rect(0, 0, config.SLOT_SIZE, config.SLOT_SIZE)
        output_rect.center = (self.craft_output_x, self.craft_output_y)
        if output_rect.collidepoint(mouse_pos):
            return "output_craft", 0

        return super()._get_clicked_slot_info(mouse_pos)

    def _get_slot(self, player: Player, area, index):
        if area == "output_craft":
            return self.preview_item
        if area == "craft":
            return self.player_craft_slots.get(index)
        return super()._get_slot(player, area, index)

    def _update_slot(self, player: Player, area, index, item):
        if area == "output_craft":
            self.preview_item = None
        if area == "craft":
            self.player_craft_slots.set(index, item)
        return super()._update_slot(player, area, index, item)

    def _get_crafting_ingredients_dict(self):
        # 統計合成盤裡的材料數量
        ingredients = {}
        for i in range(self.player_craft_slots.width * self.player_craft_slots.height):
            slot = self.player_craft_slots.get(i)
            if slot is not None:
                item_type = slot["type"]
                count = slot["count"]
                ingredients[item_type] = ingredients.get(item_type, 0) + count
        return ingredients

    """"""

    def draw(self, screen: pygame.Surface, player: Player):
        super().draw(screen, player)
        self._draw_crafting_grid(screen)

        self._draw_result_item(screen)
        self._draw_held_item(screen)

    def _draw_crafting_grid(self, screen: pygame.Surface):
        for row in range(self.player_craft_slots.height):
            for col in range(self.player_craft_slots.width):
                item = self.player_craft_slots.grid[row][col]
                if item is not None:
                    item_center_x = self.craft_start_x + col * self.INV_SPACING_X + config.SLOT_SIZE // 2
                    item_center_y = self.craft_start_y + row * self.INV_SPACING_Y + config.SLOT_SIZE // 2
                    draw_item(screen, self.assets, item, item_center_x, item_center_y)

    def _draw_held_item(self, screen: pygame.Surface):
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
