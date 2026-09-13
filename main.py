import os

import opensimplex
import pygame

import asset_manager
import camera
import config
import menu_manager
import save_manager
import tool
import world_manager
from craft_manager import CraftingManager
from environment_systems import EnvironmentSystems
from fluid_manager import FluidManager
from game_data import crafting_recipes
from player import Player
from ui import ui_manager

save = save_manager.SaveManager()
crafting_manager = CraftingManager()

# 告訴系統將下一個建立的視窗放在螢幕正中央
os.environ["SDL_VIDEO_CENTERED"] = "1"

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
world_surface = pygame.Surface((config.current_width, config.current_height))
clock = pygame.time.Clock()
# screen_text = f"2D Minecraft - {config.GAME_VERSION}"
pygame.display.set_caption(f"2D Minecraft - {config.GAME_VERSION}")  # 之後放screen_text

player = Player(0, 20)

asset = asset_manager.AssetManager()
asset.load()

ui = ui_manager.UI(asset)
menu = menu_manager.MenuManager(asset)
world = world_manager.World(asset)

last_chunk = None

save.load_world(player, world)

game_camera = camera.Camera(asset, player)
environment_systems = EnvironmentSystems(config.chunks)
fluid_manager = FluidManager(config.chunks)

crafting_recipes.register_recipes(crafting_manager)
# print("Recipes registered:", len(crafting_manager.recipes))
# print("Registered recipes:")
# for recipe in crafting_manager.recipes:
#     print(f"Ingredients: {recipe.ingredients}, Result: {recipe.result['type']} x{recipe.result['count']}")


dt = 1
opensimplex.noise2(0, 0)  # 逼 numba 先暖機

while config.running:
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(tool.Colors.CYAN)

    fps = clock.get_fps()

    if config.game_state == "MENU":
        pass

    elif config.game_state == "PLAYING":
        current_chunk = player.hitbox.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)
        game_camera.update(player, fluid_manager)

        surface_width = int(config.current_width / game_camera.zoom)
        surface_height = int(config.current_height / game_camera.zoom)

        world_surface = pygame.Surface((surface_width, surface_height))
        world_surface.fill(tool.Colors.CYAN)

        game_camera.draw_world(world_surface, mouse_pos, world)

        dropped_item = None

        player.handle_input()
        ui.handle_input()

        player.just_switched_mode = False
        for event in events:
            item = player.handle_event(event, keys, fluid_manager)

            if item is not None:
                dropped_item = item

            ui.handle_events(event, player, mouse_pos, world, crafting_manager)

        # 更新
        """任何一幀裡，只要牽涉到「滑鼠螢幕座標 → 世界座標」的換算，都必須使用「跟這一幀實際顯示畫面一致」的那個 zoom 值"""
        player.update(mouse_pos, dt, game_camera, fluid_manager)
        world.update(mouse_buttons, mouse_pos, player, game_camera, fluid_manager, environment_systems, ui)
        # print("[from: main.py] UPDATE END:", player.vel_y, player.is_grounded)
        ui.update(player, fps, mouse_pos, game_camera, world)
        asset.update()
        fluid_manager.update(pygame.time.get_ticks())

        if dropped_item is not None:
            world.spawn_item_entity(dropped_item, player.hitbox.centerx, player.hitbox.top, "drop", player)

        # print(player.rect.x, player.rect.y)
        # print(game_camera.scroll_x, game_camera.scroll_y)

        # 畫圖
        player.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y)
        world.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y, game_camera.zoom)
        game_camera.draw(screen, world_surface)
        ui.draw(screen, player)

        if current_chunk != last_chunk:
            game_camera._load_visible_chunks(player, fluid_manager)
            last_chunk = current_chunk

    elif config.game_state in menu.menus:
        screen.blit(config.pause_background, (0, 0))
        menu.update(events, mouse_pos, player)
        menu.draw(screen)

    for event in events:
        if event.type == pygame.VIDEORESIZE:
            config.current_width = event.w
            config.current_height = event.h
            screen = pygame.display.set_mode((event.w, event.h), screen.get_flags())

        if event.type == pygame.QUIT:
            config.running = False

        if event.type == pygame.KEYDOWN:
            if config.game_state == "PLAYING":
                if event.key == pygame.K_ESCAPE:
                    config.pause_background = screen.copy()
                    config.game_state = "PAUSE"
                if event.key == pygame.K_F3:
                    config.show_debug_screen = not config.show_debug_screen

    pygame.display.flip()
    dt = clock.tick(60) / 1000.0

pygame.quit()

save.save_world(player, world)
