from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from asset_manager import AssetManager
    from player import Player


class HealthBar:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        self.hp = 0
        self.max_hp = 0

        self.hotbar_rect = self.assets.hotbar_bg_rect

        self.start_x = 0
        self.start_y = 0

    def handle_input(self): ...
    def handle_events(self): ...
    def update(self, player: Player):

        self.start_x = self.hotbar_rect.left
        self.start_y = self.hotbar_rect.top - 35

        self.hp = player.hp
        self.max_hp = player.max_hp

    def draw(self, screen: pygame.Surface):
        full_img = self.assets.hp_images["full"]
        half_img = self.assets.hp_images["half"]
        empty_img = self.assets.hp_images["container"]

        total_hearts = self.max_hp // 2
        full_hearts = self.hp // 2
        has_half = self.hp % 2 == 1

        heart_width = full_img.get_width()

        for i in range(total_hearts):
            x = self.start_x + i * heart_width
            screen.blit(empty_img, (x, self.start_y))  # 先畫空的容器當底
            if i < full_hearts:
                screen.blit(full_img, (x, self.start_y))
            elif i == full_hearts and has_half:
                screen.blit(half_img, (x, self.start_y))
