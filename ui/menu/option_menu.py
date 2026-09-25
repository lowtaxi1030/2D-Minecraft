from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager

import pygame

import config
import tool
from ui.element import ui_widgets as ui

from .base_menu import BaseMenu


class OptionMenu(BaseMenu):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)

        self.start_y = 150  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 60  # 上下按鈕的間距

        self.title = ui.Text(
            name="title",
            text="Options",
            pos=(0, 50),
            colors=tool.Colors.WHITE,
            size=40,
            screen_center=True,
        )

        self.video_button = ui.ImageTextButton(
            name="video_option",
            text="Video Settings",
            image=self.assets.setting_button_img,
            pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2)),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.controls_button = ui.ImageTextButton(
            name="controls_option",
            text="Controls Settings",
            image=self.assets.setting_button_img,
            pos=(self.center_x + (self.btn_w // 2) + self.spacing_x, self.start_y + (self.btn_h // 2)),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.audio_button = ui.ImageTextButton(
            name="audio_option",
            text="Audio Settings",
            image=self.assets.setting_button_img,
            pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + self.spacing_y + (self.btn_h // 2)),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.game_button = ui.ImageTextButton(
            name="game_option",
            text="Game Settings",
            image=self.assets.setting_button_img,
            pos=(
                self.center_x - (self.btn_w // 2) + self.spacing_x,
                self.start_y + self.spacing_y + (self.btn_h // 2),
            ),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.lang_button = ui.ImageTextButton(
            name="lang_option",
            text="Lang Settings",
            image=self.assets.setting_button_img,
            pos=(
                self.center_x - (self.btn_w // 2) - self.spacing_x,
                self.start_y + self.spacing_y * 2 + (self.btn_h // 2),
            ),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.done_button = ui.ImageTextButton(
            name="done",
            text="Done",
            image=self.assets.setting_button_img,
            pos=(self.center_x, config.current_height - 60),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.all_uis = [
            self.title,
            self.video_button,
            self.controls_button,
            self.audio_button,
            self.game_button,
            self.lang_button,
            self.done_button,
        ]

    def layout(self):
        self.video_button.rect.center = (self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2))
        self.controls_button.rect.center = (self.center_x + (self.btn_w // 2) + self.spacing_x, self.start_y + (self.btn_h // 2))
        self.audio_button.rect.center = (
            self.center_x - (self.btn_w // 2) - self.spacing_x,
            self.start_y + self.spacing_y + (self.btn_h // 2),
        )
        self.game_button.rect.center = (
            self.center_x + (self.btn_w // 2) + self.spacing_x,
            self.start_y + self.spacing_y + (self.btn_h // 2),
        )
        self.lang_button.rect.center = (
            self.center_x - (self.btn_w // 2) - self.spacing_x,
            self.start_y + self.spacing_y * 2 + (self.btn_h // 2),
        )
        self.done_button.rect.center = (self.center_x, config.current_height - 60)  # 👈 確保 Done 大按鈕也完美黏在底部

    def update(self, events, mouse_pos, mouse_buttons, player):
        super().update(events, mouse_pos, mouse_buttons)

        self.layout()

    def _handle_event(self, events, mouse_pos, **kwargs):
        if self.done_button.is_clicked:
            config.game_state = "PAUSE"

        if self.video_button.is_clicked:
            config.game_state = "VIDEO_OPTION"

        if self.controls_button.is_clicked:
            config.game_state = "CONTROLS_OPTION"

        if self.game_button.is_clicked:
            config.game_state = "GAME_OPTION"

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "PAUSE"
