from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from player import Player

# import pygame

import config
import tool
from ui.element import ui_widgets as ui


class DeathMenu:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        # self.btn_w, self.btn_h = 350, 40
        self.center_x = config.current_width // 2

        self.respawn_btn = ui.ImageTextButton(
            name="respawn",
            image=self.assets.setting_button_img,
            pos=(self.center_x, config.current_height // 2),
            text="Respawn",
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.menu_btn = ui.ImageTextButton(
            name="main_menu",
            image=self.assets.setting_button_img,
            pos=(self.center_x, config.current_height // 2 + 80),
            text="Main Menu",
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.all_uis = [self.respawn_btn]  # , self.menu_btn

    def update(self, events, mouse_pos, mouse_buttons, player: Player):
        for ob in self.all_uis:
            ob.update(mouse_pos, mouse_buttons)

        if self.respawn_btn.is_clicked:
            player._respawn()
            config.game_state = "PLAYING"

        if self.menu_btn.is_clicked:
            config.game_state = "PAUSE"

        self.layout()

    def layout(self):

        self.center_x = config.current_width // 2

        self.respawn_btn.rect.center = (self.center_x, config.current_height // 2)
        self.menu_btn.rect.center = (self.center_x, config.current_height // 2 + 80)

    def draw(self, screen):
        tool.screen_vague(screen, 10, tool.Colors.DARK_RED, alpha=50)  # 模糊背景
        ui.show_text(screen, "You Died", tool.Colors.RED, 0, 100, 60, screen_center=True)

        for ob in self.all_uis:
            ob.draw(screen)
