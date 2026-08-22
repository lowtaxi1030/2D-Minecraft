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
from chest_state import ChestState
from furnace_state import FurnaceState
from item_slot_manager import SlotHandler

pygame.init()
clock = pygame.time.Clock()

Item = dict[str, str | int]


class Interfaces(Protocol):
    def handle_input(self): ...
    def handle_events(self): ...
    def update(self): ...
    def draw(self): ...
    def clear_grid_and_drop(self): ...


class UI:
    def __init__(self, assets: AssetManager):

        self.hotbar = Hotbar(assets)

        self.inventory = InventoryUI(assets)
        self.crafting_table = CraftingTableUI(assets)
        self.furnace = FurnaceUI(assets)
        self.chest = ChestUI(assets)

        self.interfaces: dict[str, Interfaces] = {
            "inventory": self.inventory,
            "crafting_table": self.crafting_table,
            "furnace": self.furnace,
            "chest": self.chest,
        }

        self.debug = DebugScreen(assets)

        self.last_crafting_type = None

    def handle_input(self):
        # 其他的之後如果有再說
        for interface in self.interfaces.values():
            interface.handle_input()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        self.hotbar.handle_events(event, player, mouse_pos)

        if player.inv_type is not None:
            self.interfaces[player.inv_type].handle_events(event, player, mouse_pos, world_manager, crafting_manager)
            self.last_crafting_type = player.inv_type

        elif self.last_crafting_type is not None:
            self.interfaces[self.last_crafting_type].clear_grid_and_drop(player, world_manager)
            self.last_crafting_type = None

    def update(self, player, fps, mouse_pos, camera, world):
        self.hotbar.update(player)

        for interface in self.interfaces.values():
            interface.update(player)

        self.debug.update(player, fps, mouse_pos, camera, world)

    def draw(self, screen, player: Player, fps, mouse_pos, camera):

        if player.inv_type is not None:
            self.interfaces[player.inv_type].draw(screen, player)
        else:
            self.hotbar.draw(screen, player)

        self.debug.draw(screen, player, fps, mouse_pos, camera)


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


