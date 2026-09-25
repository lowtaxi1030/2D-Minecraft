from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from player import Player
    from world_manager import World

import pygame

import config
from craft_manager import CraftingManager
from item_slot_manager import SlotHandler

from .player_inventory import PlayerInventory


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
                    world_manager.spawn_item_entity(
                        self.held_item, player.hitbox.centerx, player.hitbox.top, "inv_drop", player
                    )  # 生成掉落物
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
