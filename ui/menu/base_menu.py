from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager

import config


class BaseMenu:
    def __init__(self, assets: AssetManager):
        self.assets = assets

        self.btn_w, self.btn_h = 350, 40  # 按鈕標準尺寸
        self.center_x = config.current_width // 2

        self.all_uis: list = []

    def update(self, events, mouse_pos, mouse_buttons, **kwargs):
        self.center_x = config.current_width // 2

        for ob in self.all_uis:
            ob.update(mouse_pos, mouse_buttons)

        self._handle_event(events, mouse_pos=mouse_pos, **kwargs)
        self._update_continuous(mouse_pos=mouse_pos, mouse_buttons=mouse_buttons, **kwargs)

        self.layout()

    def _handle_event(self, events, **kwargs):
        """子類別覆寫：處理離散的pygame事件（按鈕點擊等）"""
        pass

    def _update_continuous(self, **kwargs):
        """子類別覆寫：每幀都要跑的持續性邏輯（例如VideoMenu拖曳中的滑桿）"""
        pass

    def layout(self):
        """子類別必須覆寫：重新計算所有元件位置"""
        pass

    def draw(self, screen):
        for ob in self.all_uis:
            ob.draw(screen)
