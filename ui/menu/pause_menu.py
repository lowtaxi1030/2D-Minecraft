from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager


import config
import tool
from ui.element import ui_widgets as ui

from .base_menu import BaseMenu


class PauseMenu(BaseMenu):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)

        self.start_y = 50  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 120  # 上下按鈕的間距

        self.title = ui.Text(
            name="title",
            text="Game Menu",
            pos=(0, 50),
            colors=tool.Colors.WHITE,
            size=40,
            screen_center=True,
        )

        self.back_btn = ui.ImageTextButton(
            name="back_to_game",
            image=self.assets.setting_button_img,
            pos=(self.center_x, self.start_y + self.spacing_y),
            text="Back to Game",
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.option_btn = ui.ImageTextButton(
            name="options",
            text="Options...",
            image=self.assets.setting_button_img,
            pos=(self.center_x, self.start_y + self.spacing_y * 2),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.quit_btn = ui.ImageTextButton(
            name="save_and_quit",
            image=self.assets.setting_button_img,
            pos=(self.center_x, self.start_y + self.spacing_y * 3),
            text="Save and Quit",
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.all_uis = [self.title, self.back_btn, self.option_btn, self.quit_btn]

    def layout(self):
        self.back_btn.rect.center = (self.center_x, self.start_y + self.spacing_y)
        self.option_btn.rect.center = (self.center_x, self.start_y + self.spacing_y * 2)
        self.quit_btn.rect.center = (self.center_x, self.start_y + self.spacing_y * 3)

    def _handle_event(self, events, mouse_pos, **kwargs):
        if self.back_btn.interactive.clicked:
            config.game_state = "PLAYING"

        if self.option_btn.interactive.clicked:
            config.game_state = "OPTION"

        if self.quit_btn.interactive.clicked:
            config.running = False
