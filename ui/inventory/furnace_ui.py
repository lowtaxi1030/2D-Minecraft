from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from craft_manager import CraftingManager
    from player import Player
    from world_manager import World

import pygame

import config
import tool
from states import FurnaceState
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

    def set_state(self, state: FurnaceState):
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
