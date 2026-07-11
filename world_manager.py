import pygame

import config
import item_entity
from camera import Camera
from player import Player


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
    def __init__(self):
        self.item_entities = []

    def update(
        self,
        mouse_buttons: tuple[bool, bool, bool],
        mouse_pos: tuple[int, int],
        player: Player,
        camera: Camera,
        world_data,
    ):

        self._handle_item_entities(world_data, player)

        if not any(mouse_buttons) or player.is_open_inv:
            return
        # 計算世界座標
        clicked = self._get_clicked_block(mouse_pos, camera)

        if clicked is None:
            return

        if mouse_buttons[0]:
            self._handle_break_block(clicked, player)

        elif mouse_buttons[1]:
            self._handle_pick_block(clicked, player)

        elif mouse_buttons[2]:
            self._handle_place_block(clicked, player, world_data)

    def _get_clicked_block(self, mouse_pos, camera: Camera):
        world_x, world_y = camera.screen_to_world(mouse_pos)

        if world_x < 0 or world_x >= config.MAP_WIDTH or world_y < 0 or world_y >= config.MAP_HEIGHT:
            return None

        clicked_block = config.world_data[world_y][world_x]

        return BlockClick(
            world_x,
            world_y,
            clicked_block,
        )

    def _handle_break_block(self, clicked: BlockClick, player: Player):
        if clicked.block != "air" and player.can_place_block():

            if player.will_drop_item_entity():
                self.item_entities.append(
                    item_entity.ItemEntity(
                        config.world_data[clicked.y][clicked.x],
                        1,
                        clicked.x * config.BLOCK_SIZE,
                        clicked.y * config.BLOCK_SIZE,
                        spawn_reason="break",
                    )
                )

            config.world_data[clicked.y][clicked.x] = "air"

    def _handle_pick_block(self, clicked: BlockClick, player: Player):
        if clicked.block != "air":
            if player.can_pick_block():
                player.pick_item(clicked.block)

    def _handle_place_block(self, clicked: BlockClick, player: Player, world_data):

        if self._can_place(clicked, player):
            current_item = player.hotbar[player.selected_hotbar_index]
            self._place_block(clicked, current_item["type"], world_data, player)
            player.remove_selected_item(1)

    def _can_place(self, clicked: BlockClick, player: Player):

        if clicked.block != "air":
            return

        if player.hotbar[player.selected_hotbar_index] is None:
            return

        if player.rect.colliderect(clicked.rect) or player.mode == "spectator":
            return

        return True

    def _place_block(self, clicked: BlockClick, block_type, world_data, player: Player):
        config.world_data[clicked.y][clicked.x] = block_type

        new_block_rect = pygame.Rect(
            clicked.x * config.BLOCK_SIZE,
            clicked.y * config.BLOCK_SIZE,
            config.BLOCK_SIZE,
            config.BLOCK_SIZE,
        )

        for item in self.item_entities:
            if item.rect.colliderect(new_block_rect):
                item.resolve_stuck(world_data, new_block_rect, player)

    def _handle_item_entities(self, world_data, player: Player):
        picked_items = []

        for item in self.item_entities:
            item.update(world_data, player)

            item.try_attract(player)

            # 處理碰到玩家
            if player.rect.colliderect(item.rect) and player.can_pickup_item():
                if player.give_item(item.item_type, item.count):
                    picked_items.append(item)

        for item in picked_items:
            self.item_entities.remove(item)

    def spawn_item_entity(self, item_type: str, count: int, x, y, spawn_reason):
        new_entity = item_entity.ItemEntity(item_type, count, x, y, spawn_reason=spawn_reason)

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
