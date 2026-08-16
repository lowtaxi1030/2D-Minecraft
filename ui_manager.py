from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from camera import Camera
    from craft_manager import CraftingManager
    from player import Player
    from world_manager import World

import pygame

import chunk_manager
import config
import craft_manager
import tool
import ui_obs as ui
from item_slot_manager import SlotHandler

pygame.init()
clock = pygame.time.Clock()

Item = dict[str, str | int]


class Interfaces(Protocol):
    def handle_input(self): ...
    def handle_events(self): ...
    def update(self): ...
    def draw(self): ...


class UI:
    def __init__(self, assets: AssetManager):

        self.hotbar = Hotbar(assets)

        self.inventory = InventoryUI(assets)
        self.crafting_table = CraftingTableUI(assets)
        self.furnace = FurnaceUI(assets)

        self.interfaces: dict[str, Interfaces] = {
            "inventory": self.inventory,
            "crafting_table": self.crafting_table,
            "furnace": self.furnace,
        }

        self.debug = DebugScreen(assets)

        self.last_crafting_type = None

    def handle_input(self):
        # 其他的之後如果有再說
        for interface in self.interfaces.values():
            interface.handle_input()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        self.hotbar.handle_events(event, player, mouse_pos)

        if player.crafting_type is not None:
            self.interfaces[player.crafting_type].handle_events(event, player, mouse_pos, world_manager, crafting_manager)
            self.last_crafting_type = player.crafting_type

        elif self.last_crafting_type is not None:
            self.interfaces[self.last_crafting_type].clear_grid_and_drop(player, world_manager)
            self.last_crafting_type = None

    def update(self, player, fps, mouse_pos, camera, world):
        self.hotbar.update(player)

        for interface in self.interfaces.values():
            interface.update(player)

        self.debug.update(player, fps, mouse_pos, camera, world)

    def draw(self, screen, player: Player, fps, mouse_pos, camera):

        if player.crafting_type is not None:
            self.interfaces[player.crafting_type].draw(screen, player)
        else:
            self.hotbar.draw(screen, player)

        self.debug.draw(screen, player, fps, mouse_pos, camera)


