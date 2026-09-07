from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from environment_systems import EnvironmentSystems
    from fluid_manager import FluidManager
    from player import Player
    from ui_manager import UI

import random

import pygame

import chunk_manager
import config
import item_entity
from camera import Camera
from game_data.block_drops import BLOCK_DROPS
from item.__init__ import NON_PLACEABLE_KEYWORDS, NON_PLACEABLE_TAGS
from special_blocks import SPECIAL_BLOCKS
from states.chest_state import ChestState
from states.furnace_state import FurnaceState


class BlockClick:
    def __init__(self, x: int, y: int, block: str):
        self.x = x
        self.y = y
        self.block = block
        self.base_name = ""
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

        self.furnaces: dict[config.Pos, FurnaceState] = {}
        self.chests: dict[config.Pos, ChestState] = {}

        self.containers = {
            "furnace": {
                "container": self.furnaces,
                "state": FurnaceState,
                "ui_attr": "furnace",  # 對應 ui.furnace
            },
            "chest": {
                "container": self.chests,
                "state": ChestState,
                "ui_attr": "chest",  # 對應 ui.chest
            },
        }

    def update(
        self,
        mouse_buttons: tuple[bool, bool, bool],
        mouse_pos: tuple[int, int],
        player: Player,
        camera: Camera,
        fluid_manager: FluidManager,
        environment_systems: EnvironmentSystems,
        ui: UI,
    ):
        """世界更新區"""
        decayed_leaves = environment_systems.update()

        for world_x, world_y, leaf_type in decayed_leaves:
            drop_item_type, drop_count = self.get_drop_item(self.get_block_base_name(leaf_type), player.held_item)
            if drop_item_type is not None and drop_count > 0:
                self.spawn_item_entity(
                    {"type": drop_item_type, "count": drop_count},
                    world_x * config.BLOCK_SIZE,
                    world_y * config.BLOCK_SIZE,
                    "break",  # 或另外開一個 spawn_reason，看你要不要讓衰變掉落有不同的噴出手感
                    player,
                )

        self._handle_item_entities(player)

        for furnace in self.furnaces.values():
            furnace.update()

        """"""

        # 沒有按下任何鍵，或是正在合成中
        if not any(mouse_buttons) or player.inv_type is not None:
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
        clicked.base_name = self.get_block_base_name(clicked.block)

        if current_pos == self.last_pos and current_btn == self.last_mouse_btn:
            return

        if mouse_buttons[0]:
            self._handle_break_block(clicked, player, fluid_manager)

        elif mouse_buttons[1]:
            self._handle_pick_block(clicked, player)

        elif mouse_buttons[2]:
            if not self._handle_special_block(clicked, player, ui):
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

    def _handle_special_block(self, clicked: BlockClick, player: Player, ui: UI) -> bool:
        if (special_block_class := SPECIAL_BLOCKS.get(clicked.block)) is None:
            return False

        special_block = special_block_class(player)
        special_block.interact()

        if clicked.block in self.containers:
            config_entry = self.containers[clicked.block]
            container_dict = config_entry["container"]
            state_class = config_entry["state"]

            pos = (clicked.x, clicked.y)
            if pos not in container_dict:
                container_dict[pos] = state_class()

            target_ui = getattr(ui, config_entry["ui_attr"])
            target_ui.set_state(container_dict[pos])

        return True

    def _handle_break_block(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):
        if clicked.base_name != "air" and player.can_place_block() and self._can_break(clicked, player, fluid_manager):
            drop_item_type, drop_count = self.get_drop_item(clicked.base_name, player.held_item)
            # print(drop_item_type)

            if player.will_drop_item_entity() and drop_item_type is not None and drop_count > 0:
                self.item_entities.append(
                    item_entity.ItemEntity(
                        {"type": drop_item_type, "count": drop_count},
                        clicked.x * config.BLOCK_SIZE,
                        clicked.y * config.BLOCK_SIZE,
                        spawn_reason="break",
                        player=player,
                        img=self.assets.block(drop_item_type),
                    )
                )

            # fluid 專區
            fluid = fluid_manager.get_fluid_type(clicked.block)

            if clicked.block.endswith("_source"):
                fluid_manager.add_fluid(clicked.x, clicked.y, fluid)

            chunk_manager.set_block(clicked.x, clicked.y, "air")

            for f in fluid_manager.FLUID_PROPERTIES.keys():
                fluid_manager.wake_fluid(f, clicked.x, clicked.y, fluid_manager.active_fluids)

            # container 專區
            pos = (clicked.x, clicked.y)
            if clicked.block in self.containers:
                container_dict = self.containers[clicked.block]["container"]
                self._drop_container_contents(pos, container_dict, player)

    def _drop_container_contents(self, pos: tuple[int, int], container_dict, player: Player):
        if (state := container_dict.pop(pos, None)) is None:
            return
        for item in state.get_all_items():
            if item is not None:
                self.spawn_item_entity(item, pos[0] * config.BLOCK_SIZE, pos[1] * config.BLOCK_SIZE, "container", player)

    def _handle_pick_block(self, clicked: BlockClick, player: Player):
        if clicked.block != "air":
            if player.can_pick_block():
                player.pick_item(clicked.base_name)

    def _handle_place_block(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):

        if self._can_place(clicked, player, fluid_manager):
            current_item = player.held_item
            self._place_block(clicked, current_item["type"], player)

            player.remove_selected_item(1)

            fluid = fluid_manager.get_fluid_type(current_item["type"])

            if current_item["type"].endswith("_source"):
                fluid_manager.add_fluid(clicked.x, clicked.y, fluid)

            for f in fluid_manager.FLUID_PROPERTIES.keys():
                fluid_manager.wake_fluid(f, clicked.x, clicked.y, fluid_manager.active_fluids)

    def _can_place(self, clicked: BlockClick, player: Player, fluid_manager: FluidManager):
        hand_item = player.held_item

        if clicked.block is None or clicked.base_name is None:
            return False

        if hand_item is None:
            return False

        item_type = hand_item["type"]
        if any(keyword == item_type for keyword in NON_PLACEABLE_TAGS):
            return False

        elif any(keyword in item_type for keyword in NON_PLACEABLE_KEYWORDS):
            return False

        if player.rect.colliderect(clicked.rect) or player.mode == "spectator":
            return False

        if fluid_manager.is_fluid(clicked.block):
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
    def get_drop_item(block_name: str, tool_item: config.Item | None) -> tuple[str | None, int]:
        # 1. 若方塊不在 BLOCK_DROPS 中，預設掉落方塊自己本身 (數量 1)
        if block_name not in BLOCK_DROPS:
            return block_name, 1

        if tool_item is not None:

            if tool_item["type"] == "shears" and "leav" in block_name:
                return block_name, 1

        raw_drops = BLOCK_DROPS[block_name]

        def parse_drop_data(data):
            """解析掉落項目與數量"""
            if data is None:
                return None, 0

            # 特殊掉落配置 (例如包含 drop 與 count 的字典)
            if isinstance(data, dict) and "drop" in data:
                item_id = data["drop"]
                count_data = data.get("count", 1)

                # 處理 (2, 5) 這種隨機數量範圍
                if isinstance(count_data, (tuple, list)):
                    count = random.randint(count_data[0], count_data[1])
                else:
                    count = count_data

                return item_id, count

            # 帶有權重的機率抽取 (例如 {"apple": 1, "oak_sapling": 5, None: 100})
            if isinstance(data, dict):
                items = list(data.keys())
                weights = list(data.values())
                chosen = random.choices(items, weights=weights, k=1)[0]
                return parse_drop_data(chosen)

            # 等機率隨機抽取清單
            if isinstance(data, list):
                chosen = random.choice(data)
                return parse_drop_data(chosen)

            # 普通單一字串
            return data, 1

        return parse_drop_data(raw_drops)

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

    def get_block_display_name(self, x, y, block_name):
        if block_name == "furnace":
            furance = self.furnaces.get((x, y))
            if furance is not None and furance.burn_time_left > 0:
                return "furnace_on"

        if "leav" in block_name and block_name.endswith("_natural"):
            block_name = block_name[:-8]

        return block_name

    @staticmethod
    def get_block_base_name(block_name: str):

        if "leav" in block_name and block_name.endswith("_natural"):
            block_name = block_name[:-8]

        return block_name
