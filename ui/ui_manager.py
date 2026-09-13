from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pygame

    from asset_manager import AssetManager
    from camera import Camera
    from craft_manager import CraftingManager
    from player import Player
    from world_manager import World

import config

from . import (
    debug_screen,  # noqa: F401
    hot_bar,  # noqa: F401
)
from .hud import HealthBar, HungerBar  # noqa: F401
from .inventory import ChestUI, CraftingTableUI, FurnaceUI, InventoryUI  # noqa: F401


class UIInterface(Protocol):
    interface_name: str = ...

    def handle_input(self): ...
    def handle_events(self): ...
    def update(self): ...
    def draw(self): ...
    def clear_grid_and_drop(self): ...


class UI:
    def __init__(self, assets: AssetManager):
        self.hotbar = hot_bar.Hotbar(assets)
        self.health_bar = HealthBar(assets)
        self.hunger_bar = HungerBar(assets)
        self.debug_screen = debug_screen.DebugScreen(assets)

        interface_list: list[UIInterface] = [
            ChestUI(assets),
            CraftingTableUI(assets),
            FurnaceUI(assets),
            InventoryUI(assets),
        ]
        self.interfaces: dict[str, UIInterface] = {ui.interface_name: ui for ui in interface_list}

        self.last_inv_type = None

    def handle_input(self):
        for interface in self.interfaces.values():
            interface.handle_input()

    def handle_events(self, event, player: Player, mouse_pos, world_manager: World, crafting_manager: CraftingManager):
        self.hotbar.handle_events(event, player, mouse_pos)

        if player.inv_type is not None:
            self.interfaces[player.inv_type].handle_events(event, player, mouse_pos, world_manager, crafting_manager)
            self.last_inv_type = player.inv_type

        elif self.last_inv_type is not None:
            self.interfaces[self.last_inv_type].clear_grid_and_drop(player, world_manager)
            self.last_inv_type = None

    def update(self, player: Player, fps, mouse_pos: tuple[int, int], game_camera: Camera, world_manager: World):
        self.hotbar.update(player)
        self.health_bar.update()  # player
        self.hunger_bar.update()  # player
        self.debug_screen.update(player, fps, mouse_pos, game_camera, world_manager)

        if player.inv_type is not None:
            self.interfaces[player.inv_type].update(player)

    def draw(self, screen: pygame.Surface, player: Player):
        self.hotbar.draw(screen, player)
        self.health_bar.draw(screen)
        self.hunger_bar.draw(screen)

        if player.inv_type is not None:
            self.interfaces[player.inv_type].draw(screen, player)

        if config.show_debug_screen:
            self.debug_screen.draw(screen)