def draw_item(screen: pygame.Surface, assets: AssetManager, item, center_x, center_y):
    block_img = assets.block(item["type"])
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
        show=item["count"] > 1,
    )


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
                    draw_item(screen, self.assets, item, item_center_x, item_center_y)
            item = player.hotbar[player.selected_hotbar_index]

            if item is not None:

                ui.show_text(
                    screen,
                    item["type"].replace("_", " "),
                    tool.Colors.WHITE,
                    self.assets.select_frame_rect.centerx,
                    self.assets.select_frame_rect.centery - 80,
                    25,
                    screen_center=True,
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

    def clear_grid_and_drop(self, player: Player, world_manager: World): ...


class InventoryUI(PlayerInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)
        self.assets = assets
        self.item_slot_manager = SlotHandler()

        self.craft_start_x = self.assets.ui_rects["inventory"].right - 281
        self.craft_start_y = self.assets.ui_rects["inventory"].top + 56

        self.craft_output_x = self.assets.ui_rects["inventory"].right - 50
        self.craft_output_y = self.assets.ui_rects["inventory"].top + 126
        self.preview_item = None

        self.player_craft_slots = craft_manager.CraftingGrid(2, 2)  # 合成欄位長度為2X2=4
        self.held_item = None

        self.keys = []

    def handle_input(self):
        self.keys = pygame.key.get_pressed()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_left_click(player, mouse_pos, world_manager, crafting_manager)

            if event.button == 3:
                self._handle_right_click(player, mouse_pos, world_manager, crafting_manager)

        self._update_craft_preview(crafting_manager)

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            if not self.assets.ui_rects["inventory"].collidepoint(mouse_pos):
                if self.held_item is not None:
                    world_manager.spawn_item_entity(self.held_item, player.rect.centerx, player.rect.top, "inv_drop", player)  # 生成掉落物
                    self.held_item = None
            return

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

        slot_item = self._get_slot(player, area, index)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_left_click(self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)

    def _handle_right_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            return

        slot_item = self._get_slot(player, area, index)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_right_click(self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)

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
            world_manager.spawn_item_entity(remaining, player.rect.centerx, player.rect.top, "inv_drop", player)  # 生成掉落物

    def update(self, player):
        self.assets.update_img_pos(self.assets.ui_rects["inventory"], y_center=True, screen_center=True)

        super().update()

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

    """好用工具"""

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
        self._draw_background(screen)
        self._draw_crafting_grid(screen)
        super().draw(screen, player)

        self._draw_preview_item(screen)
        self._draw_held_item(screen)

    def _draw_background(self, screen: pygame.Surface):
        screen.blit(self.assets.ui_images["inventory"], self.assets.ui_rects["inventory"])

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

    def _draw_preview_item(self, screen: pygame.Surface):
        # 測試用：直接畫一個工作檯看位置對不對
        # draw_item(screen, self.assets, {"type": "crafting_table", "count": 1}, self.craft_output_x, self.craft_output_y)
        if self.preview_item is None:
            return

        draw_item(screen, self.assets, self.preview_item, self.craft_output_x, self.craft_output_y)

    def clear_grid_and_drop(self, player: Player, world_manager: World):
        if self.held_item is not None and self.held_item.get("count", 0) > 0:
            player.give_item(self.held_item["type"], self.held_item["count"])
            self.held_item = None


class CraftingTableUI(PlayerInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)
        self.assets = assets
        self.item_slot_manager = SlotHandler()

        self.crafting_grid = craft_manager.CraftingGrid(3, 3)
        # self.crafting_grid.grid[0][0] = {"type": "oak_log", "count": 5}  # 測試用
        self.held_item = None
        self.preview_item = None

        self.CRAFT_OFFSET_X = 97
        self.CRAFT_OFFSET_Y = 53

        self.craft_start_x = self.assets.ui_rects["crafting_table"].left + self.CRAFT_OFFSET_X
        self.craft_start_y = self.assets.ui_rects["crafting_table"].top + self.CRAFT_OFFSET_Y

        self.craft_output_x = self.assets.ui_rects["crafting_table"].left + 0
        self.craft_output_y = self.assets.ui_rects["crafting_table"].top + 0

        self.CRAFT_SPACING_X = 63
        self.CRAFT_SPACING_Y = 63

        self.keys = []

    def handle_input(self):
        self.keys = pygame.key.get_pressed()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_left_click(player, mouse_pos, world_manager, crafting_manager)

            if event.button == 3:
                self._handle_right_click(player, mouse_pos, world_manager, crafting_manager)

        self._update_craft_preview(crafting_manager)

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            if not self.assets.ui_rects["crafting_table"].collidepoint(mouse_pos):
                if self.held_item is not None:
                    world_manager.spawn_item_entity(self.held_item, player.rect.centerx, player.rect.top, "inv_drop", player)  # 生成掉落物
                    self.held_item = None
            return

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

        slot_item = self._get_slot(player, area, index)
        # print("[from: _hadle_left_click]  GET :", area, index, slot_item)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_left_click(self.held_item, slot_item)
        # print("[from: _handle_left_click]  HANDLER :", self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)
        # print("[from: _handle_left_click]  UPDATE :", area, index, slot_item)

    def _handle_right_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None or area == "output_craft":
            return

        slot_item = self._get_slot(player, area, index)
        # print("[from: _hadle_right_click]  GET :", area, index, slot_item)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_right_click(self.held_item, slot_item)
        # print("[from: _handle_right_click]  HANDLER :", self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)
        # print("[from: _handle_right_click]  UPDATE :", area, index, slot_item)

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
            world_manager.spawn_item_entity(remaining, player.rect.centerx, player.rect.top, "inv_drop", player)  # 生成掉落物

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
        self.assets.update_img_pos(self.assets.ui_rects["crafting_table"], y_center=True, screen_center=True)

        super().update()

        self.craft_start_x = self.assets.ui_rects["crafting_table"].left + self.CRAFT_OFFSET_X
        self.craft_start_y = self.assets.ui_rects["crafting_table"].top + self.CRAFT_OFFSET_Y

        self.craft_output_x = self.assets.ui_rects["crafting_table"].right - 155
        self.craft_output_y = self.assets.ui_rects["crafting_table"].top + 150

    def draw(self, screen: pygame.Surface, player):
        screen.blit(self.assets.ui_images["crafting_table"], self.assets.ui_rects["crafting_table"])
        super().draw(screen, player)
        self._draw_crafting_grid(screen)
        self._draw_preview_item(screen)
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

    def _draw_preview_item(self, screen: pygame.Surface):
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


class FurnaceUI(PlayerInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)
        self.item_slot_manager = SlotHandler()

        self.held_item = None
        self.preview_item = None

        self.keys = []

        self.FURNACE_OFFSET_X = 97
        self.FURNACE_OFFSET_Y = 53

        self.furnace_start_x = self.assets.ui_rects["furnace"].left + self.FURNACE_OFFSET_X
        self.furnace_start_y = self.assets.ui_rects["furnace"].top + self.FURNACE_OFFSET_Y

        self.furnace_output_x = self.assets.ui_rects["furnace"].left + 0
        self.furnace_output_y = self.assets.ui_rects["furnace"].top + 0

    def handle_input(self):
        self.keys = pygame.key.get_pressed()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_left_click(player, mouse_pos, world_manager, crafting_manager)

            if event.button == 3:
                self._handle_right_click(player, mouse_pos, world_manager, crafting_manager)

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            if not self.assets.ui_rects["furnace"].collidepoint(mouse_pos):
                if self.held_item is not None:
                    world_manager.spawn_item_entity(self.held_item, player.rect.centerx, player.rect.top, "inv_drop", player)  # 生成掉落物
                    self.held_item = None
            return

        slot_item = self._get_slot(player, area, index)
        # print("[from: _hadle_left_click]  GET :", area, index, slot_item)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_left_click(self.held_item, slot_item)
        # print("[from: _handle_left_click]  HANDLER :", self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)
        # print("[from: _handle_left_click]  UPDATE :", area, index, slot_item)

    def _handle_right_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None or area == "output_craft":
            return

        slot_item = self._get_slot(player, area, index)
        # print("[from: _hadle_right_click]  GET :", area, index, slot_item)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_right_click(self.held_item, slot_item)
        # print("[from: _handle_right_click]  HANDLER :", self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)
        # print("[from: _handle_right_click]  UPDATE :", area, index, slot_item)

    def update(self, player):
        self.assets.update_img_pos(self.assets.ui_rects["furnace"], y_center=True, screen_center=True)

        super().update()
        self.furnace_start_x = self.assets.ui_rects["furnace"].left + self.FURNACE_OFFSET_X
        self.furnace_start_y = self.assets.ui_rects["furnace"].top + self.FURNACE_OFFSET_Y

    def draw(self, screen: pygame.Surface, player):
        screen.blit(self.assets.ui_images["furnace"], self.assets.ui_rects["furnace"])
        super().draw(screen, player)
        self._draw_held_item(screen)

    def _draw_held_item(self, screen: pygame.Surface):
        # print("[from: _draw_held_item]", self.held_item)
        if self.held_item is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        draw_item(screen, self.assets, self.held_item, mouse_x, mouse_y)


class DebugScreen:
    def __init__(self, assets: AssetManager):
        # self.assets = assets

        self.debug_frame = 0
        self.left_lines = []
        self.right_lines = []

    def update(self, player: Player, fps, mouse_pos: tuple[int, int], camera: Camera, world: World):
        self.debug_frame += 1

        if self.debug_frame >= 12:
            self.debug_frame = 0

            world_mouse_x, world_mouse_y = camera.screen_to_world(mouse_pos)

            show_mouse_y = 63 + (config.BASE_LINE - world_mouse_y)

            player_block_x = player.rect.centerx // config.BLOCK_SIZE
            player_block_y = player.rect.centery // config.BLOCK_SIZE

            show_player_y = 63 + (config.BASE_LINE - player_block_y)

            current_chunk = player.rect.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)
            local_x = player_block_x % config.CHUNK_WIDTH

            standing_block = (
                "None"
                if player.is_flying
                else chunk_manager.get_block(
                    player.rect.centerx,
                    tool.clamp(
                        0,
                        config.MAP_HEIGHT * config.BLOCK_SIZE - 1,
                        player.rect.bottom,
                    ),
                ).replace("_", " ")
            )

            mouse_block = chunk_manager.get_block(
                world_mouse_x * config.BLOCK_SIZE,
                world_mouse_y * config.BLOCK_SIZE,
            ).replace("_", " ")

            self.left_lines = [
                "=== Player ===",
                f"Pos : ({player_block_x}, {player_block_y})",  # show_player_y
                f"Vel : ({player.vel_x:.2f}, {player.vel_y:.2f})",
                f"Grounded : {player.is_grounded}",
                f"Flying : {player.is_flying}",
                f"Mode : {player.mode}",
                f"Facing : {'Right' if player.facing == 1 else 'Left'}",
                "",
                "=== Block ===",
                f"Mouse Pos : ({world_mouse_x}, {world_mouse_y})",  # show_mouse_y
                f"Mouse : {mouse_block}",
                f"Standing : {standing_block}",
                "",
                "=== Performance ===",
                f"FPS : {fps:.0f}",
                f"Scren Mouse Pos: {mouse_pos}",
                f"Loaded Chunks : {len(config.chunks)}",
                f"Entities : {len(world.item_entities)}",
                f"Dirty Chunks : {sum(chunk.is_dirty for chunk in config.chunks.values())}",
            ]

            self.right_lines = [
                "=== World ===",
                f"World : {config.CURRENT_WORLD}",
                f"Seed : {config.WORLD_SEED}",
                f"Chunk : {current_chunk}",
                f"Local X : {local_x}",
                f"Biome : {chunk_manager.get_biome(player.rect.centerx)}",
                "",
                "=== Camera ===",
                f"Scroll : ({camera.scroll_x:.1f}, {camera.scroll_y:.1f})",
                f"Zoom : {camera.zoom:.2f}",
                "",
            ]

    def _draw_debug(self, screen):
        """玩家按下 F3 時的畫面"""

        ui.show_text(
            screen,
            self.left_lines,
            tool.Colors.WHITE,
            10,
            10,
            size=18,
            use_cache=False,
        )
        ui.show_text(
            screen,
            self.right_lines,
            tool.Colors.WHITE,
            config.current_width - 300,
            10,
            size=18,
            use_cache=False,
        )

    def draw(self, screen, player, fps, mouse_pos, camera):
        if not config.show_debug_screen:
            return
        self._draw_debug(screen)
