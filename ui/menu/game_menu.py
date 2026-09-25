from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from player import Player

import pygame

import config
import tool
from ui.element import ui_widgets as ui

from .base_menu import BaseMenu


class GameMenu(BaseMenu):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)

        self.start_y = 150  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 60  # 上下按鈕的間距

        self.modes = ["survival", "creative", "spectator"]  # , "adventure" 之後再用
        self.mode_index = 0  # 預設是生存模式
        self.mode = self.modes[self.mode_index]

        self.title = ui.Text(
            name="title",
            text="Game",
            pos=(0, 50),
            colors=tool.Colors.WHITE,
            size=40,
            screen_center=True,
        )

        # self.alto_jump = ui.ImageButton(
        #     name="alto_jump",
        #     image=self.assets.swich_base_img,
        #     pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2)),
        # )

        self.mode_switch = ui.ImageTextButton(
            name="mode_switch",  # 視野廣角
            image=self.assets.setting_button_img,
            pos=(self.center_x + (self.btn_w // 2) + self.spacing_x, self.start_y + (self.btn_h // 2)),
            text="",  # 給update處理
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.hitbox_switch = ui.ImageTextButton(
            name="hitbox_switch",
            image=self.assets.setting_button_img,
            pos=(self.center_x + (self.btn_w // 2) + self.spacing_x, self.start_y + (self.btn_h // 2)),
            text="Hitbox: OFF",
            on_text="Hitbox: ON",
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
            interaction_mode=ui.InteractionMode.TOGGLE,
        )

        self.back_btn = ui.ImageTextButton(
            name="back",
            text="Back",
            image=self.assets.setting_button_img,
            pos=(self.center_x, config.current_height - 60),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )
        self.all_uis = [self.mode_switch, self.hitbox_switch, self.back_btn]  # , self.alto_jump

    def layout(self):
        # self.alto_jump.rect.center = (self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2))
        self.mode_switch.rect.center = (self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2))
        self.hitbox_switch.rect.center = (
            self.center_x - (self.btn_w // 2) - self.spacing_x,
            self.start_y + (self.btn_h // 2) + self.spacing_y,
        )

        self._update_mode()
        self.back_btn.rect.center = (self.center_x, config.current_height - 60)

    def _update_mode(self):
        self.mode_switch.text = (f"mode: {self.modes[self.mode_index]}",)
        self.mode = self.modes[self.mode_index]

    def _handle_event(self, events, mouse_pos, player: Player, **kwargs):
        if self.mode_switch.is_clicked:
            self.mode_index += 1
            self.mode_index %= len(self.modes)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "OPTION"

        if self.back_btn.is_clicked:
            config.game_state = "OPTION"
            player.mode = self.mode
            player.vel_x = 0
            player.vel_y = 0
            if player.mode == "survival":
                player.is_flying = False
            player.just_switched_mode = True
