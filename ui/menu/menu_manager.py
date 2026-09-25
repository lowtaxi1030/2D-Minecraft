from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from asset_manager import AssetManager
    from player import Player


import config
import tool

from . import controls_menu, death_menu, game_menu, option_menu, pause_menu, video_menu


class MenuManager:
    def __init__(self, assets: AssetManager):
        self.menus: dict[str] = {
            "PAUSE": pause_menu.PauseMenu(assets),
            "OPTION": option_menu.OptionMenu(assets),
            "VIDEO_OPTION": video_menu.VideoMenu(assets),
            "CONTROLS_OPTION": controls_menu.ControlsMenu(assets),
            "GAME_OPTION": game_menu.GameMenu(assets),
            "DEATH": death_menu.DeathMenu(assets),
        }

    def update(self, events, mouse_pos: config.Pos, mouse_buttons, player: Player = None):
        menu = self.menus.get(config.game_state)
        # print("[DEBUG: from ui/menu/menu_manager.py] ", config.game_state, menu)
        if menu:
            menu.update(events, mouse_pos=mouse_pos, mouse_buttons=mouse_buttons, player=player)

    def draw(self, screen: pygame.Surface):
        # 1. 🎯 鋪滿暗色泥土背景（Minecraft 經典風格）
        # for y_pos in range(config.current_height // 40 + 2):
        #     for x_pos in range(config.current_width // 40 + 2):
        #         screen.blit(self.assets.bg_dirt_img, (x_pos * 40, y_pos * 40))
        menu = self.menus.get(config.game_state)
        # print("[DEBUG: from ui/menu/menu_manager.py] ", config.game_state, menu)
        if menu:
            tool.screen_vague(screen, 20)
            menu.draw(screen)
