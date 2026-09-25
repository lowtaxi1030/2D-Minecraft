from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager

import pygame

import config
import tool
from ui.element import ui_widgets as ui


class ControlsMenu:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        self.btn_w, self.btn_h = 350, 40  # 按鈕標準尺寸
        self.switch_base_w, self.switch_base_h = self.assets.switch_base_rect.size  # 開關底座尺寸
        self.center_x = config.current_width // 2
        self.start_y = 150  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 60  # 上下按鈕的間距
        self.all_uis = []

    def layout(self): ...

    def update(self, events, mouse_pos, mouse_buttons, player):
        self.center_x = config.current_width // 2

        self._handle_event(events, mouse_pos)
        self.layout()

    def _handle_event(self, events, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "OPTION"

    def draw(self, screen):
        ui.show_text(screen, "Controls", tool.Colors.WHITE, 0, 50, 40, screen_center=True)

        for ob in self.all_uis:
            ob.draw(screen)
