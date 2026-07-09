import pygame

import config
from camera import Camera
from player import Player


class BlockClick:
    def __init__(self, x, y, block):
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
        pass

    def update(
        self,
        mouse_buttons: tuple[bool, bool, bool],
        mouse_pos: tuple[int, int],
        player: Player,
        camera: Camera,
    ):
        if not any(mouse_buttons) or player.is_open_inv:
            return
        # 計算世界座標
        clicked = self._get_clicked_block(mouse_pos, camera)

        if clicked is None:
            return

        if mouse_buttons[0]:
            self._handle_break_block(clicked)

        elif mouse_buttons[2]:
            self._handle_place_block(clicked, player)

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

    def _handle_break_block(self, clicked: BlockClick):
        if clicked.block != "air":
            config.world_data[clicked.y][clicked.x] = "air"

    def _handle_place_block(self, clicked: BlockClick, player: Player):

        if self._can_place(clicked, player):
            current_item = player.hotbar[player.selected_hotbar_index]
            self._place_block(clicked, current_item["type"])

    def _can_place(self, clicked: BlockClick, player: Player):

        if clicked.block != "air":
            return

        if player.hotbar[player.selected_hotbar_index] is None:
            return

        if player.rect.colliderect(clicked.rect) and player.mode != "spectator":
            return

        return True

    def _place_block(self, clicked: BlockClick, block_type):
        config.world_data[clicked.y][clicked.x] = block_type

    # def _break_block(): ...