class BaseInventory(PlayerInventory):
    def __init__(self, assets: AssetManager, interface_name: str):
        super().__init__(assets)
        self.item_slot_manager = SlotHandler()

        self.interface_name = interface_name

        self.held_item = None
        self.preview_item = None
        self.is_dragging = False

        self.drag_button = None  # 紀錄是左鍵(1)還是右鍵(3)拖曳
        self.dragged_slots = []  # 紀錄劃過了哪些格子 ( Slot 物件或 index )
        self.drag_start_item = None  # 紀錄開始拖曳時手上的物品備份 (型態與初始數量)
        self.drag_slot_snapshots = {}  # 紀錄每個格子「第一次被拖曳碰到當下」的原始內容，分配運算永遠以此為準
        self.drag_visited_slots = set()  # 紀錄滑鼠「實際碰過」哪些格子(不論合不合法)，用來判斷這次按下究竟是單擊還是真的拖曳
        self.drag_confirmed = False  # 這次按下是否已經確定演變成真正的拖曳(碰過第二格)

        self.keys = []

    def handle_input(self):
        self.keys = pygame.key.get_pressed()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button in (1, 3):
                self._handle_click_down(event.button, player, mouse_pos, world_manager, crafting_manager)

        if event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self._handle_drag_motion(player, mouse_pos, crafting_manager)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3) and self.is_dragging and event.button == self.drag_button:
                self._handle_drag_end(player, mouse_pos, world_manager, crafting_manager)

    def _handle_click_down(self, button: int, player: Player, mouse_pos, world_manager, crafting_manager):
        area, index = self._get_clicked_slot_info(mouse_pos)

        # 手上有物品、且點在有效格子上 -> 先進入「待定」狀態，不要在按下的當下就執行點擊
        # 這次按下究竟是「單擊」還是「拖曳分配」，要等放開滑鼠時才能確定
        if self.held_item is not None and area is not None:
            self.is_dragging = True
            self.drag_button = button
            self.drag_start_item = self.held_item.copy()
            self.dragged_slots = []
            self.drag_slot_snapshots = {}
            self.drag_visited_slots = {(area, index)}
            self.drag_confirmed = False

            # 起始格也要跟拖曳途中碰到的格子用同一套規則驗證：
            # 裡面裝著不同種類的物品時，不能被拖曳分配覆蓋（那應該維持原樣，只有單擊才會交換它）
            if self._can_interact_with_slot(area, index) and self._can_add_to_drag(player, area, index):
                self.dragged_slots.append((area, index))
                self.drag_slot_snapshots[(area, index)] = self._snapshot_slot(player, area, index)
            return

        # 手上沒有東西 -> 不存在「拖曳分配」的情境，維持原本單擊行為 (撿取/交換/拆堆)
        if button == 1:
            self._handle_left_click(player, mouse_pos, world_manager, crafting_manager)
        elif button == 3:
            self._handle_right_click(player, mouse_pos, world_manager, crafting_manager)

    def _snapshot_slot(self, player, area, index):
        """取得格子當下內容的獨立副本，之後分配運算永遠以此為準，不受後續寫入影響"""
        item = self._get_slot(player, area, index)
        return item.copy() if item is not None else None

    def _handle_drag_motion(self, player: Player, mouse_pos, crafting_manager):
        area, index = self._get_clicked_slot_info(mouse_pos)

        # 沒落在格子上，或是已經碰過的格子就跳過
        if area is None or (area, index) in self.drag_visited_slots:
            return

        # 這是本次按下後，滑鼠第一次真的移動到別格 -> 拖曳正式成立
        # 右鍵拖曳的話，起始格從按下當下就被延後處理、一直沒有機會放置，這裡補放一次
        if not self.drag_confirmed:
            self.drag_confirmed = True
            if self.drag_button == 3 and self.dragged_slots:
                start_area, start_index = self.dragged_slots[0]
                self._apply_right_drag_single(player, start_area, start_index)

        self.drag_visited_slots.add((area, index))

        # 檢查該格子是否允許互動/放置
        if not self._can_interact_with_slot(area, index):
            return

        if not self._can_add_to_drag(player, area, index):
            return

        self.dragged_slots.append((area, index))
        # 這格是「本次拖曳第一次碰到」，此刻的即時內容就是原始內容，記錄下來供後續分配運算使用
        self.drag_slot_snapshots[(area, index)] = self._snapshot_slot(player, area, index)

        # 依據按鈕進行拖曳計算 (1: 左鍵均分, 3: 右鍵逐一擺放)
        if self.drag_button == 1:
            self._apply_left_drag_split(player)
        elif self.drag_button == 3:
            self._apply_right_drag_single(player, area, index)

    def _handle_drag_end(self, player: Player, mouse_pos, world_manager, crafting_manager):
        # 全程只碰過起始那一格(不論那格合不合法)，代表滑鼠根本沒有真正拖到別格 -> 這其實是一般單擊
        if len(self.drag_visited_slots) <= 1:
            if self.drag_button == 1:
                self._handle_left_click(player, mouse_pos, world_manager, crafting_manager)
            elif self.drag_button == 3:
                self._handle_right_click(player, mouse_pos, world_manager, crafting_manager)

        self.is_dragging = False
        self.drag_button = None
        self.drag_start_item = None
        self.dragged_slots.clear()
        self.drag_slot_snapshots.clear()
        self.drag_visited_slots.clear()
        self.drag_confirmed = False

    def _can_add_to_drag(self, player, area, index):
        slot_item = self._get_slot(player, area, index)  # 取得該格目前的物品

        # 格子是空的 -> 可以拖曳進去
        if slot_item is None:
            return True

        # 格子有東西，但跟拖曳的物品同種類 -> 可以拖曳進去
        if slot_item["type"] == self.drag_start_item["type"]:
            if slot_item["count"] < config.MAX_STACK:
                return True

        # 格子裡是「不同的物品」 -> 不可覆蓋！
        return False

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            if not self.assets.ui_rects[self.interface_name].collidepoint(mouse_pos):
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
        if area is None or not self._can_interact_with_slot(area, index):
            return

        slot_item = self._get_slot(player, area, index)
        # print("[from: _hadle_right_click]  GET :", area, index, slot_item)

        self.held_item, slot_item = self.item_slot_manager.handle_slot_right_click(self.held_item, slot_item)
        # print("[from: _handle_right_click]  HANDLER :", self.held_item, slot_item)

        self._update_slot(player, area, index, slot_item)
        # print("[from: _handle_right_click]  UPDATE :", area, index, slot_item)

    def _can_interact_with_slot(self, area, index):
        return True

    def _apply_left_drag_split(self, player: Player):
        if not (self.drag_start_item and self.dragged_slots):
            return

        plan = self._calculate_drag_distribution()

        if plan["aborted"]:
            self._revert_dragged_slots(player)
            self.held_item = self.drag_start_item.copy()
        else:
            self._apply_drag_distribution(player, plan)

    def _calculate_drag_distribution(self):
        """回傳一份「這次拖曳應該長什麼樣子」的計畫 (plan)"""

        plan = {"aborted": False, "slot_updates": {}, "final_held_item": None}

        total_count = self.drag_start_item["count"]
        slot_count = len(self.dragged_slots)
        per_slot_count = total_count // slot_count
        remainder = total_count % slot_count

        if per_slot_count == 0:

            plan["aborted"] = True
            return plan

        item_type = self.drag_start_item["type"]
        leftover_from_stacks = 0

        for area, index in self.dragged_slots:
            # 一律用「這格第一次被拖曳碰到當下」的快照當基準，
            # 不讀即時值，避免同一批數量被本次拖曳的上一輪計算重複疊加
            original = self.drag_slot_snapshots.get((area, index))

            existing_count = 0
            if original is not None and original["type"] == item_type:
                existing_count = original["count"]

            target_count = existing_count + per_slot_count

            # 處理 64 個堆疊上限
            if target_count > config.MAX_STACK:
                leftover_from_stacks += target_count - config.MAX_STACK
                target_count = config.MAX_STACK

            new_item = {"type": item_type, "count": target_count}
            plan["slot_updates"][(area, index)] = new_item

        # 修正：手上總剩餘數量 = 均分餘數 + 爆堆疊溢出的數量
        final_held_count = remainder + leftover_from_stacks
        if final_held_count > 0:
            plan["final_held_item"] = {"type": item_type, "count": final_held_count}
        else:
            plan["final_held_item"] = None

        return plan

    def _apply_drag_distribution(self, player: Player, plan):
        for (area, index), new_item in plan["slot_updates"].items():
            self._update_slot(player, area, index, new_item)

        self.held_item = plan["final_held_item"]

    def _revert_dragged_slots(self, player: Player):
        """把本次拖曳寫過的格子還原成拖曳開始前的原始內容"""
        for (area, index), original in self.drag_slot_snapshots.items():
            self._update_slot(player, area, index, original.copy() if original is not None else None)

    def _apply_right_drag_single(self, player: Player, area: str, index: int):
        if self.held_item is None or self.held_item["count"] <= 0:
            return

        slot_item = self._get_slot(player, area, index)

        # 格子若是空的，放 1 個進去
        if slot_item is None:
            self._update_slot(player, area, index, {"type": self.held_item["type"], "count": 1})
            self.held_item["count"] -= 1

        # 格子若有相同物品，堆疊 +1
        elif slot_item["type"] == self.held_item["type"] and slot_item["count"] < config.MAX_STACK:
            slot_item["count"] += 1
            self._update_slot(player, area, index, slot_item)
            self.held_item["count"] -= 1

        # 扣到 0 則清空手上物品
        if self.held_item["count"] <= 0:
            self.held_item = None

    def update(self, player):
        self.assets.update_img_pos(self.assets.ui_rects[self.interface_name], y_center=True, screen_center=True)

        super().update()

    def draw(self, screen: pygame.Surface, player):
        screen.blit(self.assets.ui_images[self.interface_name], self.assets.ui_rects[self.interface_name])
        super().draw(screen, player)


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
            world_manager.spawn_item_entity(remaining, player.rect.centerx, player.rect.top, "inv_drop", player)  # 生成掉落物

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

    def clear_grid_and_drop(self, player: Player, world_manager: World):
        if self.held_item is not None and self.held_item.get("count", 0) > 0:
            player.give_item(self.held_item["type"], self.held_item["count"])
            self.held_item = None


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


