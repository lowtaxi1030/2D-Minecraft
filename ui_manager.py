from typing import TYPE_CHECKING

import pygame

import asset_manager as assets
import config
import tool
import ui_obs as ui

if TYPE_CHECKING:
    from player import Player

pygame.init()


class UI:
    def __init__(self):

        self.hotbar = Hotbar()
        self.inventory = Inventory()
        self.debug = DebugScreen()

    def handle_events(self, event, player, mouse_pos):
        self.inventory.handle_events(event, player, mouse_pos)

    def update(self, player):
        self.hotbar.update(player)
        self.inventory.update()
        self.debug.update()

    def draw(self, screen, player: "Player"):

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

    def update(self, player: "Player"):
        assets.update_img_pos(assets.hotbar_bg_rect, screen_center=True, is_bottom=True)

        assets.select_frame_rect.left = assets.hotbar_bg_rect.left - 1 + (player.selected_hotbar_index * self.SLOT_SPACING)
        assets.select_frame_rect.top = assets.hotbar_bg_rect.top - 3

    def draw(self, screen: pygame.Surface, player: "Player"):
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

        self.inv_hotbar_first_x = assets.inv_rect.left + 20
        self.inv_hotbar_first_y = assets.inv_rect.bottom - 91

        self.INV_SPACING = 63

        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = assets.inv_rect.top + 287  # 調整這個

        self.INV_SPACING_X = 63
        self.INV_SPACING_Y = 63

        self.held_item = None

    def handle_events(self, event, player, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._handle_left_click(player, mouse_pos)

            if event.button == 3:
                self._handle_right_click(player, mouse_pos)

    def _handle_left_click(self, player: "Player", mouse_pos):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            return

        self._handle_slot_left_click(player, area, index)

    def _handle_right_click(self, player: "Player", mouse_pos):

        area, index = self._get_clicked_slot_info(mouse_pos)
        if area is None:
            return

        self._handle_slot_right_click(player, area, index)

    def _handle_slot_left_click(self, player: "Player", area, index):

        if not player.is_open_inv:
            return

        slot_item = self._get_slot(player, area, index)

        if self.held_item is None:
            self.held_item = slot_item
            slot_item = None

            self._set_slot(player, area, index, slot_item)

        elif slot_item is None:
            self._set_slot(player, area, index, self.held_item)

            self.held_item = None

        elif slot_item["type"] == self.held_item["type"]:
            slot_item, self.held_item = self._try_merge_stack(slot_item, self.held_item)

            self._set_slot(player, area, index, slot_item)

        else:
            slot_item, self.held_item = self.held_item, slot_item

            self._set_slot(player, area, index, slot_item)

    def _handle_slot_right_click(self, player: "Player", area, index):

        if not player.is_open_inv:
            return

        slot_item = self._get_slot(player, area, index)

        if self.held_item is None:
            if slot_item is None:
                return

            held_count = (slot_item["count"] + 1) // 2

            self.held_item = {
                "type": slot_item["type"],
                "count": held_count,
            }

            slot_item["count"] -= held_count

            if slot_item["count"] == 0:
                self._set_slot(player, area, index, None)
        elif slot_item is None:
            self.held_item["count"] -= 1

            self._set_slot(player, area, index, {"type": self.held_item["type"], "count": 1})

            if self.held_item["count"] == 0:
                self.held_item = None

        elif slot_item["type"] == self.held_item["type"]:
            if slot_item["count"] < 64:
                self.held_item["count"] -= 1

                new_count = slot_item["count"] + 1

                self._set_slot(player, area, index, {"type": self.held_item["type"], "count": new_count})

            if self.held_item["count"] == 0:
                self.held_item = None

        # 原版 Minecraft 甚麼都不做
        else:
            pass

    """好用工具"""

    def _get_clicked_slot(self, mouse_pos, start_x, start_y):
        col = (mouse_pos[0] - start_x) // self.INV_SPACING_X
        row = (mouse_pos[1] - start_y) // self.INV_SPACING_Y
        return col, row

    def _get_clicked_slot_info(self, mouse_pos):
        # --- 1. 檢查主背包區域 ---
        # 💡 提示：把 self.inv_main_first_x 和 y 丟進去算
        col, row = self._get_clicked_slot(mouse_pos, self.inv_main_first_x, self.inv_main_first_y)
        if mouse_pos[0] >= self.inv_main_first_x and mouse_pos[1] >= self.inv_main_first_y:
            if 0 <= col < 9 and 0 <= row < 3:
                return "inventory", row * 9 + col

        # --- 2. 檢查快捷列區域 ---
        # 💡 提示：改把 self.inv_hotbar_first_x 和 y 丟進去算
        col, row = self._get_clicked_slot(mouse_pos, self.inv_hotbar_first_x, self.inv_hotbar_first_y)
        if mouse_pos[0] >= self.inv_hotbar_first_x and mouse_pos[1] >= self.inv_hotbar_first_y:
            # 快捷列只有一排，所以 row 必須是 0
            if 0 <= col < 9 and row == 0:
                return "hotbar", col

        return None, None

    def _get_slot(self, player: "Player", area, index):
        if area == "hotbar":
            return player.hotbar[index]
        if area == "inventory":
            return player.inventory[index]

    def _set_slot(self, player, area, index, item):
        if area == "hotbar":
            player.hotbar[index] = item
        elif area == "inventory":
            player.inventory[index] = item

    def _try_merge_stack(self, dst_item, src_item):
        """
        dst_item: 目標格
        src_item: 來源(通常是滑鼠)
        """

        if dst_item["type"] != src_item["type"]:
            return dst_item, src_item

        total = dst_item["count"] + src_item["count"]

        if total <= 64:
            dst_item["count"] = total
            src_item = None
        else:
            src_item["count"] = total - 64
            dst_item["count"] = 64

        return dst_item, src_item

    """"""

    def update(self):
        assets.update_img_pos(assets.inv_rect, y_center=True, screen_center=True)

        self.inv_hotbar_first_x = assets.inv_rect.left + 20
        self.inv_hotbar_first_y = assets.inv_rect.bottom - 91

        self.inv_main_first_x = self.inv_hotbar_first_x
        self.inv_main_first_y = assets.inv_rect.top + 287

    def draw(self, screen, player: "Player"):
        self._draw_background(screen)
        self._draw_inventory_items(player, screen)
        self._draw_hotbar_items(player, screen)

        self._draw_held_item(screen)

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
                    item_center_x = self.inv_main_first_x + col * self.INV_SPACING_X + config.SLOT_SIZE // 2
                    item_center_y = self.inv_main_first_y + row * self.INV_SPACING_Y + config.SLOT_SIZE // 2
                    draw_item(screen, item, item_center_x, item_center_y)

    def _draw_hotbar_items(self, player, screen):
        for i in range(9):
            item = player.hotbar[i]
            if item is not None:
                # 利用新的微調變數算出位置
                item_center_x = self.inv_hotbar_first_x + i * self.INV_SPACING_X + config.SLOT_SIZE // 2
                item_center_y = self.inv_hotbar_first_y + config.SLOT_SIZE // 2
                draw_item(screen, item, item_center_x, item_center_y)

    def _draw_held_item(self, screen):
        if self.held_item is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        draw_item(screen, self.held_item, mouse_x, mouse_y)


class DebugScreen:

    def update(self):
        pass

    def _draw_pos(self, screen, player: "Player"):
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
