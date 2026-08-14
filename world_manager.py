from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from fluid_manager import FluidManager
    from player import Player

import random

import pygame

import chunk_manager
import config
import item_entity
from camera import Camera
from game_data.block_drops import BLOCK_DROPS
from special_blocks import SPECIAL_BLOCKS


class BlockClick:
    def __init__(self, x: int, y: int, block: str):
        self.x = x
        self.y = y
        self.block = block
        self.rect = pygame.Rect(
            self.x * int(config.BLOCK_SIZE),
            self.y * int(config.BLOCK_SIZE),
            int(config.BLOCK_SIZE),
            int(config.BLOCK_SIZE),
        )


class World:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        self.item_entities = []

        self.last_pos = (0, 0)
        self.last_mouse_btn = -1

    def update(
        self,
        mouse_buttons: tuple[bool, bool, bool],
        mouse_pos: tuple[int, int],
        player: Player,
        camera: Camera,
        fluid_manager: FluidManager,
    ):

        self._handle_item_entities(player)

        # 沒有按下任何鍵，或是正在合成中
        if not any(mouse_buttons) or player.crafting_type is not None:
            # 鬆開所有按鍵時，把記錄的按鍵與位置重置
            self.last_mouse_btn = -1
            self.last_pos = None
            return

        current_btn = -1
        if mouse_buttons[0]:
            current_btn = 0
        elif mouse_buttons[1]:
            current_btn = 1
        elif mouse_buttons[2]:
            current_btn = 2

        # 計算世界座標
        clicked = self._get_clicked_block(mouse_pos, camera)

        if clicked is None:
            self.last_mouse_btn = -1
            self.last_pos = None
            return

        current_pos = (clicked.x, clicked.y)

        if current_pos == self.last_pos and current_btn == self.last_mouse_btn:
            return

        if mouse_buttons[0]:
            self._handle_break_block(clicked, player, fluid_manager)

        elif mouse_buttons[1]:
            self._handle_pick_block(clicked, player)

        elif mouse_buttons[2]:
            if not self._handle_special_block(clicked, player):
                self._handle_place_block(clicked, player, fluid_manager)
        self.last_pos = current_pos
        self.last_mouse_btn = current_btn

    def _get_clicked_block(self, mouse_pos, camera: Camera):
        world_x, world_y = camera.screen_to_world(mouse_pos)

        # if world_x < 0 or world_x >= config.MAP_WIDTH or world_y < 0 or world_y >= config.MAP_HEIGHT:
        #     return None

        clicked_block = chunk_manager.get_block(world_x * config.BLOCK_SIZE, world_y * config.BLOCK_SIZE)
        return BlockClick(
            world_x,
            world_y,
            clicked_block,
        )

    def _handle_special_block(self, clicked: BlockClick, player: Player) -> bool:
        # 檢查是不是特殊方塊
        if (special_block_class := SPECIAL_BLOCKS.get(clicked.block)) is None:
            return False
        # 執行interact
        special_block = special_block_class(player)
        special_block.interact()

        return True

    def _handle_break_block(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):
        if clicked.block != "air" and player.can_place_block() and self._can_break(clicked, player, fluid_manager):
            drop_item_type = self.get_drop_item(clicked.block)
            print(drop_item_type)

            if player.will_drop_item_entity() and drop_item_type is not None:
                self.item_entities.append(
                    item_entity.ItemEntity(
                        {"type": drop_item_type, "count": 1},
                        clicked.x * config.BLOCK_SIZE,
                        clicked.y * config.BLOCK_SIZE,
                        spawn_reason="break",
                        player=player,
                        img=self.assets.block(drop_item_type),
                    )
                )

            fluid = fluid_manager.get_fluid_type(clicked.block)

            if clicked.block.endswith("_source"):
                fluid_manager.add_fluid(clicked.x, clicked.y, fluid)

            chunk_manager.set_block(clicked.x, clicked.y, "air")

            for f in fluid_manager.FLUID_PROPERTIES.keys():
                fluid_manager.wake_fluid(f, clicked.x, clicked.y, fluid_manager.active_fluids)

            # print(fluid_manager.active_fluids["water"])

    def _handle_pick_block(self, clicked: BlockClick, player: Player):
        if clicked.block != "air":
            if player.can_pick_block():
                player.pick_item(clicked.block)

    def _handle_place_block(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):

        if self._can_place(clicked, player, fluid_manager):
            current_item = player.hotbar[player.selected_hotbar_index]
            self._place_block(clicked, current_item["type"], player)

            player.remove_selected_item(1)

            fluid = fluid_manager.get_fluid_type(current_item["type"])

            if current_item["type"].endswith("_source"):
                fluid_manager.add_fluid(clicked.x, clicked.y, fluid)

            for f in fluid_manager.FLUID_PROPERTIES.keys():
                fluid_manager.wake_fluid(f, clicked.x, clicked.y, fluid_manager.active_fluids)

    def _can_place(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):
        hand_item = player.hotbar[player.selected_hotbar_index]

        if clicked.block is None:
            return False

        if hand_item is None:
            return False

        if player.rect.colliderect(clicked.rect) or player.mode == "spectator":
            return False

        if fluid_manager.is_fluid(clicked.block) and not fluid_manager.is_fluid(hand_item["type"]):
            return True

        if clicked.block != "air":
            return False

        return True

    def _can_break(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):
        if clicked.block is None:
            return False

        if clicked.block == "air":
            return False

        if fluid_manager.is_fluid(clicked.block) and player.mode == "survival":
            if clicked.block.endswith("_source"):
                return True
            return False

        return True

    def _place_block(self, clicked: BlockClick, block_type, player: Player):
        chunk_manager.set_block(clicked.x, clicked.y, block_type)

        new_block_rect = pygame.Rect(
            clicked.x * config.BLOCK_SIZE,
            clicked.y * config.BLOCK_SIZE,
            config.BLOCK_SIZE,
            config.BLOCK_SIZE,
        )

        for item in self.item_entities:
            if item.rect.colliderect(new_block_rect):
                item.resolve_stuck(new_block_rect, player)

    def _handle_item_entities(self, player: Player):
        picked_items = []

        for item in self.item_entities:
            item.update(player)

            item.try_attract(player)

            # 處理碰到玩家
            if player.rect.colliderect(item.rect) and player.can_pickup_item(item.item_type) and item.pickup_delay == 0:
                remaining = player.give_item(item.item_type, item.count)
                if remaining == 0:
                    picked_items.append(item)

        for item in picked_items:
            self.item_entities.remove(item)

    @staticmethod
    def get_drop_item(block_name: str):
        print(block_name)

        def pick_weighted_drop(raw_drops):
            # 1. 如果是字典：代表有設定「權重/比重」
            if isinstance(raw_drops, dict):
                items = list(raw_drops.keys())
                weights = list(raw_drops.values())
                return random.choices(items, weights=weights, k=1)[0]

            # 2. 如果是清單：代表「等機率隨機抽取」
            elif isinstance(raw_drops, list):
                return random.choice(raw_drops)

            # 3. 如果是單一字串
            return raw_drops

        # 一般精確匹配 (例如 "stone", "grass")
        if block_name in BLOCK_DROPS:
            raw_drops = BLOCK_DROPS[block_name]

            chosen_drop = pick_weighted_drop(raw_drops)
            return chosen_drop  # 如果配置檔寫 None 就回傳 None

        # 動態模板比對 (例如 {wood}_leaves)
        for pattern, raw_drops in BLOCK_DROPS.items():
            if "{wood}" in pattern:
                prefix, suffix = pattern.split("{wood}", 1)

                if block_name.startswith(prefix) and block_name.endswith(suffix):
                    # 提取出來的木頭種類 (例如 "birch")
                    # 處理 suffix 為空字串的情況
                    end_index = len(block_name) - len(suffix) if suffix else None
                    wood_type = block_name[len(prefix) : end_index]

                    chosen_drop = pick_weighted_drop(raw_drops)

                    if chosen_drop:
                        return chosen_drop.replace("{wood}", wood_type)
                    return None  # 抽到 None 代表不掉落

        # 若字典內完全沒設定，預設掉落方塊自己本身
        return block_name

    def spawn_item_entity(self, item, x, y, spawn_reason, player):
        new_entity = item_entity.ItemEntity(item, x, y, spawn_reason, player, self.assets.block(item["type"]))

        self.item_entities.append(new_entity)

    def draw(self, screen, scroll_x, scroll_y, camera_zoom):
        # 設定一個安全的緩衝距離，確保漂浮動畫或邊緣圖片不會被切掉
        buffer = config.BLOCK_SIZE

        for item in self.item_entities:
            if (
                item.rect.right < scroll_x - buffer
                or item.rect.left > scroll_x + config.current_width / camera_zoom + buffer
                or item.rect.top < scroll_y - buffer
                or item.rect.bottom > scroll_y + config.current_height / camera_zoom + buffer
            ):
                continue

            item.draw(screen, scroll_x, scroll_y)

    # def _break_block(): ...