class FurnaceUI(BaseInventory):
    def __init__(self, assets: AssetManager):
        super().__init__(assets, "furnace")
        self.furnace_state = None

        self.INPUT_OFFSET = (223, 88)
        self.FUEL_OFFSET = (223, 214)
        self.OUTPUT_OFFSET = (182, 150)

        self.FIRE_OFFSET = (200, 130)
        self.ARROW_OFFSET = (280, 123)

        self.input_pos = (
            self.assets.ui_rects["furnace"].left + self.INPUT_OFFSET[0],
            self.assets.ui_rects["furnace"].top + self.INPUT_OFFSET[1],
        )

        self.fuel_pos = (
            self.assets.ui_rects["furnace"].left + self.FUEL_OFFSET[0],
            self.assets.ui_rects["furnace"].top + self.FUEL_OFFSET[1],
        )

        self.output_pos = (
            self.assets.ui_rects["furnace"].right - self.OUTPUT_OFFSET[0],
            self.assets.ui_rects["furnace"].top + self.OUTPUT_OFFSET[1],
        )

    def set_furnace_state(self, state: FurnaceState):
        """用來切換目前 UI 正在顯示/操作哪一個熔爐的資料"""
        self.furnace_state = state

    # 屬性讀取要補上安全檢查（防止 self.furnace_state 為 None）
    @property
    def input_item(self):
        return self.furnace_state.input_item if self.furnace_state else None

    @input_item.setter
    def input_item(self, value):
        if self.furnace_state:
            self.furnace_state.input_item = value

    @property
    def fuel_item(self):
        return self.furnace_state.fuel_item if self.furnace_state else None

    @fuel_item.setter
    def fuel_item(self, value):
        if self.furnace_state:
            self.furnace_state.fuel_item = value

    @property
    def output_item(self):
        return self.furnace_state.output_item if self.furnace_state else None

    @output_item.setter
    def output_item(self, value):
        if self.furnace_state:
            self.furnace_state.output_item = value

    def _handle_left_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        area, _ = self._get_clicked_slot_info(mouse_pos)
        if area == "furnace_input":
            self.held_item, self.input_item = self.item_slot_manager.handle_slot_left_click(self.held_item, self.input_item)
            return
        if area == "furnace_fuel":
            self.held_item, self.fuel_item = self.item_slot_manager.handle_slot_left_click(self.held_item, self.fuel_item)
            return
        if area == "furnace_output":
            if self.output_item is None:
                return

            # 1. Shift + 左鍵：快速將成品轉移至背包
            if self.keys[pygame.K_LSHIFT] or self.keys[pygame.K_RSHIFT]:
                # 直接把整個 output_item 丟進背包（這部分可以複用你寫好的 _receive_crafted_item 或背包收納 logic）
                remains = player.give_item(self.output_item["type"], self.output_item["count"])
                self.output_item = (
                    {"type": self.output_item["type"], "count": remains} if remains > 0 else None
                )  # 若背包滿了裝不下，剩餘的會留留在 output 槽
                return

            # 2. 一般左鍵點擊：使用剛才設計的 handle_output_slot_click 拿取到手上
            self.held_item, self.output_item = self.item_slot_manager.handle_output_slot_click(self.held_item, self.output_item)
            return

        super()._handle_left_click(player, mouse_pos, world_manager, crafting_manager)

    def _handle_right_click(self, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        area, _ = self._get_clicked_slot_info(mouse_pos)
        if area == "furnace_input":
            self.held_item, self.input_item = self.item_slot_manager.handle_slot_right_click(self.held_item, self.input_item)
            return
        if area == "furnace_fuel":
            self.held_item, self.fuel_item = self.item_slot_manager.handle_slot_right_click(self.held_item, self.fuel_item)
            return
        if area == "furnace_output":
            return  # 取得物品

        super()._handle_right_click(player, mouse_pos, world_manager, crafting_manager)

    def _can_interact_with_slot(self, area, index):
        return area != "furnace_output"

    def _get_clicked_slot_info(self, mouse_pos):
        slot_size = config.SLOT_SIZE

        input_rect = pygame.Rect(0, 0, slot_size, slot_size)
        input_rect.center = (self.input_pos[0], self.input_pos[1])

        if input_rect.collidepoint(mouse_pos):
            return "furnace_input", 0

        fuel_rect = pygame.Rect(0, 0, slot_size, slot_size)
        fuel_rect.center = (self.fuel_pos[0], self.fuel_pos[1])
        if fuel_rect.collidepoint(mouse_pos):
            return "furnace_fuel", 0

        output_rect = pygame.Rect(0, 0, slot_size, slot_size)
        output_rect.center = (self.output_pos[0], self.output_pos[1])
        if output_rect.collidepoint(mouse_pos):
            return "furnace_output", 0

        return super()._get_clicked_slot_info(mouse_pos)

    def _get_slot(self, player: Player, area, index):
        if area == "furnace_input":
            return self.input_item
        if area == "furnace_fuel":
            return self.fuel_item
        if area == "furnace_output":
            return self.output_item
        return super()._get_slot(player, area, index)

    def _update_slot(self, player: Player, area, index, item):
        if area == "furnace_input":
            self.input_item = item
            return
        if area == "furnace_fuel":
            self.fuel_item = item
            return
        if area == "furnace_output":
            self.output_item = item
            return
        super()._update_slot(player, area, index, item)

    def update(self, player):
        super().update(player)

        self.input_pos = (
            self.assets.ui_rects["furnace"].left + self.INPUT_OFFSET[0],
            self.assets.ui_rects["furnace"].top + self.INPUT_OFFSET[1],
        )

        self.fuel_pos = (
            self.assets.ui_rects["furnace"].left + self.FUEL_OFFSET[0],
            self.assets.ui_rects["furnace"].top + self.FUEL_OFFSET[1],
        )

        self.output_pos = (
            self.assets.ui_rects["furnace"].right - self.OUTPUT_OFFSET[0],
            self.assets.ui_rects["furnace"].top + self.OUTPUT_OFFSET[1],
        )

        self.FIRE_OFFSET = (195, 125)
        self.ARROW_OFFSET = (280, 122)

        if self.furnace_state:
            self.furnace_state.update()

    def draw(self, screen: pygame.Surface, player):
        super().draw(screen, player)
        self._draw_input_item(screen)
        self._draw_fuel_item(screen)
        self._draw_output_item(screen)

        self._draw_fire_progress(screen)
        self._draw_arrow_progress(screen)

        self._draw_held_item(screen)

    def _draw_held_item(self, screen: pygame.Surface):
        # print("[from: _draw_held_item]", self.held_item)
        if self.held_item is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        draw_item(screen, self.assets, self.held_item, mouse_x, mouse_y)

    def _draw_input_item(self, screen: pygame.Surface):
        if self.input_item is None:
            # draw_item(screen, self.assets, {"type": "oak_log", "count": 5}, self.input_pos[0], self.input_pos[1])
            return

        draw_item(screen, self.assets, self.input_item, self.input_pos[0], self.input_pos[1])

    def _draw_fuel_item(self, screen: pygame.Surface):
        if self.fuel_item is None:
            # draw_item(screen, self.assets, {"type": "oak_planks", "count": 5}, self.fuel_pos[0], self.fuel_pos[1])
            return

        draw_item(screen, self.assets, self.fuel_item, self.fuel_pos[0], self.fuel_pos[1])

    def _draw_output_item(self, screen: pygame.Surface):
        if self.output_item is None:
            # draw_item(screen, self.assets, {"type": "oak_planks", "count": 5}, self.output_pos[0], self.output_pos[1])
            return

        draw_item(screen, self.assets, self.output_item, self.output_pos[0], self.output_pos[1])

    def _draw_fire_progress(self, screen: pygame.Surface):
        if self.furnace_state.burn_time_left <= 0 or self.furnace_state.burn_time <= 0:
            return

        fire_img = self.assets.ui_images.get("lit_progress")
        if not fire_img:
            return

        w, h = fire_img.get_size()
        burn_pct = self.furnace_state.burn_time_left / self.furnace_state.burn_time
        current_h = int(h * burn_pct)

        if current_h > 0:
            # 由下往上裁切 (y從 h - current_h 開始)
            crop_rect = pygame.Rect(0, h - current_h, w, current_h)
            cropped_fire = fire_img.subsurface(crop_rect)

            # 對齊 UI 基準座標 (FIRE_OFFSET 需要依據 3.5 倍後的相對位置微調)
            fire_x = self.assets.ui_rects["furnace"].left + self.FIRE_OFFSET[0]
            fire_y = self.assets.ui_rects["furnace"].top + self.FIRE_OFFSET[1] + (h - current_h)

            screen.blit(cropped_fire, (fire_x, fire_y))

    def _draw_arrow_progress(self, screen: pygame.Surface):
        if self.furnace_state.cook_progress <= 0 or self.furnace_state.cook_time <= 0:
            return

        arrow_img = self.assets.ui_images.get("burn_progress")
        if not arrow_img:
            return

        # 1. 原始圖片的寬度 (未放大前是 24 px)
        ORIGINAL_WIDTH = 24
        SCALE = 3.5

        cook_pct = self.furnace_state.cook_progress / self.furnace_state.cook_time

        # 2. 計算目前推進到第幾個「原始像素格」(0 ~ 24)
        raw_step = int(ORIGINAL_WIDTH * cook_pct)

        # 3. 再將格數轉換成實際繪製的像素寬度
        current_w = int(raw_step * SCALE)

        if current_w > 0:
            crop_rect = pygame.Rect(0, 0, current_w, arrow_img.get_height())
            cropped_arrow = arrow_img.subsurface(crop_rect)

            arrow_x = self.assets.ui_rects["furnace"].left + self.ARROW_OFFSET[0]
            arrow_y = self.assets.ui_rects["furnace"].top + self.ARROW_OFFSET[1]

            screen.blit(cropped_arrow, (arrow_x, arrow_y))


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

    def set_chest_state(self, state: ChestState):
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
                f"Pos : ({player_block_x}, {show_player_y})",  # show_player_y
                f"Vel : ({player.vel_x:.2f}, {player.vel_y:.2f})",
                f"Grounded : {player.is_grounded}",
                f"Flying : {player.is_flying}",
                f"Mode : {player.mode}",
                f"Facing : {'Right' if player.facing == 1 else 'Left'}",
                "",
                "=== Block ===",
                f"Mouse Pos : ({world_mouse_x}, {show_mouse_y})",  # show_mouse_y
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
