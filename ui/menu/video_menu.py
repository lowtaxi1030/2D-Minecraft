from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager

import pygame

import config
import tool
from ui.element import ui_widgets as ui

from .base_menu import BaseMenu


class VideoMenu(BaseMenu):
    def __init__(self, assets: AssetManager):
        super().__init__(assets)

        self.fov_value = 70  # 預設 FOV 值（Minecraft 通常是 70）
        self.fov_min = 30  # 最小值
        self.fov_max = 200  # 最大值（例如 Quake Pro 可以是 110）
        self.fov_width = self.assets.FOV_bg_rect.width
        self.is_dragging_fov = False  # 標記目前滑鼠是不是正在「按住拖曳拉桿」

        self.start_y = 150
        self.spacing_x = 60
        self.spacing_y = 60

        self.title = ui.Text(
            name="title",
            text="Video Options",
            pos=(0, 50),
            colors=tool.Colors.WHITE,
            size=40,
            screen_center=True,
        )

        self.fov_base = ui.ImageButton(
            name="FOV_base",  # 視野廣角
            image=self.assets.fov_bg_img,
            pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2)),
        )

        self.fov_lever = ui.ImageButton(
            name="FOV_lever",
            image=self.assets.lever_img,
            pos=(0, 0),  # 在update裡做
        )

        self.back_btn = ui.ImageTextButton(
            name="back",
            text="Back",
            image=self.assets.setting_button_img,
            pos=(self.center_x, config.current_height - 60),
            text_colors=ui.StateGroup(tool.Colors.WHITE, tool.Colors.MC_YELLOW),
        )

        self.fov_text = ui.Text(
            name="fov_text",
            text="Fov: ",
            pos=(self.fov_base.rect.centerx, self.fov_base.rect.centery),
            colors=tool.Colors.WHITE,
            size=30,
        )

        self.all_uis = [self.title, self.fov_base, self.fov_lever, self.back_btn]

    def layout(self):
        self.fov_base.rect.center = (
            self.center_x - (self.btn_w // 2) - self.spacing_x,
            self.start_y + (self.btn_h // 2),
        )
        self._update_slider()
        self.back_btn.rect.center = (self.center_x, config.current_height - 60)

    def _update_slider(self):
        self.fov_lever.rect.centery = self.fov_base.rect.centery
        lever_off = (self.fov_value - self.fov_min) / (self.fov_max - self.fov_min) * self.fov_width
        self.fov_lever.rect.centerx = self.fov_base.rect.left + lever_off

    def update(self, events, mouse_pos, mouse_buttons, player):
        super().update(events, mouse_pos, mouse_buttons)

        self._update_fov(mouse_pos)

        self.fov_text.text = (f"FOV: {self.fov_value}",)

    def _handle_event(self, events, **kwargs):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fov_base.is_hover:
                    self.is_dragging_fov = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.is_dragging_fov = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "OPTION"

        if self.back_btn.is_clicked:
            config.game_state = "OPTION"

    def _update_fov(self, mouse_pos):

        if self.is_dragging_fov:
            relative_x = mouse_pos[0] - self.fov_base.rect.left
            total_width = self.fov_base.rect.width

            pct = tool.clamp(0.0, 1.0, relative_x / total_width)
            fov_range = self.fov_max - self.fov_min

            self.fov_value = int(self.fov_min + pct * fov_range)
            config.fov = self.fov_value
